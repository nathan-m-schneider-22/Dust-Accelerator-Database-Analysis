import mysql.connector
#SQLTest.py retrieives the database information through mysql connector
#It then processes the results (see function comments for explanation)

def main():
    

mydb = mysql.connector.connect(host="localhost", user="root",passwd="dust",database="ccldas_production")

cursor = mydb.cursor()

cursor.execute("select integer_timestamp, velocity_max, \
velocity_min from psu order by integer_timestamp ASC")
speeds = cursor.fetchall()

print(len(speeds))


cursor.execute("SELECT * FROM ccldas_production.source_settings\
 WHERE !(frequency=0 OR needle_voltage=0 OR einzel_voltage=0 OR amplitude=0)")
starts = cursor.fetchall()

print(len(starts))

cursor.execute("SELECT * FROM ccldas_production.source_settings\
 WHERE (frequency=0 OR needle_voltage=0 OR einzel_voltage=0 OR amplitude=0)")
stops = cursor.fetchall()



print(len(stops))


main()
