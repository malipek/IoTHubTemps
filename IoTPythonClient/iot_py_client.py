#!/usr/bin/python3
""" Program reads temperatures from connected Arduino device
https://github.com/malipek/IoTHubTemps/tree/master/Arduino/temps
and sends them as a message to Azure IoT Hub
"""
import os
import sys
import json
#import serial

# https://github.com/Azure/azure-iot-sdk-python
# pip3 install azure-iot-device
from azure.iot.device import IoTHubDeviceClient, Message

def get_iot_connection_string():
    """ Returns Azure IoT Hub connection string read from environment variable IOT_CS

        The device connection string to authenticate the device with your IoT hub.
        Using the Azure CLI:
        az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} \
        --device-id MyNodeDevice --output table
        export "IOT_CS=HostName=iot_azurehub_host;DeviceId=MyNodeDevice;\
        SharedAccessKey=access_key_b64

    """
    try:
        os.environ["IOT_CS"]
    except KeyError:
        print("Please set the environment variable IOT_CS with Azure IoT connection string")
        sys.exit(1)
    return os.environ.get("IOT_CS")

def get_iot_temps():
    """ Reads JSON from connected Arduino board with temps.ino program
    https://github.com/malipek/IoTHubTemps/tree/master/Arduino/temps

    Returns temps list

    """
    # todo - communication with arduino
    json_obj = '{"temps":[18.63,22.56,16.56]}'
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
    TEMPS = get_iot_temps()
    LABELS = get_labels_for_temps(TEMPS)
    CLIENT = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    if CLIENT:
        MESSAGE = Message(prepare_iot_message(LABELS, TEMPS))
        print("Sending message: {}".format(MESSAGE))
        CLIENT.send_message(MESSAGE)
        print("Message successfully sent")
