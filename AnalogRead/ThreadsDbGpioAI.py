# Based of:
# https://www.troyfawkes.com/learn-python-multithreading-queues-basics/

import beaglebone_pru_adc as adc
import Adafruit_BBIO.GPIO as GPIO
import math
from Queue import Queue
from threading import Thread
from datetime import datetime
from firebase import Firebase as fb

# Global variables
nSamples = 100
convertion = 1.8/4095.0

# Initializing Firebase
f = fb('https://fb-powernet.firebaseio.com/sensor_data/')


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
    print "PRODUCER_AI..."
    dts = []    # date/time stamp for each start of analog read
    dts.append(str(datetime.now()))
    ai0 = analogRead(formatAI[0])
    dts.append(str(datetime.now()))
    ai1 = analogRead(formatAI[1])
    qAI.put(zip(ai0,ai1))
    qAI.put(dts)
    print "Datetime: ", dts
    #qAI.join()


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
    print "CONSUMER_AI..."
    while(True):
        ai = qAI.get()
        date = qAI.get()
        if(qAI.empty()):
            qAI.task_done()
            print "Consumed queue"
        else: print "Queue not empty"
        Irms = RMS(ai[1:])
        print "Firebase write..."
        ##### Writing to firebase
        f.push({'sensor_id': 0, 'date_time': str(date[0]), 'value': '%1.2f' % Irms[0]})
        f.push({'sensor_id': 1, 'date_time': str(date[1]), 'value': '%1.2f' % Irms[1]})
        print "Done writing to FB-DB"



def main():

    # Initializing variables for queue and threads
    qAI = Queue(maxsize=0)
    #qDate = Queue(maxsize=0)
    nThreads = 3
    nAI = 2
    #formatAI = [i*4 for i in range(nAI)]
    formatAI = [0,4]

    # INITIALIZING THREADS
    producerAI_thread = Thread(target=producerAI,args=(formatAI,qAI))
    #producerAI_thread.setDeamon(True)
    producerAI_thread.start()
    consumerAI_thread = Thread(target=consumerAI,args=(qAI,))
    #consumerAI_thread.setDeamon(True)
    consumerAI_thread.start()

if __name__ == '__main__':
    main()
