#!/usr/bin/python

# emon logger
# elha 20141220
# version 1.0
#
# inspired by OpenEnergyMonitor.org

import math
import time
import requests
import Queue
import threading
import Adafruit_BBIO.ADC as ADC
import sqlite3


# Initializing ADC
ADC.setup()

# const
NUMBER_OF_SAMPLES = 850         # take 850 Samples per Measurement (takes approx 1.2 secs)
ICAL = 1000 / 33                # CT 1000:1 / Burden 33 Ohms
VOLT_NORM = 1.8                 # Adafruit voltage "denormalization" - when using read
VOLT_PER_TICK = 1.8 / 4096      # VDC BBB / 12 bit ADC Resolution
VOLT_AC_RMS = 230               # fixed value
# INTERVAL = 60                   # measure every 60 secs
INTERVAL = 5                    # measure every 5 seconds

# globals
buffer = [0 for i in range(NUMBER_OF_SAMPLES)]
logfile = "/var/log/AnalogRead.log"
# pins = ["0", "1", "2", "3", "4", "5", "6"]
# pins = ["P9_33"]
pins = ["4"]
url = "http://emoncms.org/input/post.json?node=1&apikey=<EMONAPIKEY>"
paramts = "&time="
paramcsv = "&csv="


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
        while a < NUMBER_OF_SAMPLES:
                buffer[a] = Read(pin)
                a += 1

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

        #print "SumI"
        #print sumI
        #print "Current: "
        #print VOLT_PER_TICK * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        return VOLT_AC_RMS * ICAL * VOLT_PER_TICK * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        #print "Power: "
        #print VOLT_AC_RMS * math.sqrt(sumI / NUMBER_OF_SAMPLES)
        #return VOLT_AC_RMS * math.sqrt(sumI / NUMBER_OF_SAMPLES)


# calc power for each pin and return csv-data
def Calc():
        out = ""
        for pin in pins:
                out += "%1.1f," % CalcPower(pin)
        print "OUT: "
        print out
        return out[:-1]


# log to logfile
def log(msg):
        with open(logfile, "a") as f:
                f.write(msg + '\n')


# send to emoncms.org
def sendworker():
    item = ""
    while 1:
        if(item == ""):
                item = backlog.get()

        try:
                requests.get(item)
                backlog.task_done()
                item=""
        except:
                pass

        time.sleep(1)

def databaseInit():
    # Creating database object
    sqlite_file = "/root/Programs/Python-Code/Databases/analogIn_test.sqlite"
    return sqlite3.connect(sqlite_file)

# main, init
try:
        print("emon logger")
        print("logging to " + logfile)

        log("-----------------------------------------------")
        log("start %10d" % int(time.time()))

        # Initializing database
        conn = databaseInit()
        c = conn.cursor()


        backlog = Queue.Queue()

        sender = threading.Thread(target=sendworker)
        sender.daemon = True
        sender.start()

        # main, run loop
        while 1:
                # wait until next query
                time.sleep(INTERVAL - (int(time.time()) % INTERVAL))

                # query data
                csv = Calc()
                ts = "%10d" % int(time.time())
                sID = int(pins[0])

                # Writing to database
                c.execute('INSERT INTO AnalogReads (sensor_id, timestamp, value)'\
                VALUES (sID,ts,csv))
                conn.commit()


                # report in backlog
                # backlog.put(url + paramts + ts + paramcsv + csv)

                # log to logfile (if something goes wrong)
                log(ts + ',' + csv)

except:
        conn.close()
        print("shutdown.")