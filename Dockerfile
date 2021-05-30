FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY obd-to-mqtt.py ./

CMD [ "python", "./obd-to-mqtt.py" ]