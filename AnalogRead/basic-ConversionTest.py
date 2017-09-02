import beaglebone_pru_adc as adc
import time

# Defining conversion constant
CONSTANT = 1.8/4095.0

# Starting method to capture data
capture = adc.Capture()
#capture.cap_delay = 10000

t0 = time.time()
capture.start()

# Just creates a list with the values from the pins

#while i<1000:
#    v_list = ["{0:.4f}".format(item * CONSTANT) for item in capture.values]
#    i+=1
v = []

for i in range(50):
    v.append((capture.timer,capture.values))
    #print "Timer, Values: ", v[i][0], v[i][1]

for i in v:
    print i


#v_list = ["{0:.4f}".format(item * CONSTANT) for item in capture.values]

#del v_list[7]
#print v_list
#print "TIME: ", time.time()-t0

# for _ in range(1000):
#    print capture.timer, capture.values

capture.stop() # ask driver to stop
capture.wait() # wait for graceful exit
capture.close()
