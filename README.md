# neptuneapex-hass-mqtt
Neptune Apex to HASS MQTT gateway

This will connect to your Neptune Apex via the local API, and poll it every 60
seconds (by default).  It converts all the data into MQTT, and sets up
MQTT Discovery, and feeds it into an MQTT broker for Home Assistant.

This is a READ ONLY integration.  Yes, it's possible to flip switches and do
things in an Apex via the http API.  No, I have no interest in crashing my
aquarium like this.  The point of this integration is to simply pull data from
your aquarium into HASS, so you can do *other* automations in HASS based on it.
For example, by pulling in my aquarium's temperature, I might decide to run the
AC harder if it's going up too fast.

You could also theoretically use this to control your aquarium with HASS, like
read the pH out of HASS, and then tell an ESPHome device to flip a relay?  Up to
you there.

Devices supported:

* Temp
* pH
* ORP
* Salinity
* Switches (open/closed)
* Outlets
* COR
* WAV
* DOS
* Trident
* FLO
* Alarms
* Virtual Outlets
* ATF
* 24v accessories
* Amps
* Wattage

# install
   python3 ./setup.py install

# usage
```
usage: __main__.py [-h] [-d] --host HOST [--auser AUSER]
                   [--apassword APASSWORD] [--file FILE]
                   [--poll_time POLL_TIME] [-n NAME] [-u USER]
                   [-w PASSWORD] [-i CLIENT_ID] [--broker BROKER]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Debug mode
  --host HOST           Hostname or IP of APEX
  --auser AUSER         Apex Username
  --apassword APASSWORD
                        Apex Password
  --file FILE           Read json file, not connect
  --poll_time POLL_TIME
                        How often in seconds to poll the apex (60)
  -n NAME, --name NAME  Sensor name
  -u USER, --user USER  MQTT Username
  -w PASSWORD, --password PASSWORD
                        MQTT Password
  -i CLIENT_ID, --client_id CLIENT_ID
                        MQTT Broker
  --broker BROKER       MQTT Broker
  
Example:

/opt/neptuneapex-hass-mqtt/venv/bin/python3 /opt/neptuneapex-hass-mqtt/venv/bin/neptuneapex-hass-mqtt --host apex --broker mymqtt.local -u mqttuser -w mqttpass
```
