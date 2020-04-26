#!/usr/bin/python3

import os
import sys
import json

# https://github.com/Azure/azure-iot-sdk-python
# pip3 install azure-iot-device
from azure.iot.device import IoTHubDeviceClient, Message

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} --device-id MyNodeDevice --output table
# export IOTP

def get_iot_connection_string():
    try:
        os.environ["IOT_CS"]
    except KeyError:
        print ("Please set the environment variable IOT_CS with Azure IoT connection string")
        sys.exit(1)
    return os.environ.get("IOT_CS")


def get_iot_temps():
    # todo - communication with arduino 
    JSON_OBJ = '{"temps":[18.63,22.56,16.56]}'
    # read object
    temps_obj = json.loads(JSON_OBJ)
    temps = temps_obj.get('temps')
    return temps


#  Lables for temperature measurements
#  set list in IOT_LABELS (JSON)
#  export 'IOT_LABELS=["Sensor 1","Sensor 2","Sensor 3"]'
#  If no labels are set Temp1, Temp2, Temp3, etc will be used

def get_labels_for_temps( temps ):
    labels = []
    try:
        if os.environ["IOT_LABELS"]:
            JSON_LABELS = os.environ.get("IOT_LABELS")
            labels = json.loads(JSON_LABELS)
            assert len(labels) == len(temps), "Count of labels doesn't match count of measured values"
    except KeyError:
        pass
    return labels

def prepare_iot_message( labels , temps ):
    MSG_TXT= ''
    index = 0
    measurements = {}
    assert len(temps) > 0 , "Empty measurements"
    for temp in temps:
        measurements[ labels[index] if labels else 'temp'+ str(index) ] = temp
        index = index + 1
    MSG_TXT = '{' + json.dumps(measurements) + '}'
    return MSG_TXT


if __name__ == '__main__':
    CONNECTION_STRING = get_iot_connection_string()
    temps = get_iot_temps()
    labels = get_labels_for_temps( temps )

    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    if client:
        message = Message( prepare_iot_message( labels, temps ) )
        print( "Sending message: {}".format(message) )
        client.send_message(message)
        print ( "Message successfully sent" )