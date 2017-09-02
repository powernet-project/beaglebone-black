import beaglebone_pru_adc as adc
import time

# Global variables:
nSamples = 100

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

def main():

    ai0 = analogRead(0)
    ai1 = analogRead(4)
    ai = zip(ai0,ai1)
    with open('data1.txt','w') as f:
        for i in ai:
            f.write('%s\t %s\n' % (str(i[0]),str(i[1])))

    #t0 = time.time()
    #ai0 = analogRead(0)
    #t1 = time.time()
    #ai1 = analogRead(4)
    #t2 = time.time()

    #print "t0, t1: ", t1-t0, t2-t1
    #print "####################"
    #print ai0
    #print "####################"
    #print ai1


if __name__ == '__main__':
  main()
