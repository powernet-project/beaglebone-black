# Creating a sqlite database
import sqlite3
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

# Creating a new SQLite table with 1 column
c.execute('CREATE TABLE IF NOT EXISTS {tn} (id INTEGER PRIMARY KEY,\
    name TEXT)'.format(tn=tb_SensorList))
c.execute('INSERT INTO {tn} VALUES (1,"Sensor1")'.format(tn=tb_SensorList))
c.execute('INSERT INTO {tn} VALUES (2,"Sensor2")'.format(tn=tb_SensorList))
c.execute('INSERT INTO {tn} VALUES (3,"Sensor3")'.format(tn=tb_SensorList))
c.execute('INSERT INTO {tn} VALUES (4,"Sensor4")'.format(tn=tb_SensorList))
conn.commit()

c.execute('CREATE TABLE IF NOT EXISTS {tn} (\
    sensor_id INTEGER  NOT NULL,\
    time_stamp DATETIME NOT NULL,\
    value REAL,\
    FOREIGN KEY (sensor_id) REFERENCES Sensor_List(id))'.format(tn=tb_AnalogReads))

# c.execute('CREATE INDEX sensor_index ON {tn} (sensor_id)'.format(tn=tb_AnalogReads))

# Committing changes and closing the connection to the database file
conn.commit()
conn.close()

# Checking database:
#sqlite3
#.open 'path/filename'
