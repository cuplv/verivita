import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

home_dir = os.getenv("HOME")
f = open("%s/.pgpass" % home_dir,'r')
pg_pass = f.readlines()[0].strip()
 

def database_exists(dbname):
    conn = psycopg2.connect(user="postgres", password=pg_pass, dbname='postgres',host='localhost')
    cur = conn.cursor()
    exists = cur.execute("""select datname from pg_catalog.pg_database where lower(datname) = lower(%s)""", (dbname,))
    result = cur.fetchone() is not None
    conn.close()
    return result
def create_database(dbname):
    conn = psycopg2.connect(user="postgres", password=pg_pass, dbname='postgres',host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute('create database %s' % dbname)
    conn.close()

def create_table():
    pass


if __name__ == "__main__":
    dbname = "trace_query"
    if not database_exists(dbname):
        create_database(dbname)

