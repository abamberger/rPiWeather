import Adafruit_BMP.BMP085 as BMP085
from smbus import SMBus
import time
import psycopg2
import datetime
import numpy as np

import secrets

time.sleep(1)

tempparr = np.array([])
pressurearr = np.array([])
tempharr = np.array([])
humidarr = np.array([])

bmp = BMP085.BMP085(busnum = 1)

HIH6130 = SMBus(1)
var = [0, 0, 0, 0]

insert = 0 #change to zero
now=datetime.datetime.now()

while True:
	try:
		while now.minute%10 != 0 or insert == 1:
			time.sleep(30)
			#BMP180 Read
			tempp = bmp.read_temperature()
			pressure = bmp.read_pressure()/100.00
			#HIH6130 Read
			HIH6130.write_quick(0x27)
			time.sleep(0.050)
			var = HIH6130.read_i2c_block_data(0x27, 0)
			status = (var[0] & 0xc0) >> 6
			humidity = (((var[0] & 0x3f) << 8) + var[1]) * 100.0 / 16383.0
			temph = ((var[2] << 6) + ((var[3] & 0xfc) >> 2)) * 165.0 / 16383.0 - 40.0
			#print(tempp)
			print(temph)
			print(humidity)
			print(tempp)
			print(pressure)
			#Store in arrays
			if tempp < 50:
				tempparr = np.append(tempparr,tempp)
			if pressure > 700 and pressure < 900:
				pressurearr = np.append(pressurearr,pressure)
			if temph < 50:
				tempharr = np.append(tempharr, temph)
			if humidity > -1 and humidity < 101:
				humidarr = np.append(humidarr,humidity)
			now=datetime.datetime.now()
			if insert == 1 and now.minute%10 != 0:
				insert = 0
			#print tempparr
			#print tempharr
			#print humidarr
			#print pressurearr
		#calculate means of 30sec arrays
		temppi = np.mean(tempparr)
		temphi = np.mean(tempharr)
		humidi = np.mean(humidarr)
		pressurei = np.mean(pressurearr)
		dpti = 243.04*(np.log(humidi/100.0)+((17.625*temppi)/(243.04+temppi)))/(17.625-np.log(humidi/100.0)-((17.625*temppi)/(243.04+temppi)))
		slpi = pressurei*np.exp(1637.0/(29.3*(temppi+273)))
		#insert into db
		con = psycopg2.connect(host=secrets.host, database=secrets.database, user=secrets.user, password=secrets.password)
		cur = con.cursor()
		if len(tempparr) > 0:
			cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 1, %s)' % (temppi))
		if len(tempharr) > 0:
			cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 2, %s)' % (temphi))
		if len(humidarr) > 0:
			cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 7, %s)' % (humidi))
		if len(pressurearr) > 0:
			cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 8, %s)' % (pressurei))
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 9, %s)' % (round(dpti,4)))
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 10, %s)' % (round(slpi,4)))
		con.commit()
		con.close()
		#Clear 30 second arrays for next cycle
		tempparr = np.array([])
		pressurearr = np.array([])
		tempharr = np.array([])
		humidarr = np.array([])
		insert = 1
		now = datetime.datetime.now()
	except KeyboardInterrupt:
		con.close()
		raise



