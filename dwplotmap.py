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
        self.t=[]
        self.tprop=0

logging = True

series=factorydict(lambda id: Tag(id))
aseries=factorydict(lambda id: Tag(id))

def on_plot_hover(event):
    print(event.ydata)
def onpick3(event):
    ind = event.ind
    print ('onpick3 scatter:', ind)


fig = plt.figure()
fig.canvas.mpl_connect('pick_event', onpick3)

def on_message(client, userdata, msg):
    report = json.loads(msg.payload)
    report=bunchify(report)

    if report.type=='tag':
        series[report.id].x.append(report.x)
        series[report.id].y.append(report.y)
        series[report.id].t.append(report.t)
        if not 'tprops' in report: return
        for id, v in aseries.items():
            v.tprop=0
        for (id,t) in report.tprops:
            aseries[id].tprop=t
    else:
        aseries[report.id].x=report.x
        aseries[report.id].y=report.y
        return

    plt.clf()
    plt.axis([0,40,0,28])
    for id,v in series.items():
        plt.plot(v.x[-100:],v.y[-100:])
        plt.plot(v.x[-1:],v.y[-1:],marker='o',markersize=10,label=id,gid=v.t)
    for id,v in aseries.items():
        plt.plot(v.x,v.y,marker='+',markersize=30,label=id)
        #plt.scatter(v.x, v.y, marker='o', s=(v.tprop)*100, facecolors='none', edgecolors='r')
    ax = plt.gca()
    for id, v in aseries.items():
        if v.tprop == 0 : continue
        print(id,v.tprop,v.x,v.y)
        circle1 = plt.Circle((v.x,v.y), v.tprop*0.9835, color='r',fc='none',alpha=0.2)
        ax.add_artist(circle1)
    plt.legend(loc='lower left', shadow=True)
    plt.pause(0.1)



client = paho.Client()

client.on_message = on_message
client.tls_set("./server.crt", certfile="client.crt", keyfile="client-nopass.key")
# client.tls_set("/usr/local/etc/mosquitto/server.crt",certfile="client.crt",keyfile="client.key",tls_version=ssl.PROTOCOL_TLSv1)
client.tls_insecure_set(True)
client.connect("192.168.1.69", 8883)
client.subscribe("/tagat", qos=1)
plt.ion()
client.loop_forever()
