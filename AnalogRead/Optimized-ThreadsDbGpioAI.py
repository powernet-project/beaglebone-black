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

# Global variables
nSamples = 100
convertion = 1.8/4095.0

# Initializing GPIOs:
gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.LOW)


# Initializing Firebase
f = fb('https://fb-powernet.firebaseio.com/DayTest')
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
        #print "Putting AI Data..."
        tempAI = zip(ai0,ai1)
        tempQueue = [tempAI, dts]
        qAI.put(tempQueue)
        print "Queue done..."
        time.sleep(2)


# Current RMS calculation for consumerAI
def RMS(data):
    # The size of sumI is the size of the AIN ports
    sumI = [0,0]
    for val in data:
        sumI[0]+=math.pow(val[0],2)
        sumI[1]+=math.pow(val[1],2)

    rmsA0 = convertion * math.sqrt(sumI[0]/nSamples)
    rmsA1 = convertion * math.sqrt(sumI[1]/nSamples)
    return [rmsA0,rmsA1]


def consumerAI(qAI):
    #print "CONSUMER_AI..."
    # Template for DB
    template = [{"sensor_id": 1, "samples": []}, {"sensor_id": 2, "samples": []}]
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
            # Queue is done processing the element
            qAI.task_done()
            print "Inserted..."
            #print "dFB-1:", len(dFB[1]["samples"])
            #print "TEMPLATE: ", template
            if(len(dFB[1]["samples"])==10):
                f.push(dFB)
                dFB[:]=[]
                dFB = None
                dFB = copy.deepcopy(template)
                print "Done writing to FB-DB"
                #print "dFB: ", dFB
                print datetime.now()


# Reading if there is any input for the relay
def relayAct(device, state):
    print "Actuating relay"
    if state == "ON":
        GPIO.output(gpioDict[device],GPIO.HIGH)
    else:
        GPIO.output(gpioDict[device],GPIO.LOW)

# Dumb function to simulate interfacing web server looking for inputs
def relayTh():
    print "Starting relay thread..."
    state = "OFF"
    device = "Lights"
    while(True):
        if state == "OFF":
            state = "ON"
        else:
            state = "OFF"
        print "Device and State: ",device, state
        relayAct(device, state)
        td = time.time()
        time.sleep(5)

def main():

    # Initializing variables for queue and threads
    BUFFER_SIZE = 7
    qAI = Queue(7)
    nAI = 2
    #formatAI = [i*4 for i in range(nAI)]
    formatAI = [0,4]

    # INITIALIZING THREADS
    producerAI_thread = Thread(target=producerAI,args=(formatAI,qAI))
    producerAI_thread.start()
    consumerAI_thread = Thread(target=consumerAI,args=(qAI,))
    consumerAI_thread.start()
    relay_thread = Thread(target=relayTh)
    relay_thread.start()


if __name__ == '__main__':
    main()
