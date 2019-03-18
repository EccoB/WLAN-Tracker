# WLAN-Tracker
This python executeable implements a WLAN sniffer/tracker, capturing all MAC-Addresses that are passively received and sends them with additional data out via MQTT.
Could be useful for home-automatication as presence detection.

For this it puts a compatible wlan-device into monitor mode and listens passively for any incomming packets. If any packet is received, the MAC-Adress is stored together with a timestamp when this device was seen and how long. In regular intervals, this is sent to the MQTT-Server.

## Usage
### Using the python script
This script needs full access to the device, therefore it needs atm root privileges.
Set the environment variable WDEVICE to the name of your wlan-device.
f.ex. export WDEVICE=wlx001d43b0063a

### Running with docker
A dockerimage is availabe, set the environment variable according to your wlan-device and run the container f.ex.:
docker run -e WDEVICE=wlx001d43b0063a --privileged --net=host ebaeum/wlantracker
