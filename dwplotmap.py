import paho.mqtt.client as paho
from scipy.optimize import leastsq
import math
import matplotlib.pyplot as plt
from dwutil import *
import json
from neobunch import bunchify

class Tag:
    def __init__(self, id):
        self.id=id
        self.x=[]
        self.y=[]

logging = True

series=factorydict(lambda id: Tag(id))


def on_message(client, userdata, msg):
    report = json.loads(msg.payload)
    report=bunchify(report)
    series[report.id].x.append(report.x)
    series[report.id].y.append(report.y)

    plt.clf()
    plt.axis([-20,10,-10,10])
    for id,v in series.items():
        plt.plot(v.x[-100:],v.y[-100:],label=id)
    plt.legend(loc='upper left', shadow=True)
    plt.pause(0.1)



client = paho.Client()

client.on_message = on_message
client.tls_set("/usr/local/etc/mosquitto/server.crt", certfile="client.crt", keyfile="client-nopass.key")
# client.tls_set("/usr/local/etc/mosquitto/server.crt",certfile="client.crt",keyfile="client.key",tls_version=ssl.PROTOCOL_TLSv1)
client.tls_insecure_set(True)
client.connect("192.168.1.69", 8883)
client.subscribe("/tagat", qos=1)
plt.ion()
client.loop_forever()