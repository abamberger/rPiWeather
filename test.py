import psycopg2

con = psycopg2.connect(host='10.0.0.249', database='weather', user='met', password='metp@ss')
cur = con.cursor()

cur.execute('insert into stationdata values (\'2014-08-15 15:00:00\', 1, 10)')

con.commit()

print rows