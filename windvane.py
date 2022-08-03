import time, signal, sys
from math import sin
from math import cos
from math import radians
from math import degrees
from math import atan2
from math import sqrt
from math import asin

import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import numpy as np
import datetime
import psycopg2

import secrets

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

valuesx = np.array([])
valuesy = np.array([])


insert = 0
now=datetime.datetime.now()

while True:
	try:
		while now.minute%10 != 0 or insert == 1:
			time.sleep(10)
			volts = chan.voltage
			print(volts)
			angle = 80.71*volts**2.0-525.25*volts+848.89
			xcomp = sin(radians(angle))
			ycomp = cos(radians(angle))
			valuesx = np.append(valuesx,xcomp)
			valuesy = np.append(valuesy,ycomp)
			now=datetime.datetime.now()
			if insert == 1 and now.minute%10 != 0:
				insert = 0
		heading = (270-degrees(atan2(np.mean(-1.0*valuesy),-1.0*np.mean(valuesx))))%360
		e = sqrt(1-(np.mean(valuesx)**2+np.mean(valuesy)**2))
		sigmatheta = asin(e)*(1+(2/sqrt(3)-1)*e**3)
		con = psycopg2.connect(host=secrets.host, database=secrets.database, user=secrets.user, password=secrets.password)
		cur = con.cursor()
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 12, %s)' % (heading))
		cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 13, %s)' % (degrees(sigmatheta)))
		con.commit()
		con.close()
		valuesx = np.array([])
		valuesy = np.array([])
		insert = 1
		now=datetime.datetime.now()
	except KeyboardInterrupt:
		con.close()
		raise


con.close()
