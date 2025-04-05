#!/usr/bin/env python3

try:
    import simplejson as json
except ImportError:
    import json
import requests
from requests.auth import HTTPBasicAuth
import base64
import argparse
import time
import paho.mqtt.client as mqtt

from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceBase, MqttDeviceSettings
from ha_mqtt.mqtt_thermometer import MqttThermometer
from ha_mqtt.mqtt_sensor import MqttSensor
from ha_mqtt.util import HaDeviceClass

debug_mode = False


# Special sensor for device class none
class MqttSensorNone(MqttDeviceBase):
    """
    class that implements an arbitrary sensor such as a thermometer
    :param unit: string containing the unit of measurement, example: '°C'
    :param device_class: a entry of the deviceclass enum containing the device class as in
           https://www.home-assistant.io/integrations/sensor/#device-class
    :param settings: as in :class:`~ha_mqtt.mqtt_device_base.MqttDeviceBase`
    .. hint::
       Use :meth:`~ha_mqtt.mqtt_device_base.MqttDeviceBase.publish_state`
       to send the actual sensor data to homeassistant
    """
    device_type = "sensor"

    def __init__(self, settings: MqttDeviceSettings, unit: str, device_class: HaDeviceClass
                 , send_only=False):
        """
        create sensor instance
        """
        self.device_class = device_class
        self.unit_of_measurement = unit
        super().__init__(settings, send_only)

    def pre_discovery(self):
        self.add_config_option("unit_of_measurement", self.unit_of_measurement)


class MqttBinarySensor(MqttDeviceBase):
    """
    class that implements an arbitrary sensor such as a thermometer
    :param unit: string containing the unit of measurement, example: '°C'
    :param device_class: a entry of the deviceclass enum containing the device class as in
           https://www.home-assistant.io/integrations/sensor/#device-class
    :param settings: as in :class:`~ha_mqtt.mqtt_device_base.MqttDeviceBase`
    .. hint::
       Use :meth:`~ha_mqtt.mqtt_device_base.MqttDeviceBase.publish_state`
       to send the actual sensor data to homeassistant
    """

    device_type = "binary_sensor"

    def __init__(self, settings: MqttDeviceSettings,
                 device_class: HaDeviceClass,
                 send_only=False):
        """
        create sensor instance
        """
        self.device_class = device_class
        super().__init__(settings, send_only)

    def pre_discovery(self):
        if isinstance(self.device_class, str):
            self.add_config_option("device_class", self.device_class)
        elif self.device_class.value != 'None':
            self.add_config_option("device_class", self.device_class.value)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Debug mode')
    parser.add_argument("--host", help="Hostname or IP of APEX",
                        required=True)
    parser.add_argument("--auser", help="Apex Username", default="admin")
    parser.add_argument("--apassword", help="Apex Password", default="1234")
    parser.add_argument("--file", help="Read json file, not connect",
                        action='store', default=None)
    parser.add_argument('--poll_time', type=int, action='store',
                        default=60,
                        help='How often in seconds to poll the apex (60)')
    # parser.add_argument('-t', '--topic', type=str, action='store',
    #                     default='hass_apex/', help='MQTT Topic')
    parser.add_argument('-n', '--name', type=str, action='store',
                        default='apex', help='Sensor name')
    parser.add_argument('-u', '--user', type=str, action='store',
                        default=None, help='MQTT Username')
    parser.add_argument('-w', '--password', type=str, action='store',
                        default=None, help='MQTT Password')
    parser.add_argument('-i', '--client_id', type=str, action='store',
                        default='apex', help='MQTT Broker')
    parser.add_argument('--broker', type=str, action='store',
                        default='127.0.0.1', help='MQTT Broker')

    args = parser.parse_args()
    return args


def init_mqtt(broker, args):
    global debug_mode
    c_id = args.host
    try:
        mq_client = mqtt.Client(client_id=c_id)
        if args.user is not None and args.password is not None:
            mq_client.username_pw_set(username=args.user, password=args.password)
        mq_client.connect(broker, 1883)
        mq_client.loop_start()
    except Exception:
        print("Unable to connect to MQTT broker at {0}".format(str(broker)))
        exit(1)
    return mq_client


def poll_apex(mq_client, args):

    # do an initial connect, and setup the topics

    url = 'http://' + args.host + '/cgi-bin/status.json'

    try:
        req = requests.get(url, auth=(args.auser, args.apassword),
                           timeout=15)
        # print(req)
        jdata = req.json()
    except Exception as e:
        print("Connection failed on {0} : {1}".format(str(url), str(e)))
        exit(1)

    # First, grab the hostname
    hostname = jdata['istat']['hostname']
    serial = jdata['istat']['serial'].replace(':', '_')

    # set a now
    now_sec = jdata['istat']['date']

    # Setup the device entry
    ha_dev = HaDevice(name=hostname, unique_id=serial)
    ha_dev.add_config_option(key='manufacturer', value='Neptune')
    if 'type' in jdata['istat']:
        ha_dev.add_config_option(key='model', value=jdata['istat']['type'])
    else:
        ha_dev.add_config_option(key='model', value='AC4')
    ha_dev.add_config_option(key='hw_version', value=jdata['istat']['hardware'])
    ha_dev.add_config_option(key='sw_version', value=jdata['istat']['software'])
    # ha_dev.add_config_option(key='via_device', value=jdata['istat']['serial'].replace(':', '_'))

    mqtt_apex = dict()

    # first, the inputs
    for idx,input in enumerate(jdata['istat']['inputs']):
        #print(f'{hostname} {input["name"]}' + ' ' + f'{hostname}_{input["did"]}')
        base_settings = MqttDeviceSettings(
            name=f'{hostname} {input["name"]}',
            unique_id=f'{serial}_{input["did"]}',
            client=mq_client,
            device=ha_dev,
        )
        if input['type'] == 'Temp':
            mqtt_apex[input['did']] = MqttSensor(
                base_settings,
                unit='°F',
                device_class=HaDeviceClass.TEMPERATURE,
            )
        if input['type'] == 'pH':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='pH',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'Cond':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='mS',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'Amps':
            mqtt_apex[input['did']] = MqttSensor(
                base_settings,
                unit='A',
                device_class=HaDeviceClass.CURRENT,
            )
        if input['type'] == 'digital':
            mqtt_apex[input['did']] = MqttBinarySensor(
                base_settings,
                device_class=HaDeviceClass.OPENING,
            )
        if input['type'] == 'ORP':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='ORP',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'pwr':
            mqtt_apex[input['did']] = MqttSensor(
                base_settings,
                unit='W',
                device_class=HaDeviceClass.POWER,
            )
        if input['type'] == 'volts':
            mqtt_apex[input['did']] = MqttSensor(
                base_settings,
                unit='V',
                device_class=HaDeviceClass.VOLTAGE,
            )
        if input['type'] == 'alk':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='dKH',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'ca':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='ppm',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'mg':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='ppm',
                device_class=HaDeviceClass.NONE,
            )
        if input['type'] == 'gph':
            mqtt_apex[input['did']] = MqttSensorNone(
                base_settings,
                unit='gph',
                device_class=HaDeviceClass.NONE,
            )

    # now, the outputs
    for idx,output in enumerate(jdata['istat']['outputs']):
        base_settings = MqttDeviceSettings(
            name=f'{hostname} {output["name"]}',
            unique_id=f'{serial}_{output["did"]}',
            client=mq_client,
            device=ha_dev,
        )
        if output['type'] == 'variable' or output['type'] == 'serial' or output['type'] == 'sky' or output['type'] == 'moon':
            mqtt_apex[output['did']] = MqttSensorNone(
                base_settings,
                device_class=HaDeviceClass.NONE,
                unit='%',
            )
        if output['type'] == 'alert':
            mqtt_apex[output['did']] = MqttBinarySensor(
                base_settings,
                device_class=HaDeviceClass.PROBLEM,
            )
        if output['type'] == 'outlet' or output['type'] == '24v' or output['type'] == 'virtual' or output['type'] == 'afs' or output['type'] == 'dos' or output['type'] == 'selector':
            mqtt_apex[output['did']] = MqttBinarySensor(
                base_settings,
                device_class='power'
            )

        # COR's are super fiddly
        if 'cor' in output['type']:
            mqtt_apex[output['did']] = MqttBinarySensor(
                base_settings,
                device_class='power'
            )
            mqtt_apex[output['did'] + '_1'] = MqttSensorNone(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} Duty',
                    unique_id=f'{serial}_{output["did"]}_1',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.NONE,
                unit='%',
            )
            mqtt_apex[output['did'] + '_4'] = MqttSensorNone(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} RPM',
                    unique_id=f'{serial}_{output["did"]}_4',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.NONE,
                unit='RPM',
            )
            mqtt_apex[output['did'] + '_6'] = MqttSensor(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} Power',
                    unique_id=f'{serial}_{output["did"]}_6',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.POWER,
                unit='W',
            )

        # WAV's are more fiddly than COR's
        if output['type'] == 'wav':
            mqtt_apex[output['did']] = MqttBinarySensor(
                base_settings,
                device_class='power'
            )
            mqtt_apex[output['did'] + '_1'] = MqttSensorNone(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} Duty',
                    unique_id=f'{serial}_{output["did"]}_1',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.NONE,
                unit='%',
            )
            mqtt_apex[output['did'] + '_4'] = MqttSensorNone(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} RPM',
                    unique_id=f'{serial}_{output["did"]}_4',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.NONE,
                unit='RPM',
            )
            mqtt_apex[output['did'] + '_5'] = MqttSensor(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} Temperature',
                    unique_id=f'{serial}_{output["did"]}_5',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.TEMPERATURE,
                unit='°F',
            )

        # A DOS is slightly fiddly
        if output['type'] == 'dos':
            mqtt_apex[output['did'] + '_4'] = MqttSensorNone(
                MqttDeviceSettings(
                    name=f'{hostname} {output["name"]} total dosage',
                    unique_id=f'{serial}_{output["did"]}_4',
                    client=mq_client,
                    device=ha_dev,
                ),
                device_class=HaDeviceClass.NONE,
                unit='ml',
            )


    # Now loop forever and gather the data
    while(True):
        try:
            req = requests.get(url, auth=(args.auser, args.apassword),
                               timeout=15)
            # print(req)
            json_data = req.json()
            # print(json_data)
            for idx,input in enumerate(json_data['istat']['inputs']):
                if input['did'] in mqtt_apex:
                    # special type handlers
                    if input['type'] == 'digital':
                        if input['value']:
                            mqtt_apex[input['did']].publish_state('ON')
                        else:
                            mqtt_apex[input['did']].publish_state('OFF')

                    # generic fallback float
                    else:
                        mqtt_apex[input['did']].publish_state(float(input['value']))
            for idx,output in enumerate(json_data['istat']['outputs']):
                if output['did'] in mqtt_apex:
                    # all outputs are special
                    if output['type'] == 'variable' or output['type'] == 'serial' or output['type'] == 'sky' or output['type'] == 'moon':
                        if output['status'][1] == '':
                            mqtt_apex[output['did']].publish_state(0.0)
                        else:
                            mqtt_apex[output['did']].publish_state(float(output['status'][1]))
                    if output['type'] == 'alert' or output['type'] == 'outlet' or output['type'] == '24v' or output['type'] == 'virtual' or output['type'] == 'afs' or output['type'] == 'dos' or output['type'] == 'selector':
                        
                        if 'ON' in output['status'][0] or 'TBL' in output['status'][0]:
                            state = 'ON'
                        else:
                            state = 'OFF'
                        mqtt_apex[output['did']].publish_state(state)

                    # COR
                    if 'cor' in output['type']:
                        if 'ON' in output['status'][0] or 'TBL' in output['status'][0]:
                            state = 'ON'
                        else:
                            state = 'OFF'
                        mqtt_apex[output['did']].publish_state(state)
                        mqtt_apex[output['did'] + '_1'].publish_state(float(output['status'][1]))
                        mqtt_apex[output['did'] + '_4'].publish_state(float(output['status'][4]))
                        mqtt_apex[output['did'] + '_6'].publish_state(float(output['status'][6]))

                    # WAV
                    if output['type'] == 'wav':
                        if 'ON' in output['status'][0] or 'TBL' in output['status'][0]:
                            state = 'ON'
                        else:
                            state = 'OFF'
                        mqtt_apex[output['did']].publish_state(state)
                        mqtt_apex[output['did'] + '_1'].publish_state(float(output['status'][1]))
                        mqtt_apex[output['did'] + '_4'].publish_state(float(output['status'][4]))
                        mqtt_apex[output['did'] + '_5'].publish_state(float(output['status'][5]))

                    # DOS
                    if output['type'] == 'dos':
                        dout = 0.0
                        if output['status'][4] != '':
                            dout = float(output['status'][4])
                        mqtt_apex[output['did'] + '_4'].publish_state(dout)


        except Exception as e:
            print("Connection failed on {0} : {1}".format(str(url), str(e)))
            pass
        time.sleep(args.poll_time)


def main(args=None):
    args = parse_arguments()

    if args.debug:
        debug_mode = args.debug

    mq_client = init_mqtt(args.broker, args)

    poll_apex(mq_client, args)


if __name__ == "__main__":
    main()
