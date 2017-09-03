import beaglebone_pru_adc as adc
import Adafruit_BBIO.GPIO as GPIO
import time

# Global variables:
nSamples = 100

# Initializing GPIOs:
gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.LOW)


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

####################### MAIN ########################

def main():
    # Initializing local variables:
    td = time.time()
    state = "OFF"
    device = "Lights"

    ai0 = analogRead(0)
    ai1 = analogRead(4)
    ai = zip(ai0,ai1)
    with open('data1.txt','w') as f:
        for i in ai:
            f.write('%s\t %s\n' % (str(i[0]),str(i[1])))

    # Testing GPIO
    while 1:
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


if __name__ == '__main__':
  main()
