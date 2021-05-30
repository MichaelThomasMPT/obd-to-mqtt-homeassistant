NOTE: This readme is very much a work in progress, and is currently just a braindump of things to remember. 

TODO: Add dockerfile with:

    pip install obd
    pip install pyyaml
    pip install paho-mqtt
    sudo apt-get update
    sudo apt-get install bluetooth bluez blueman

Step 2 - Connect OBD Adapater via Bluetooth

    bluetoothctl
    help <-- see all the commands
    show
    power on
    pairable on
    agent on <-- used for persisting pairing code
    default-agent
    scan on <-- find OBDII and its MAC address
    pair <mac_address> <-- enter pin 1234
    trust <mac_address> <-- this will allow Pi to automatically pair with the device next time
    scan off
    quit

Step 4 - Connect Car with Python OBD

    Create a serial port: sudo rfcomm bind hci0 <mac_address>
    Run the program: python3 obd_reader.py
    See a list of commands here


TODO: implement proper logging
TODO: Look at todos
TODO: Instructions for copying and setting up config files
