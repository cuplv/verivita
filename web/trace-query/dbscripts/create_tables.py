import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import argparse
import fnmatch
from cbverifier.traces.ctrace import CTraceSerializer, CCallin, CMessage, CCallback

home_dir = os.getenv("HOME")
pg_pass = ""
with open("%s/.pgpass" % home_dir,'r') as f:
    pg_pass = f.readlines()[0].strip()
pg_user = "postgres"
 
class TraceDb:
    tables = ['method','method_param','traces','aggrigate_edge','trace_edge']
    tables.reverse()
    def __init__(self,dbname,tables_file):
        self.dbname = dbname
        self.tables_file = tables_file
    def drop_tables(self):
        with psycopg2.connect(user=pg_user, password=pg_pass, dbname=self.dbname, host='localhost') as conn:
            cur = conn.cursor()
            for table in self.tables:
                cur.execute("drop table %s;" % (table,))
    
    def database_exists(self):
        result = ""
        with psycopg2.connect(user=pg_user, 
                password=pg_pass, dbname='postgres',host='localhost') as conn:
            cur = conn.cursor()
            exists = cur.execute("""select datname from pg_catalog.pg_database where lower(datname) = lower(%s)""", (self.dbname,))
            result = cur.fetchone() is not None
        return result
    def create_database(self):
        try:
            conn = psycopg2.connect(user=pg_user, password=pg_pass, dbname='postgres',host='localhost')
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute('create database %s' % self.dbname)
        finally:
            conn.close()
    
    def create_tables(self):
        with psycopg2.connect(user=pg_user, password=pg_pass, dbname=self.dbname, host='localhost') as conn:
            f = open(self.tables_file,'r')
            create_commands = f.read()
            cur = conn.cursor()
            cur.execute(create_commands)

    def import_message(connection, object_method_param_map):
            #store relationship between trace objects and message positions
            #TODO:loop over messages in ctrace (tree structure so probably recursive)
            while False:
                #TODO: add message to method table
                #TODO: add relevant method_param entries to table
                #TODO: put all objects in object_method_param_map
                #TODO: add edges for all methods already in object_method_param_map - aggrigate edge - trace_edge
                pass


    def import_trace(self,ctrace, connection):
        object_method_param_map = {} #concrete objects in trace mapped to set of MethodParam objects
        i_import_trace(connection)



    def import_trace_data(self,trace_basepath):
        with psycopg2.connect(user=pg_user, password=pg_pass, dbname=self.dbname, host='localhost') as conn:
            trace_directory = TraceDirectory(trace_basepath)
            #loop over traces
            for trace in trace_directory:
                trace_name = trace['trace_name']
                app_name = trace['app_name']
                relative_path = trace['relative_path']
                git_repo = trace['git_repo']
                # serialize to ctrace
                ctrace = CTraceSerializer.read_trace_file_name(trace['full_path'], False, True)
                # check if trace already added
                cur = connection.cursor()
                cur.execute('SELECT trace_id FROM traces WHERE trace_name = %s AND app_name = %s;', (trace_name,app_name)) 
                if cur.fetchone() is not None:
                    raise Exception("Trace already added") #TODO: should we do something better here?
                cur.close()
                # add trace to traces table
                cur = connection.cursor()
                trace_runner_version = trace['trace_runner_version']
                cur.execute("INSERT INTO traces (app_name,trace_name,git_repo,trace_runner_version) VALUES (%s,%s,%s,%s);", 
                        (app_name,trace_name,git_repo,trace_runner_version))
                cur.close()

            
                raise Exception("dbg_done")
                import_trace(ctrace,conn)

#loads a directory of traces and maps to names and github repos
class TraceDirectory:
    def __init__(self,base_path):
        self.base_path = base_path
        tracefiles = {}
        for root,dirnames,filenames in os.walk(base_path):
            for filename in fnmatch.filter(filenames, "*.repaired"):
                relpath = root.split(base_path)[1]
                rel_trace_path = os.path.join(relpath,filename)
                trace_path=os.path.join(root,filename)
                #TODO: github link
                #TODO: extract trace_runner_version from somewhere
                tracefiles[trace_path] = {"full_path": trace_path, 
                        "relative_path":rel_trace_path, 
                        "app_name":self.pathToAppId(trace_path,{}), 
                        'trace_name':rel_trace_path.split(os.sep)[-1],
                        'git_repo':"",
                        'trace_runner_version':0}
        self.tracefiles = tracefiles
    def __iter__(self):
        class TDIter:
            def __init__(iself):
                iself.iter = self.tracefiles.__iter__()
            def next(iself):
                return self.tracefiles[iself.iter.next()]
        return TDIter()
    
    def pathToAppId(self,outpath, alias_map):
       outpath_pieces = outpath.split("/")
       if outpath_pieces[5] == "monkey_traces": #TODO: split data not on file path, this is a bad way to do it
           pass
           appname = outpath_pieces[-3]
       else:
           if len(outpath_pieces) > 3:
               appname = outpath_pieces[-4]
               if appname.isdigit():
                   appname = outpath_pieces[-5]
           else:
               raise Exception("unparseable path")
       if appname in alias_map:
           return alias_map[appname]
       else:
           return appname
    def appIdToGit(self, appid, mapfile):
        pass #TODO:



def tracedb_from_default():
    return TraceDb(dbname="trace_query",tables_file="tables.txt")

#import and clean out existing data
def import_clean(trace_dir_list):
    pass

#add data to existing data
def import_append(trace_dir_list):
    pass
