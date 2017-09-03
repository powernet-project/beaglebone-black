import beaglebone_pru_adc as adc
import Adafruit_BBIO.GPIO as GPIO
from firebase import Firebase as fb
from datetime import datetime
import math
import time

# Global variables:
nSamples = 100
convertion = 1.8/4095.0

# Initializing GPIOs:
gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.LOW)

# Initializing Firebase
f = fb('https://fb-powernet.firebaseio.com/sensor_data/')




# Average fcn time to get 100 samples with 1kHz (delay = 100000)=0.29sec
def analogRead(off_value):
    capture = adc.Capture()
    capture.cap_delay = 50000
    capture.oscilloscope_init(adc.OFF_VALUES+off_value, nSamples)
    capture.start()

    #for _ in range(20):
    #    if capture.oscilloscope_is_complete():
    #        break
    #    time.sleep(0.01)

    while not (capture.oscilloscope_is_complete()):
        # This is a dumb condition just to keep the loop running
        False

    capture.stop()
    capture.wait()
    capture.close()
    return capture.oscilloscope_data(nSamples)

# Reading if there is any input for the relay
def relayAct(device, state):
    if state == "ON":
        GPIO.output(gpioDict[device],GPIO.HIGH)
    else:
        GPIO.output(gpioDict[device],GPIO.LOW)

# Current RMS calculation
def RMS(data):
    # The size of sumI is the size of the AIN ports
    sumI = [0,0]
    for val in data:
        sumI[0]+=math.pow(val[0],2)
        sumI[1]+=math.pow(val[1],2)

    rmsA0 = convertion * math.sqrt(sumI[0]/nSamples)
    rmsA1 = convertion * math.sqrt(sumI[1]/nSamples)
    return [rmsA0,rmsA1]


####################### MAIN ########################

def main():
    # Initializing local variables:
    td = time.time()
    state = "OFF"
    device = "Lights"
    Vrms = 120


    #with open('data1.txt','w') as fw:
    #    for i in ai:
    #        fw.write('%s\t %s\n' % (str(i[0]),str(i[1])))

    # Testing GPIO
    while 1:
        if time.time()-td > 5:
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

            # Reading analog inputs should be in its own thread - here just for Testing
            ts0 = datetime.now()
            ai0 = analogRead(0)
            ts1 = datetime.now()
            ai1 = analogRead(4)
            ai = zip(ai0,ai1)
            # Computing RMS - first values of ai are always 0 -> remove
            Irms = RMS(ai[1:])
            Power = [i * Vrms for i in Irms]

            print "Firebase write..."
            ##### Writing to firebase
            f.push({'sensor_id': 0, 'date_time': str(ts0), 'value': '%1.2f' % Irms[0]})
            f.push({'sensor_id': 1, 'date_time': str(ts1), 'value': '%1.2f' % Irms[1]})
            print "Done writing to FB-DB"



if __name__ == '__main__':
  main()
