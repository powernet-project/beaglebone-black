# Creating a sqlite database
import sqlite3
import time
#sqlite_file = "/root/Programs/Python-Code/Databases/analogIn_test.sqlite"
sqlite_file = "/Users/gcezar/Documents/BBB/analogIn_test.sqlite"
tb_AnalogReads = "AnalogReads" # Table name
tb_SensorList = "Sensor_List"

tb_SwitchStates = "Switch"
column1_SwitchStates = "GPIO68"

# Connecting to the database
# It wont create a table
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

n=1000
aIn = [240]*n
ts = ["12/13/14"]*n
sId = [3]*n
l = zip(aIn,ts,sId)
t0 = time.time()
i=0
while (i<len(aIn)):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    c.execute('INSERT INTO "AnalogReads" VALUES (?,?,?)',l[i])
    #c.execute('INSERT INTO {tn} VALUES (1,"12/12/12",200)'.format(tn=tb_AnalogReads))
    i+=1
    conn.commit()
    conn.close()


t1 = time.time()-t0
print "Time OPEN/CLOSE every time: ", t1

t0 = time.time()
i=0

conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
while (i<len(aIn)):
    c.execute('INSERT INTO "AnalogReads" VALUES (?,?,?)',l[i])
    #c.execute('INSERT INTO {tn} VALUES (1,"12/12/12",200)'.format(tn=tb_AnalogReads))
    i+=1
conn.commit()
conn.close()
t1 = time.time()-t0
print "Time OPEN/CLOSE once: ", t1


# Checking database:
#sqlite3
#.open 'path/filename'
