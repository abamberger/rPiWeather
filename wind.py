import time
import pigpio
import numpy as np
import datetime
import psycopg2

import secrets

WIND_GPIO=4
pi = pigpio.pi()
pi.set_mode(WIND_GPIO, pigpio.INPUT)
pi.set_pull_up_down(WIND_GPIO, pigpio.PUD_UP)
wind_cb = pi.callback(WIND_GPIO, pigpio.FALLING_EDGE)
old_count=0
values = np.array([])

#con = psycopg2.connect(database='weather', user='alex')
#cur = con.cursor()

insert = 0
now=datetime.datetime.now()

while True:
   try:
      while now.minute%10 != 0 or insert == 1:
         time.sleep(3)
         count = wind_cb.tally()
         speed = ((count-old_count)/3)*0.05103+0.14727
         values = np.append(values,speed)
         old_count = count
         now=datetime.datetime.now()
         if insert == 1 and now.minute%10 != 0:
            insert = 0
      con = psycopg2.connect(host=secrets.host, database=secrets.database, user=secrets.user, password=secrets.password)
      cur = con.cursor()
      cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 3, %s)' % (np.mean(values)))
      cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 4, %s)' % (np.std(values)))
      cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 5, %s)' % (max(values)))
      cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 6, %s)' % (min(values)))
      con.commit()
      con.close()
      values = np.array([])
      insert = 1
      now=datetime.datetime.now()
   except KeyboardInterrupt:
      pi.stop()
      con.close()
      raise

pigpio.stop()
con.close()
