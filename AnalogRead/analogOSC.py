import beaglebone_pru_adc as adc
import time

nSamples = 100
capture = adc.Capture()
capture.cap_delay = 100000

capture.oscilloscope_init(adc.OFF_VALUES, nSamples)
capture.start()
t0 = time.time()

#while not (capture.oscilloscope_is_complete()):
for _ in range(10):
    if capture.oscilloscope_is_complete():
        break
    time.sleep(0.1)

capture.stop()
print "Acq. time: ", time.time()-t0
capture.wait()

print "Saving data..."

with open('data.csv', 'w') as f:
    for x in capture.oscilloscope_data(nSamples):
        f.write("%s %s", str(x), str(x))
        #f.write(str(x) + '\n')

print 'done'

capture.close()
