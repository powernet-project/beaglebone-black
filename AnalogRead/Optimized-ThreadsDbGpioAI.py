# Based of:
# https://www.troyfawkes.com/learn-python-multithreading-queues-basics/

#OBS: Yuting's load model: real power at <=1min

import beaglebone_pru_adc as adc
import Adafruit_BBIO.GPIO as GPIO
import math
from Queue import Queue
from threading import Thread
from datetime import datetime
from firebase import Firebase as fb
import time
import copy
import logging
import requests
from raven import Client

client = Client('https://e3b3b7139bc64177b9694b836c1c5bd6:fbd8d4def9db41d0abe885a35f034118@sentry.io/230474')

# Global variables
nSamples = 100
convertion = 1.8/4095.0

# Initializing GPIOs:
# gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
applianceList = ["PW1", "RA1", "AC1", "DR1", "RF1","SE1"]
gpioDict = {"PW1": "P8_9", "RA1": "P8_10", "AC1":"P8_11", "DR1":"P8_12", "RF1":"P8_14", "SE1":"P8_15"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.LOW)


# Initializing Firebase
f = fb('https://fb-powernet.firebaseio.com/ApplianceTest09')
#f = fb('https://fb-powernet.firebaseio.com/OvernightTest')

def analogRead(off_value):
    capture = adc.Capture()
    capture.cap_delay = 50000
    capture.oscilloscope_init(adc.OFF_VALUES+off_value, nSamples)
    capture.start()
    while not (capture.oscilloscope_is_complete()):
        # This is a dumb condition just to keep the loop running
        False
    capture.stop()
    capture.wait()
    capture.close()
    return capture.oscilloscope_data(nSamples)

def producerAI(formatAI,qAI):
    #print "PRODUCER_AI..."
    while(True):
        dts = []    # date/time stamp for each start of analog read
        dts.append(str(datetime.now()))
        ai0 = analogRead(formatAI[0])
        dts.append(str(datetime.now()))
        ai1 = analogRead(formatAI[1])
        dts.append(str(datetime.now()))
        ai2 = analogRead(formatAI[2])
        #print "Putting AI Data..."
        tempAI = zip(ai0,ai1,ai2)
        tempQueue = [tempAI, dts]
        qAI.put(tempQueue)
        #print "Queue done..."
        time.sleep(2)


# Current RMS calculation for consumerAI
def RMS(data):
    # The size of sumI is the size of the AIN ports
    sumI = [0,0,0]
    for val in data:
        sumI[0]+=math.pow((val[0]*convertion-0.89),2)
        sumI[1]+=math.pow((val[1]*convertion-0.89),2)
        sumI[2]+=math.pow((val[2]*convertion-0.89),2)

    rmsA0 = math.sqrt(sumI[0]/nSamples)
    rmsA1 = math.sqrt(sumI[1]/nSamples)
    rmsA2 = math.sqrt(sumI[2]/nSamples)
    return [rmsA0,rmsA1,rmsA2]


def consumerAI(qAI):
    #print "CONSUMER_AI..."
    # Template for DB
    template = [{"sensor_id": 1, "samples": []}, {"sensor_id": 2, "samples": []}, {"sensor_id": 3, "samples": []}]
    dFB = copy.deepcopy(template)
    while(True):
        if not qAI.empty():
            tempCons = qAI.get()
            ai = tempCons[0]
            date = tempCons[1]
            #print "Consumed queue"
            Irms = RMS(ai[1:])
            # Adding analog reads, sID and Date to lists for db upload
            dFB[0].get("samples").append({"RMS": Irms[0], "date_time": date[0]})
            dFB[1].get("samples").append({"RMS": Irms[1], "date_time": date[1]})
            dFB[2].get("samples").append({"RMS": Irms[2], "date_time": date[2]})
            # Queue is done processing the element
            qAI.task_done()
            #print "Inserted..."
            #print "dFB-1:", len(dFB[1]["samples"])
            #print "TEMPLATE: ", template
            if(len(dFB[1]["samples"])==10):
                try:
                    f.push(dFB)
                    dFB[:]=[]
                    dFB = None
                    dFB = copy.deepcopy(template)
            #        print "Done writing to FB-DB"
                    #print "dFB: ", dFB
            #        print datetime.now()
                except Exception as e:
                    logging.exception("message")


# Reading if there is any input for the relay
def relayAct(device, state):
    #print "Actuating relay"
    if state == "ON":
        GPIO.output(gpioDict[device],GPIO.LOW)
    else:
        GPIO.output(gpioDict[device],GPIO.HIGH)

# Appliances ID:
# id:1 ; Powerwall_1
# id:2 ; Powerwall_2
# id:3 ; Range_1
# id:4 ; Range_2
# id:5 ; AC_1
# id:6 ; AC_2
def relayTh():
    app_OrigStates = ["OFF","OFF","OFF","OFF","OFF","OFF"]
    while(True):
        #print "relayTh"
        #td = time.time()
        #Powerwall_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/1")
        #status_PW1 = Powerwall_1.json()["status"]
        #Range_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/3")
        #status_RA1 = Range_1.json()["status"]
        AC_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/5")
        status_AC1 = AC_1.json()["status"]
        #Dryer_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/9")
        #status_DR1 = Dryer_1.json()["status"]
        #Refrigerator_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/10")
        #status_RF1 = Refrigerator_1.json()["status"]
        SE_1 = requests.get("http://pwrnet-158117.appspot.com/api/v1/device/12")
        status_SE1 = SE_1.json()["status"]
        #app_NewStatus = [status_PW1, status_RA1, status_AC1, status_DR1, status_RF1]
        app_NewStatus = ["OFF", "OFF", status_AC1, "OFF","OFF",status_SE1]
        for index,(first,second) in enumerate(zip(app_OrigStates,app_NewStatus)):
            if first!=second:
                #print "Appliance: ", applianceList[index]
                #print "Status: ", second
                relayAct(applianceList[index],second)
                app_OrigStates = copy.deepcopy(app_NewStatus)
                #print app_OrigStates
        #print "time: ", time.time()-td
        time.sleep(1)


def main():

    # Initializing variables for queue and threads
    BUFFER_SIZE = 7
    qAI = Queue(7)
    # Number of analog inputs -> Needs to be automated
    nAI = 3
    formatAI = [i*4 for i in range(nAI)]
    #formatAI = [0,4]
    # INITIALIZING THREADS
    producerAI_thread = Thread(target=producerAI,args=(formatAI,qAI))
    producerAI_thread.start()
    consumerAI_thread = Thread(target=consumerAI,args=(qAI,))
    consumerAI_thread.start()
    relay_thread = Thread(target=relayTh)
    relay_thread.start()


if __name__ == '__main__':
    main()
