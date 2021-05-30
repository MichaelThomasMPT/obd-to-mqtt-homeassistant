import obd
import time
import yaml
import json
import paho.mqtt.publish as MqttPublish
import logging
from serial import SerialException

CAR_ATTRIBUTES_CONFIG_FILE = "./config/car_config.yml"
MQTT_CONFIG_FILE = "./config/mqtt.yml"
SLEEP_SECONDS_AFTER_READ = 120
SLEEP_SECONDS_NO_READ = 10
MQTT_STATE_TOPIC = 'obd/sensor/car/state'
MQTT_HOME_ASSISTANT_TOPIC_BASE = 'homeassistant/sensor/car/'

# Set up the logger
log = logging.getLogger()
log.setLevel(logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)


def main():
  # show list of available adaptors
  ports = obd.scan_serial()
  log.info("Ports available: " + str(ports))

  carProperties = readCarPropertiesConfig(CAR_ATTRIBUTES_CONFIG_FILE)
  attributesToRead = readCarAttributesConfig(CAR_ATTRIBUTES_CONFIG_FILE)
  mqttConfig = readMqttConfig(MQTT_CONFIG_FILE)
  obdConnection = None

  addHomeAssistantConfigToMqtt(mqttConfig, carProperties, attributesToRead)

  while True:
    attributesWereRead = False

    try:
      log.info("Attempting to read from OBD device...")
      obdConnection = obd.OBD() # auto-connects to USB or RF port
      printSupportedCommands(obdConnection)

      if obdConnection.status() == obd.OBDStatus.CAR_CONNECTED: # car is on
        car = readCarAttributes(obdConnection, attributesToRead)
        attributesWereRead = True
        log.debug("Car values = " + str(car)) #TODO debug
        log.info("Successfully read from OBD device.")
        publishToMqtt(car, mqttConfig)
      elif obdConnection.status() == obd.OBDStatus.OBD_CONNECTED: # car is off
        log.info("Car is off, will wait for ignition.")

    except SerialException as e:
      log.error("Error occurred connecting to OBD device: " + str(e))

    finally:
      if obdConnection != None:
        obdConnection.close()

    sleepBeforeNextRead(attributesWereRead)


def addHomeAssistantConfigToMqtt(config, carProperties, carAttributes):
  log.info("Creating Home Assistant config in MQTT...")
  carName = carProperties["name"]

  messages = []
  for attribute in carAttributes:
    message = {}
    
    message["name"] = carName + " " + carAttributes[attribute]["name"]
    message["unit_of_measurement"] = carAttributes[attribute]["unit_of_measurement"]
    if carAttributes[attribute]["ha_device_class"] != "None":
      message["device_class"] = carAttributes[attribute]["ha_device_class"]
    
    message["state_topic"] = MQTT_STATE_TOPIC
    message["value_template"] = "{{ value_json.%s }}" % attribute
    
    message["device"] = {}
    message["device"]["manufacturer"] = carProperties["manufacturer"]
    message["device"]["model"] = carProperties["model"]
    message["device"]["name"] = carProperties["name"]
    message["device"]["identifiers"] = [carProperties["name"]]

    topic = MQTT_HOME_ASSISTANT_TOPIC_BASE + attribute + "/config"
    messages.append({"topic": topic, "payload": json.dumps(message)})

  log.debug(messages)

  MqttPublish.multiple(
    msgs=messages,
    hostname=config["host"],
    port=config["port"],
    keepalive=config["keepalive"],
    auth=config["auth"]
  )
  log.info("Successfully created HomeAssistant config in MQTT.")


def publishToMqtt(payload, config):
  log.info("Publishing to MQTT...")
  MqttPublish.single(
    topic=MQTT_STATE_TOPIC,
    hostname=config["host"],
    port=config["port"],
    keepalive=config["keepalive"],
    auth=config["auth"],
    payload=json.dumps(payload)
  )
  log.info("Successfully sent to MQTT.")


def readCarAttributes(obdConnection, attributesToRead):
  car = {}
  for attributeKey in attributesToRead:
    attributeValue = eval("obdConnection.query(obd.commands.%s).value" % attributesToRead[attributeKey]["obd_key"]) #TODO Can I sanitise this first?
    #FIXME Find a better way to check if the attributeValue is a Quantity class
    try:
      car[attributeKey] = attributeValue.magnitude
    except:
      car[attributeKey] = attributeValue
  return car


def printSupportedCommands(obdConnection):
  log.debug("Supported commands: ")
  for command in obdConnection.supported_commands:
    log.debug(str(command))
  log.debug("")


def sleepBeforeNextRead(attributesWereRead):
  if attributesWereRead:
    sleepTime = SLEEP_SECONDS_AFTER_READ
  else:
    sleepTime = SLEEP_SECONDS_NO_READ
  log.info("Sleeping for %d seconds..." % sleepTime)
  time.sleep(sleepTime) #sleep before trying again


def readCarPropertiesConfig(filename):
  log.info("Reading config from file: \'%s\'" % str(filename))
  carProperties = {}
  with open(filename, "r") as file:
    carProperties = yaml.load(file, Loader=yaml.FullLoader)["car"]
    log.info("Car properties read: " + str(carProperties))
  return carProperties


def readCarAttributesConfig(filename):
  log.info("Reading config from file: \'%s\'" % str(filename))
  carAttributes = {}
  with open(filename, "r") as file:
    carAttributes = yaml.load(file, Loader=yaml.FullLoader)["attributes"]
    log.info("Read %d attributes." % len(carAttributes))
  return carAttributes


def readMqttConfig(filename):
  log.info("Reading config from file: \'%s\'" % str(filename))
  mqttConfig = {}
  with open(filename, "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    mqttConfig = config["mqtt"]
    log.info("MQTT config successfully read.")
  return mqttConfig


main()