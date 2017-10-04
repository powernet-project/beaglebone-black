import beaglebone_pru_adc as adc
import time
import Adafruit_BBIO.GPIO as GPIO

gpioDict = {"Lights": "P8_10", "Fan": "P8_14"}
for key in gpioDict:
    GPIO.setup(gpioDict[key], GPIO.OUT)
    GPIO.output(gpioDict[key], GPIO.HIGH)

while(True):
    dev_name = raw_input('Device name: ')
    dev_state = raw_input('Device state: ')
    if dev_state == "ON":
        GPIO.output(gpioDict[dev_name],GPIO.LOW)
    else:
        GPIO.output(gpioDict[dev_name],GPIO.HIGH)

    acq = raw_input('Acquire and save data in csv format?')
    if(acq == 'YES'):
        numsamples = 10000 # how many samples to capture

        capture = adc.Capture()
        capture.cap_delay = 50000

        capture.oscilloscope_init(adc.OFF_VALUES, numsamples) # captures AIN0 - the first elt in AIN array
        #capture.oscilloscope_init(adc.OFF_VALUES+8, numsamples) # captures AIN2 - the third elt in AIN array
        capture.start()

        for _ in range(10):
            if capture.oscilloscope_is_complete():
                break
            print '.'
            time.sleep(0.1)

        capture.stop()
        capture.wait()

        print 'Saving oscilloscope values to "data.csv"'

        with open('data.csv', 'w') as f:
            for x in capture.oscilloscope_data(numsamples):
                f.write(str(x) + '\n')

        print 'done'

        capture.close()
