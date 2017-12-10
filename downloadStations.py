#f = open('/home/alex/weather/extStation/extStation.log','w')
import string
import urllib
from datetime import datetime, timedelta
from metar import Metar
from math import exp
from math import pow
import psycopg2
#from __future__ import print_function

con = psycopg2.connect(database='weather', user='alex')
cur = con.cursor()

BASE_URL = "http://weather.noaa.gov/pub/data/observations/metar/stations"

stations = [
            'KDEN'      #DIA
          , 'KBJC'      #Broomfield Airport
          , 'KLIC'      #Limon
          , 'KLAA'      #Lamar
          , 'KVTP'      #La Veta Pass
          , 'KCOS'      #Colorado Springs
          , 'K4BM'      #Wilkerson Pass
          , 'K0CO'      #Berthoud Pass
          #, 'KGNB'      Granby
          , 'KSBS'      #Steamboat Springs
          , 'K3MW'      #Mt werner above steamboat
          , 'KLXV'      #Leadville
          , 'KANK'      #Salida
          , 'KMYP'      #Monarch Pass
          , 'KASE'      #Aspen
          , 'KGUC'      #Gunnison
          , 'K5SM'      #Sunlight above glenwood
          , 'KGJT'      #Grand Junction
          , 'KTEX'      #Telluride
          , 'KDRO'      #Durango
          , 'KCNY'      #Moab
          , 'KPUB'      #Pueblo
          , 'KSPD'      #Springfield
          , 'KTAD'      #Trinidad
          , 'KALS'      #Alimosa
          , 'K04V'      #Saguache
          , 'KCPW'      #Wolf Creek Pass
          , 'KPSO'      #Pagosa Springs
          , 'KFMM'      #Fort Morgan
          , 'KITR'      #Burlington
          , 'KHEQ'      #Holyoke
          , 'KFNL'      #Fort Collins
          , 'KCYS'      #Cheyenne
          , 'K20V'      #Kremmling
          , 'K33V'      #Walden
          , 'KCAG'      #Craig
          , 'KEEO'      #Meeker
          , 'KCEZ'      #Cortez
          , 'KMTJ'      #Montrose
          , 'KAJZ'      #Delta
          , 'KAIB'      #Hopkins
          , 'K4BL'      #Blanding
          , 'KVEL'      #Vernal
          , 'KU28'      #Green River
          , 'K4HV'      #Hanksville
          , 'KPUC'      #Price
          , 'K36U'      #Heber
          , 'KSLC'      #Salt Lake City
          ]

def RH(temp, dewpt):
  relHum = 100 * (exp((17.625*dewpt)/(243.04+dewpt))/exp((17.625*temp)/(243.04+temp)))
  return relHum

def windDir(dirStr):
  degrees = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5]
  degreesStr = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
  for i in xrange(0,15):
    if dirStr == degreesStr[i]:
      break
  return degrees[i]

def roundHour(datatime):
  epoch = datetime.utcfromtimestamp(0)
  delta = datatime - epoch
  datatimehr = epoch + timedelta(hours=round(delta.total_seconds()/3600,0))
  return datatimehr

def selectStationid(icao):
  cur.execute('select stationid from stationlocations where icao = \'%s\'' % (icao))
  rows = cur.fetchall()
  stationid =  rows[0][0]
  return stationid

def sqlCheck(name):
  cur.execute("""
          select exists (
        select * from stationsensors
        where stationid = (
        select stationid from stationlocations where icao = \'%s\'
        )
        ) """ % (name))
  rows = cur.fetchall()
  exists = rows[0][0]
  if not exists:
    stationid = selectStationid(name)
    cur.execute("""
        insert into stationsensors
        (stationid, description, units)
        values
        ({0}, 'tmp2m', 'C')
        ,({0}, 'dpt2m', 'C')
        ,({0}, 'rh2m', '%')
        ,({0}, 'wnd10mdir', 'deg')
        ,({0}, 'wnd10m', 'm/s')
        ,({0}, 'gustsfc', 'm/s')
        ,({0}, 'presmsl', 'mbar')
        ,({0}, 'apcpsfc', 'mm')
        ,({0}, 'irrsfc', 'W/m^2')
        ,({0}, 'tcdcclm', '%')
        """.format(stationid))
    con.commit()
    return 'false'
  else:
    return 'true'

def sensorid(stationid, field):
  cur.execute("""
          select sensorid
          from stationsensors
          where stationid = %s
          and description = \'%s\' """ % (stationid, field))
  rows = cur.fetchall()
  return rows[0][0]

def checkInsert(stationid, datatime):
  cur.execute("""
              select exists (
              select *
              from stationdata sd
              inner join stationsensors ss
              on sd.sensorid = ss.sensorid
              where ss.stationid = %s
              and sd.datatime = \'%s\'
              )""" % (stationid, datatime))
  rows = cur.fetchall()
  exists = rows[0][0]
  return exists

fail = 0


for name in stations:
  url = "%s/%s.TXT" % (BASE_URL, name)
  try:
    urlh = urllib.urlopen(url)
    report = ''
    for line in urlh:
      if line.startswith(name):
        exists = sqlCheck(name)
        #print exists
        report = line.strip()
        obs = Metar.Metar(line)
        datatime = roundHour(datetime.strptime(obs.time.ctime(), "%a %b %d %H:%M:%S %Y"))
        stationid =  selectStationid(name)
        #print stationid
        print name
        datatimesql = datetime.strftime(datatime, "%Y-%m-%d %H:%M:%S")
        #f.write(obs.string())
        if not checkInsert(stationid, datatimesql):
          if obs.temp:
            print "temperature: %s" % obs.temp.value()
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'tmp2m'), obs.temp.value()))
          if obs.dewpt:
            print "dew point: %s" % obs.dewpt.value()
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'dpt2m'), obs.dewpt.value()))
          if obs.temp and obs.dewpt:
            print "relative humidty: %s" % RH(obs.temp.value(), obs.dewpt.value())
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'rh2m'), RH(obs.temp.value(), obs.dewpt.value())))
          if obs.wind_speed:
            windArr = obs.wind().split()
            print windArr
            if windArr[0] == "calm":
              print "wind direction: %s" % "NULL"
              print "wind speed: %s" % 0
              cur.execute('insert into stationdata values (\'%s\', %s, NULL)' % (datatimesql, sensorid(stationid, 'wnd10mdir')))
              cur.execute('insert into stationdata values (\'%s\', %s, 0)' % (datatimesql, sensorid(stationid, 'wnd10m')))
            else:
              i = 0
              if windArr[1] == 'to':
                i = 2
              print "wind direction: %s" % windDir(windArr[0])
              print "wind speed: %s" % (float(windArr[2+i])*0.51444)
              cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'wnd10mdir'), windDir(windArr[0])))
              cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'wnd10m'), (float(windArr[2+i])*0.51444)))
              if len(windArr) > (4+i) and windArr[4+i] == "gusting":
                print "wind gust: %s" % (float(windArr[6+i])*0.51444)
                cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'gustsfc'), (float(windArr[6+i])*0.51444)))
          if obs.press:
            print "pressure: %s" % (obs.press.value()*33.8638)
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'presmsl'), (obs.press.value()*33.8638)))
          if obs.precip_1hr:
            print "precipitation: %s" % obs.precip_1hr.value()
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'apcpsfc'), (obs.precip_1hr.value()*25.4)))
          else:
            print "precipitation: 0"
            cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'apcpsfc'), 0))
          skyCover = pow((1-0.11875), obs.code.count('FEW')) * pow((1-0.4375), obs.code.count('SCT')) * pow((1-0.750), obs.code.count('BKN')) * pow((1-1), obs.code.count('OVC'))
          skyCover = round(min(1-skyCover, 1)*100.0,0)
          print "sky cover: %s" % (skyCover)
          cur.execute('insert into stationdata values (\'%s\', %s, %s)' % (datatimesql, sensorid(stationid, 'tcdcclm'), (skyCover)))
          print ''
          con.commit()
          break
    if not report:
      print "No data for ",name,"\n\n"
  except Metar.ParserError, err:
    print "METAR code: ",line
    print string.join(err.args,", "),"\n"
  except:
    fail = fail +1
    print "Error retrieving",name,"data","\n"

print "Failures: ",fail

con.close()
