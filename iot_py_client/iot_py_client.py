#!/usr/bin/python3
""" Program reads temperatures from connected Arduino device
https://github.com/malipek/IoTHubTemps/tree/master/Arduino/temps
and sends them as a message to Azure IoT Hub
"""
import os
import sys
import json
import time
import serial

# https://github.com/Azure/azure-iot-sdk-python
# pip3 install azure-iot-device
from azure.iot.device import IoTHubDeviceClient, Message

def get_env_var(var_name):
    """ Returns env value for var_name
        Throws KeyException if not exists
    """
    try:
        os.environ[var_name]
    except KeyError:
        sys.stderr.write("Environment variable \"{}\" not set\n".format(var_name))
        sys.exit(1)
    return os.environ.get(var_name)

def get_serial_port():
    """ Returns serial port name form env variable
        IOT_PORT
        On Linux it's usually /dev/ttyACM0
        Find correct one with ls /dev/ttyACM* and expose with
        export IOT_PORT=/dev/ttyACMX

    """
    return get_env_var("IOT_PORT")

def get_iot_connection_string():
    """ Returns Azure IoT Hub connection string read from environment variable IOT_CS

        The device connection string to authenticate the device with your IoT hub.
        Using the Azure CLI:
        az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} \
        --device-id MyNodeDevice --output table
        export "IOT_CS=HostName=iot_azurehub_host;DeviceId=MyNodeDevice;\
        SharedAccessKey=access_key_b64

    """
    return get_env_var("IOT_CS")

def open_serial(port):
    """ Tries to open given serial port
        with 9600 baud - hardoced speed in arduino program
        Set timeout to 5s (proccesing sensors takes some time)
        returns pyserial instance
    """
    port = serial.Serial(port, 9600, timeout=5)
    assert port, "Port doesn't exists"
    time.sleep(2) #added due to lag when opening port
    # add longer sleep when connection tis timeouting
    return port

def close_serial(port):
    """ Check if port is opened anc lose it
    """
    if port.is_open:
        port.close()

def get_iot_temps(port):
    """ Reads JSON from connected Arduino board with temps.ino program
    https://github.com/malipek/IoTHubTemps/tree/master/Arduino/temps

    Returns temps list

    """
    command = "GET TEMPS"
    term_sign = "" # empty string for Andruino Leonardo
    message = command+term_sign
    port.write(message.encode())
    message = port.readline()
    if not message:
        # timeouted!
        close_serial(port)
        sys.stderr.write("Timeout exceeded when reading data\n")
        sys.exit(1)
    json_obj = message.decode()
    temps_obj = json.loads(json_obj)
    temps = temps_obj.get('temps')
    return temps

def get_labels_for_temps(temps):
    """ Returns list of lables for temperature measurements
    Set list in IOT_LABELS env variable (JSON)
    example: export 'IOT_LABELS=["Sensor 1","Sensor 2","Sensor 3"]'
    If no labels are set Temp1, Temp2, Temp3, etc will be used

    """
    labels = []
    try:
        if os.environ["IOT_LABELS"]:
            json_labels = os.environ.get("IOT_LABELS")
            labels = json.loads(json_labels)
            assert len(labels) == len(temps), ("Count of labels doesn't "\
            "match count of measured values")
    except KeyError:
        pass
    return labels

def prepare_iot_message(labels, temps):
    """Gets list of lables, list of temperatires
    Returns string - message in JSON format for client message

    """
    msg_txt = ''
    index = 0
    measurements = {}
    assert temps, "Empty measurements"
    for temp in temps:
        measurements[labels[index] if labels else 'temp'+ str(index)] = temp
        index = index + 1
    msg_txt = '{' + json.dumps(measurements) + '}'
    return msg_txt


if __name__ == '__main__':
    CONNECTION_STRING = get_iot_connection_string()
    PORT = open_serial(get_serial_port())
    TEMPS = get_iot_temps(PORT)
    close_serial(PORT)
    LABELS = get_labels_for_temps(TEMPS)
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    if CLIENT:
        MESSAGE = Message(prepare_iot_message(LABELS, TEMPS))
        print("Sending message: {}".format(MESSAGE))
        CLIENT.send_message(MESSAGE)
        print("Message successfully sent")
