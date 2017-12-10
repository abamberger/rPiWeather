import time, signal, sys
from math import sin
from math import cos
from math import radians
from math import degrees
from math import atan2
from math import sqrt
from math import asin
from Adafruit_ADS1x15 import ADS1x15
import numpy as np
import datetime
import psycopg2

ADS1015 = 0x00  # 12-bit ADC

# Select the gain
# gain = 61    # +/- 6.144V
gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
# gain = 1024  # +/- 1.024V
# gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
# sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

# Initialise the ADC using the default mode (use default I2C address)
# Set this to ADS1015 or ADS1115 depending on the ADC you are using!
adc = ADS1x15(ic=ADS1015)

valuesx = np.array([])
valuesy = np.array([])

#con = psycopg2.connect(database='weather', user='alex')
#cur = con.cursor()

insert = 0
now=datetime.datetime.now()

while True:
	try:
		while now.minute%10 <> 0 or insert == 1:
			time.sleep(10)
			volts = adc.readADCSingleEnded(0, gain, sps) / 1000
			angle = 80.71*volts**2.0-525.25*volts+848.89
			xcomp = sin(radians(angle))
			ycomp = cos(radians(angle))
			print volts
			valuesx = np.append(valuesx,xcomp)
			valuesy = np.append(valuesy,ycomp)
			now=datetime.datetime.now()
			if insert == 1 and now.minute%10 <> 0:
				insert = 0
		heading = (270-degrees(atan2(np.mean(-1.0*valuesy),-1.0*np.mean(valuesx))))%360
		e = sqrt(1-(np.mean(valuesx)**2+np.mean(valuesy)**2))
		sigmatheta = asin(e)*(1+(2/sqrt(3)-1)*e**3)
		con = psycopg2.connect(host='10.0.0.247', database='weather', user='met', password='metp@ss')
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
