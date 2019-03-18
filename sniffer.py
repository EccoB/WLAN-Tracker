#!/usr/bin/env python
import subprocess
import threading
from threading  import Thread
import os
import time
import sys
from datetime import datetime
import json
import paho.mqtt.client as mqtt

print("Example run: docker run -e WDEVICE=wlx001d43b0063a --privileged --net=host ebaeum/wlantracker")
timeout=1*60  #after 10 minutes, we consider the device as dead
deadtime=60
refresh=5
server="192.168.2.111"
try:
    print(os.environ['WDEVICE'])
    print(os.environ['SERVER'])
    server=os.environ['SERVER']
    timeout=os.environ["TIMEOUT"]
    refresh=os.environ['REFRESHRATE']

except KeyError:
    print("Not all environment variables were set: WDEVICE, SERVER, TIMEOUT, REFRESHRATE")


wdevice=os.environ['WDEVICE']

#------------ MQTT ---------------------------------
#apt install python-pip
#pip install paho-mqtt
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
client = mqtt.Client()
client.on_connect = on_connect

client.connect(server, 1883, 60)

client.loop_start()


seen =dict()
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            #return o.isoformat()
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        return json.JSONEncoder.default(self, o)

def emit(entry):
    global client
    file=json.dumps(entry, cls=DateTimeEncoder)
    print(json.loads(file))
    client.publish("stat/wlan",file,retain=False)

def emitState(list):
    global client
    file=json.dumps(list, cls=DateTimeEncoder)
    print(json.loads(file))
    client.publish("stat/wlanstate",file,retain=True)


lock = threading.Lock()
stopthread=False
def checkOnline():
    global stopthread
    global seen
    global checkThr
    global refresh
    while True:
        if(stopthread==True):
            break
        updated=False
        todelete=[]
        lock.acquire()
        for key in seen:
            entry=seen[key]
            print(entry)
            if(entry["state"]==1 and ((datetime.now()-entry["lseen"]).total_seconds()>timeout)):
                #Consider this device as offline
                print("Device is offline")
                entry["state"]=0
                entry["emitted"]=datetime.now()
                emit(entry)
                seen.update({key:entry})
                updated=True
            elif(entry["state"]==0 and ((datetime.now()-entry["lseen"]).total_seconds()>timeout*20)):
                #Clean our state
                print("Devie is offline for a long time")
                todelete.append(key)
                updated=True
        if(updated):
            for key in todelete:
                del seen[key]
        lock.release()
        emitState(seen)
        time.sleep(refresh)





#### ------------- Main Logic -------------------------------------


sendbeacon=False
def computeS(str):
    global seen
    global timeout
    global sendbeacon
    global deadtime
    mac=str
    try:
        if(len(mac) <10):
            return
    except:
        print("Error")
        return
    print(mac)
    if mac in seen:
        entry=seen[mac]
        #print(entry)
        timediff=datetime.now()-entry["lseen"]
        diffemitted=datetime.now()-entry["emitted"]

        if(timediff.total_seconds()>timeout):
            #Timeout: this device was offline, set the seen since to on
            entry["state"]=1
            entry["since"]=datetime.now()
            emit(entry)

        entry["lseen"]=datetime.now()

        if(sendbeacon==True and ((datetime.now()-entry["emitted"]).total_seconds()>deadtime or (timediff.total_seconds()>60))):
            print("Is here",mac)
            entry["emitted"]=datetime.now()
            emit(entry)
        lock.acquire()
        seen.update({mac:entry})
        lock.release()
    else:
        # ---- First seen:
        entry={"mac":mac,"lseen":datetime.now(),"since":datetime.now(),"emitted":datetime.now(),"state":1}
        lock.acquire()
        seen.update({mac:entry})
        lock.release()
        print("New",mac)
        emit(entry)





def compute(line):
    print(line)

#pipe=subprocess.Popen("tshark -l -i wlx001d43b0063a -T fields -e wlan.sa subtype probereq",stdout=subprocess.PIPE,shell=True)
def startup():
	global pipe
	subprocess.Popen("ip link set dev "+wdevice+" down && iwconfig "+wdevice+" mode monitor && ip link set dev "+wdevice+" up",shell=True)
	pipe=subprocess.Popen("tshark -l -i "+wdevice+" -T fields -e wlan.sa",stdout=subprocess.PIPE,shell=True)
startup()
#dann halt ohne PIPE
isdied=0
loops=0
checkThr=threading.Timer(refresh, checkOnline)
checkThr.start()
try:
    while 1:
        line = pipe.stdout.readline()
        if line.rstrip != '':
            computeS(line.rstrip().decode('UTF-8'))
            loops =loops+1
            if(isdied>0 and loops >100):
                print("Seems everything ok - resetting")
                isdied=0
        else:
            time.sleep(1)


        poll=pipe.poll()
        if poll!=None:
            if(isdied>5):
                print("Subprocess died again, giving up")
                sys.exit(1)
            print("Subprocess died, respaning")
            startup()
            time.sleep(1)
            isdied=isdied+1
            loops=0
except (KeyboardInterrupt, SystemExit):
    stopthread=True
    sys.exit()
