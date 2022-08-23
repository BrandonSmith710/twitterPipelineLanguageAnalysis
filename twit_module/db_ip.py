import psycopg2


def connect_pg(dbname, user, password, host):
	return psycopg2.connect(dbname = dbname, user = user,
		                    password = password, host = host)
def get_curs(conn):
	return conn.cursor()

def init_ip_table(curs, conn):
	curs.execute('''
			CREATE TABLE IF NOT EXISTS userip (
			ip VARCHAR(50) primary key
			);''')
	conn.commit()

def insert_ip(curs, conn, ip):
	query = 'INSERT INTO userip (ip) VALUES (%s);'
	curs.execute(query, ip)
	conn.commit()

def get_ips(curs):
	curs.execute('SELECT * FROM userip')
	return curs.fetchall()