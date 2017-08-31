#!/usr/bin/python

# emon logger
# elha 20141220
# version 1.0
#
# inspired by OpenEnergyMonitor.org

import math
import time
#import requests
import Queue
import threading
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
import sqlite3
from firebase import Firebase as fb



# Initializing ADC
ADC.setup()

# Initializing GPIOs
gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.LOW)


# const
NUMBER_OF_SAMPLES = 60         # take 850 Samples per Measurement (takes approx 1.2 secs)
ICAL = 1000 / 33                # CT 1000:1 / Burden 33 Ohms
VOLT_NORM = 1.8                 # Adafruit voltage "denormalization" - when using read
VOLT_PER_TICK = 1.8 / 4096      # VDC BBB / 12 bit ADC Resolution
VOLT_AC_RMS = 230               # fixed value
# INTERVAL = 60                   # measure every 60 secs
INTERVAL = 2                    # measure every 5 seconds

# globals
buffer = [0 for i in range(NUMBER_OF_SAMPLES)]
logfile = "/var/log/AnalogRead.log"
# pins = ["0", "1", "2", "3", "4", "5", "6"]
# pins = ["P9_33"]
pins = ["4"]
paramts = "&time="
paramcsv = "&csv="

# Initializing Firebase
f = fb('https://fb-powernet.firebaseio.com/sensor_data/')


# read ADC
def Read(pin):
        pinfile = "/sys/bus/iio/devices/iio:device0/in_voltage" + pin + "_raw"
        with open(pinfile, "r") as analog:
                #print "Analog Read: "
                #print int(analog.readline())
                return int(analog.readline())
        #return ADC.read(pin)


# Calculating mean
def Mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)


# calc RMS power for single pin
def CalcPower(pin):
        a = 0
        # sampling
        #t0 = time.time()
        while a < NUMBER_OF_SAMPLES:
                #t0 = time.time()
                buffer[a] = Read(pin)
                #d = time.time()-t0
                #print "Acquisition time: "
                #print d
                #time.sleep(0.001)
                a += 1
        #d = time.time()-t0
        #print "Acquisition time: "
        #print d
        # Converting current to Amps
        # buffer = VOLT_NORM*ICAL*buffer

        # Mean
        #avg = Mean(buffer)
        #print "avg: "
        #print avg
        sort = sorted(buffer)
        median = sort[NUMBER_OF_SAMPLES/2]

        # calc RMS (sum squares -> average ->  squareroot)
        sumI = 0.0
        a = 0
        while a < NUMBER_OF_SAMPLES:
                sumI += math.pow(buffer[a], 2)
                a += 1

        print "SumI: ", sumI
        print "Current: "
        print VOLT_PER_TICK * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        return VOLT_PER_TICK * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        #return VOLT_AC_RMS * ICAL * VOLT_PER_TICK * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        #print "Power: "
        #print VOLT_AC_RMS * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        #return VOLT_AC_RMS * math.sqrt(sumI / NUMBER_OF_SAMPLES)


# calc power for each pin and return csv-data
def Calc():
        out = ""
        for pin in pins:
                out += "%1.1f," % CalcPower(pin)
        #print "OUT: "
        #print out
        return out[:-1]


# log to logfile
def log(msg):
        with open(logfile, "a") as f:
                f.write(msg + '\n')


def databaseInit():
    # Creating database object
    sqlite_file = "/root/Programs/Python-Code/Databases/analogIn_test.sqlite"
    return sqlite3.connect(sqlite_file)

# Reading if there is any input for the relay
def relayAct(device, state):
    if state == "ON":
        GPIO.output(gpioDict[device],GPIO.HIGH)
    else:
        GPIO.output(gpioDict[device],GPIO.LOW)

# main, init
def main():
        print("Starting...")

        log("-----------------------------------------------")
        log("start %10d" % int(time.time()))

        ##### Initializing database
        conn = databaseInit()
        #conn = sqlite3.connect("/root/Programs/Python-Code/Databases/analogIn_test.sqlite")
        c = conn.cursor()
        # Initialization of relay variables
        td = time.time()
        state = "OFF"
        device = "Lights"

        #backlog = Queue.Queue()

        #sender = threading.Thread(target=sendworker)
        #sender.daemon = True
        #sender.start()

        # main, run loop
        #try:
            #ts = time.time()
            #state = "OFF"
        while 1:
                ##### wait until next query
                time.sleep(INTERVAL - (int(time.time()) % INTERVAL))

                ##### query data
                val = Calc()
                ts = "%10d" % int(time.time())
                sID = int(pins[0])

                # Reading if there are new inputs in the web for the relays:
                # Check for new data data every second
                # web server function
                #print "Starting relay"
                # Check to see if clock has set back
                if td > time.time():
                    td = time.time()
                #print "Passed Clock check"
                if time.time()-td > 1:
                    # function to read server and check for updates
                    # Reading the update

                    # fake function
                    if state == "OFF":
                        state = "ON"
                    else:
                        state = "OFF"
                    print "Device and State: ",device, state
                    relayAct(device, state)
                    td = time.time()
                    #print "Relay actuated"
                ##### Writing to database
                #print "Before DB insert"
                #c.execute('INSERT INTO AnalogReads VALUES (?,?,?);',\
                #(sID,ts,val))
                #conn.commit()

                #print "Firebase write..."
                ##### Writing to firebase
                #f.push({'sensor_id': sID, 'time_stamp': ts, 'value':val})

                #print 'Done!'


                # report in backlog
                # backlog.put(url + paramts + ts + paramcsv + csv)

                # log to logfile (if something goes wrong)
                # log(ts + ',' + val)
        #except:
        #    #conn.close()
        #    print "shutdown..."

if __name__ == '__main__':
  main()
