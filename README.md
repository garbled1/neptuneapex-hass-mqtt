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
