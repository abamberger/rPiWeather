import time
import pigpio
import datetime
import psycopg2

#con = psycopg2.connect(database='weather', user='alex')
#cur = con.cursor()

RAIN_GPIO=18
pi = pigpio.pi()
pi.set_mode(RAIN_GPIO, pigpio.INPUT)
pi.set_pull_up_down(RAIN_GPIO, pigpio.PUD_UP)

count = 0
old_count = 0
last_t = datetime.datetime.now()

def cbf(g, L, t):
   global last_t
   global count
   if (datetime.datetime.now()-last_t).total_seconds() > 10:
      count = count + 1
   last_t = datetime.datetime.now()

insert = 0
now=datetime.datetime.now()
cb = pi.callback(RAIN_GPIO, pigpio.FALLING_EDGE, cbf)

while True:
   try:
      while now.minute%10.0 <> 0 or insert == 1:
         time.sleep(30)
         now=datetime.datetime.now()
         if insert == 1 and now.minute%10.0 <> 0:
            insert = 0
      con = psycopg2.connect(host='10.0.0.247', database='weather', user='met', password='metp@ss')
      cur = con.cursor()
      cur.execute('insert into stationdata values (round_10min(now_utc() + interval \'1 second\'), 11, %s)' % ((count-old_count)*0.79719))
      con.commit()
      con.close()
      old_count = count
      insert = 1
      now=datetime.datetime.now()
   except KeyboardInterrupt:
      raise
