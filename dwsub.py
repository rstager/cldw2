from __future__ import print_function
import paho.mqtt.client as paho
from struct import *
import binascii
from dwutil import *
import time, threading
from scipy.optimize import leastsq
from numpy import mean, std

import json

t0=time.time()

def distance(a, b):
    return math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2))

globaldr=5
class Anchor:
    def __init__(self, id):
        self.id = id
        self.x = 0
        self.y = 0
        self.fixed = False
        self.solnidx= 0
    def loc(self,x,y):
        self.x=x
        self.y=y
        self.fixed=True

anchorTable = factorydict(lambda id: Anchor(id))


class Tag:
    def __init__(self, id):
        self.id = id
        self.x = 0
        self.y = 0
        self.history_x=[]
        self.history_y=[]
    def loc(self,x,y):
        self.x=x
        self.y=y

    def record(self, loc, props):
        self.history_x.append(loc[0])
        self.history_y.append(loc[1])
        #self.history_prop[id].append(loc[1])
        if len(self.history_x) > 100:
            self.history_x.pop(0)
            self.history_y.pop(0)

tagTable = factorydict(lambda id: Tag(id))

class Range:
    def __init__(self, id):
        (self.pong, self.ping) = id
        self.M1sequence = -1
        self.Treply1 = 0
        self.Tround1 = 0
        self.Treply2 = 0
        self.Tround2 = 0
        self.Tprop = 0
        self.q1 = 0
        self.q2 = 0
        self.q3 = 0
        self.q4 = 0
        self.delta = 0
        self.history = []
        self.raw1=0
        self.timestamp=0

    def record(self, t):
        self.delta=abs(self.Tprop-t)
        self.Tprop = t
        self.history.append(t)
        self.timestamp=time.time()
        if len(self.history) > 10: self.history.pop(0)

    def mean(self):
        if len(self.history)>0:
            return mean(self.history)
        else:
            return 0
    def std(self):
        return std(self.history)


tprop = factorydict(lambda id: Range(id))


def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    headingcnt = 0

histogram=[0]*100

def on_message(client, userdata, msg):
    if (len(msg.payload) < 14):
        return
    #print(binascii.hexlify(msg.payload))

    (report_addr, count) = unpack_from("<HH", msg.payload);
    #print(msg.topic+" "+str(msg.qos)+" ",len(msg.payload)," addr=",report_addr," count= ",count)
    offset = 4
    for idx in range(count):
        if len(msg.payload) < offset + 16:
            continue
        (Treply1, Tround1, Treply2, Tround2, pong_addr, ping_addr, rx_fqual1, rx_fqual2,rx_fqual3,rx_fqual4, M1sequence, flags) = unpack_from("<IIIIHHHHHHBB", msg.payload, offset=offset);
        #print("report={:05d} ping={:05d} pong={:05d} seq={:3d} flags={:2x} Treply={:10d} Tround={:10d}  Treply={:10d} Tround={:10d} q1={:6d} q2={:6d} q3={:6d} q4={:6d} ".format(report_addr, ping_addr, pong_addr, M1sequence, flags, Treply1, Tround1, Treply2, Tround2, rx_fqual1, rx_fqual2,rx_fqual3,rx_fqual4))
        offset += 32
        if (Treply1 == 0 and Tround1 == 0):
            pass
        if (flags == 0):
            leg = tprop[(ping_addr, pong_addr)]
            leg.Treply1 = Treply1
            leg.Tround1 = Tround1
            leg.Treply2 = Treply2
            leg.Tround2 = Tround2
            leg.M1sequence == M1sequence
            leg.record(TIMEUNITS_TO_NS(leg.Tround1 - leg.Treply2 + leg.Tround2 - leg.Treply1) / 4.0)
            leg.q1=rx_fqual1
            leg.q2=rx_fqual2
            leg.q3=rx_fqual3
            leg.q4=rx_fqual4
            #print("ping:{:5d} pong:{:5d} Tprop:{:6.2f}".format(leg.ping,leg.pong,leg.Tprop))
            #leg.raw2=leg.raw1
            #leg.raw1=leg.Tround1 - leg.Treply2 + leg.Tround2 - leg.Treply1
            #if(leg.raw1!=0 and leg.raw2!=0 and pong_addr==39336):
                #diff=abs(leg.raw1-leg.raw2)
                #print("{:6.1f} {:012x} {:012x} diff={:012x} round={:012x} {:012x} reply={:012x} {:012x} prop={:012x} {:012x}".format(leg.Tprop, leg.raw1, leg.raw2, diff,
                # #                                                                                                                    leg.Tround1 , leg.Tround2,
                #                                                                                                                     leg.Treply1,leg.Treply2,leg.Tround1-leg.Treply2,leg.Tround2-leg.Treply1))
             #   if (diff>>4)<100:
            #        histogram[diff>>4]+=1

            if leg.Tprop < 300:
                print("anchor={:05d} tag={:05d} tprop={:6.1f}".format(leg.anchor, leg.tag, leg.Tprop))
                print(leg.Treply1, leg.Tround1, leg.Treply2, leg.Tround2, leg.M1sequence, M1sequence)


'''
'''

client = paho.Client()
client.on_subscribe = on_subscribe
client.on_message = on_message
client.tls_set("server.crt", certfile="client.crt", keyfile="client-nopass.key")
# client.tls_set("/usr/local/etc/mosquitto/server.crt",certfile="client.crt",keyfile="client.key",tls_version=ssl.PROTOCOL_TLSv1)
client.tls_insecure_set(True)
client.connect("192.168.1.69", 8883)
client.subscribe("/tprop", qos=1)

anchorids = []
tagids = []


def distance(a, b):
    return math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2))


def distance4(x1, y1, x2, y2):
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def anchorResidual(vars, atprops):
    resid = []
    v = vars.tolist()
    dr=vars[len(vars)-1]
    for ping, pong, t in atprops:
        if ping.fixed:
            x1=ping.x
            y1=ping.y
        else:
            x1 = v[ping.solnidx]
            y1 = v[ping.solnidx + 1]
        if pong.fixed:
            x2=pong.x
            y2=pong.y
        else:
            x2 = v[pong.solnidx]
            y2 = v[pong.solnidx + 1]
        #print (t,(FT_TO_NS(distance4(x1, y1, x2, y2)) + 510 + dr))
        resid.append((t) - (FT_TO_NS(distance4(x1, y1, x2, y2)) + 510 + dr))  # ydata-f(x,params)
    return resid


def generateAnchorLocations():
    cidx = -1
    oidx = -1
    v = []
    v=[]
    idx=0
    for a in anchorTable.values():
        if not a.fixed:
            v.append(a.x)
            v.append(a.y)
            anchorTable[a.id].solnidx=idx #maybe we should make a deep copy and change that
            idx+=2
    v.append(0)  # add a common dr
    atprops = []
    for  ping in anchorTable.values():
        for  pong in anchorTable.values():
            if (ping != pong  and not (ping.fixed and pong.fixed) and tprop[ping.id, pong.id].Tprop != 0):
                atprops.append((ping, pong, tprop[ping.id, pong.id].mean()))

    if (len(atprops) < len(v)): return
    answer = leastsq(anchorResidual, v, (atprops),full_output=True,ftol=0.1)
    v = answer[0].tolist()
    globaldr = v.pop()
    for a in anchorTable.values():
        if not a.fixed:
            anchorTable[a.id].x=v.pop(0)
            anchorTable[a.id].y=v.pop(0)
    print("answers=", answer[3], answer[4], globaldr)

def tagResidual(vars,tag,atprops,dr):
    x=vars[0]
    y=vars[1]
    resid=[]
    for pong, t,d in atprops:
        resid.append( (t) - (FT_TO_NS(distance4(x, y, pong.x, pong.y)) + 510 + dr)) # ydata-f(x,params)
    return resid


def locateTag(tagid):
    atprops=[]
    v=[0,0]
    for a in anchorTable.values():
        tp=tprop[tagid,a.id]
        valid=(tp.timestamp-time.time()<1.5)
        delta=tp.delta
        t=tprop[tagid,a.id].Tprop
        if t>0 and valid and delta<3:
            atprops.append((a,t,delta))
    if len(atprops)<2: return (0,0),[]
    satprops=sorted(atprops, key=lambda tp: tp[1])
    solntprops=satprops[:4]
    answer = leastsq(tagResidual, v, (tagid,solntprops,globaldr),full_output=True,ftol=0.1)
    return (answer[0][0],answer[0][1]),solntprops


headingcnt = 8


def periodic():
    global headingcnt
    global anchorids, tagids
    if (headingcnt > 10):
        tagids = sorted(set([ping for (ping, pong) in tprop.keys() if IS_TAG(ping)]))
        anchorids = sorted(set([pong for (ping, pong) in tprop.keys() if not IS_TAG(pong)]))
        if len(anchorids) > 3:
            generateAnchorLocations()
        if len(anchorids) > 0:
            print()
            print("anchor tprop dr=",globaldr)
            print("       ", end='')
            for addr in anchorids:
                print("  {:05d} ".format(addr), end='')
            print()
            for ping in anchorids:
                print("  {:05d}|".format(ping), end='')
                for pong in anchorids:
                    print("{:6.1f}  ".format(tprop[(ping, pong)].mean()), end='')
                anchor = anchorTable[ping]
                print(" {:3.1f} {:3.1f}".format(anchor.x, anchor.y), end='')
                print()
            print()
            print("anchor std")
            print("       ", end='')
            for addr in anchorids:
                print("  {:05d} ".format(addr), end='')
            print()
            for ping in anchorids:
                print("  {:05d}|".format(ping), end='')
                for pong in anchorids:
                    print("{:6.3f}  ".format(tprop[(ping, pong)].std()), end='')
                anchor = anchorTable[ping]
                print(" {:3.1f} {:3.1f}".format(anchor.x, anchor.y), end='')
                print()
            print()
            print("tag tprop")
            print("             ", end='')
            for addr in anchorids:
                print("  {:05d}       ".format(addr), end='')
            print()
            for a in anchorTable.values():
                jstr = json.dumps({'id':a.id,'type':'anchor','x':a.x,'y':a.y})
                client.publish("/tagat", payload=jstr, qos=1)
        headingcnt = 0
    else:
        headingcnt += 1

    timestamp=time.time()-t0
    for ping in tagids:
        print("{:5.0f}  {:05d}  ".format(timestamp,ping), end='')
        for pong in anchorids:
            tp=tprop[(ping, pong)]
            print("{:6.1f}{} {:5d} ".format(tp.Tprop,("*" if (time.time()-tp.timestamp)>1.1 else " "),tp.q1),end='')
        loc,atprops=locateTag(ping)

        jtprops=[(a.id,t-510-globaldr) for (a,t,d) in atprops]
        jstr = json.dumps({'id':ping,'type':'tag','x':loc[0],'y':loc[1],'t':timestamp,'tprops':jtprops})
        client.publish("/tagat", payload=jstr, qos=1)
        print("{:6.1f}  {:6.1f}  ".format(loc[0],loc[1]), end='')
        print()

    timer = threading.Timer(1.2, periodic)
    timer.daemon = True
    timer.start()
anchorTable[49951].loc(18,3.5)
anchorTable[59303].loc(36,1)
anchorTable[59770].loc(20.5,28)
anchorTable[52962].loc(34,27) 
anchorTable[39336].loc(0,12)
anchorTable[61368].loc(18,11)
anchorTable[65022].loc(7,25)
#anchorTable[49951].loc(20,3.5)
#anchorTable[59303].loc(2,1)/
#anchorTable[59770].loc(15.5,28)
#anchorTable[52962].loc(2,27) 
#anchorTable[39336].loc(37.5,12)
#anchorTable[59303].loc(3.5,5)
periodic()

client.loop_forever()
# mosquitto_sub -v -p 8883 -t /test --cafile /usr/local/etc/mosquitto/server.crt --cert client.crt --key client.key --tls-version tlsv1 --insecure
