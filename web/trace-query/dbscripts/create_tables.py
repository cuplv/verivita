import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

home_dir = os.getenv("HOME")
pg_pass = ""
with open("%s/.pgpass" % home_dir,'r') as f:
    pg_pass = f.readlines()[0].strip()
pg_user = "postgres"
 

def database_exists(dbname):
    result = ""
    with psycopg2.connect(user=pg_user, 
            password=pg_pass, dbname='postgres',host='localhost') as conn:
        cur = conn.cursor()
        exists = cur.execute("""select datname from pg_catalog.pg_database where lower(datname) = lower(%s)""", (dbname,))
        result = cur.fetchone() is not None
    return result
def create_database(dbname):
    try:
        conn = psycopg2.connect(user=pg_user, password=pg_pass, dbname='postgres',host='localhost')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute('create database %s' % dbname)
    finally:
        conn.close()

def create_tables(tables_file, dbname):
    with psycopg2.connect(user=pg_user, password=pg_pass, dbname=dbname, host='localhost') as conn:
        f = open(tables_file,'r')
        create_commands = f.read()
        cur = conn.cursor()
        cur.execute(create_commands)

if __name__ == "__main__":
    dbname = "trace_query"
    if not database_exists(dbname):
        create_database(dbname)

