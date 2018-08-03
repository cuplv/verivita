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

    def get_method_id(self,method_dat, connection):
        exists_cur = connection.cursor()
        exists_cur.execute("""
            SELECT method_id FROM method 
            WHERE 
                signature = %s AND 
                first_framework_override = %s AND
                is_callback = %s AND
                is_callin = %s
        """,method_dat)
        method_list = exists_cur.fetchall()
        exists_cur.close()
        results = len(method_list)
        assert(results < 2)
        return method_list[0][0] if results == 1 else None
    def get_method_param_id(self, method_param_dat, connection):
        cur = connection.cursor()

        cur.execute("""
            SELECT param_id FROM method_param
            WHERE
                method_id = %s AND
                param_position = %s
        """,method_param_dat)
        param_list = cur.fetchall()
        results = len(param_list)
        cur.close()
        assert(results < 2)
        return param_list[0][0] if results == 1 else None
    def insert_method_param(self,method_param_dat,connection):
        method_param_id = self.get_method_param_id(method_param_dat, connection)
        if method_param_id is None:
            cur = connection.cursor()
            cur.execute("""
                INSERT INTO method_param (method_id,param_position)
                VALUES (%s,%s)
            """,method_param_dat)
            cur.close()
            method_param_id = self.get_method_param_id(method_param_dat,connection)
        return method_param_id
    def get_edge_id(self,trace_edge_dat, connection):
        cur = connection.cursor()
        cur.execute("""
            SELECT edge_id FROM trace_edge WHERE start_method_param = %s AND end_method_param = %s AND trace_id = %s;
        """, trace_edge_dat)
        edge_list = cur.fetchall()
        cur.close()
        assert(len(edge_list) < 2)
        return None if len(edge_list) == 0 else edge_list[0][0]

    def insert_trace_edge(self,method_param_id, old_methods, connection, trace_id):
        for old_method_id in old_methods:
            d1 = (method_param_id, old_method_id, trace_id)
            d2 = (old_method_id, method_param_id, trace_id)
            d1_id = self.get_edge_id(d1,connection)
            d2_id = self.get_edge_id(d2,connection)
            inslist = [d1,d2] if method_param_id != old_method_id else [d1]
            if (d1_id is None) and (d2_id is None):
                for d in inslist:
                    cur = connection.cursor() #TODO: finish me
                    cur.execute("""
                        INSERT INTO trace_edge (start_method_param,end_method_param,trace_id)
                        VALUES (%s,%s,%s);
                    """,d)
                    cur.close()
            else:
                assert( (d1_id is not None) and (d2_id is not None))

    def import_message(self,connection, object_method_param_map, message, trace_id):
            # add message to method table
            framework_override=None
            if isinstance(message, CCallback):
                if len(message.fmwk_overrides) > 0:
                    #TODO: we should probably figure out what to do on a list of these
                    #for now it makes sense to just use the first one
                    framework_override = str(message.fmwk_overrides[0])
            else:
                pass
                raise Exception("todo")
            signature = str(message.method_name)
            #application_class = str(message.class_name)
            is_callback = isinstance(message,CCallback)
            is_callin = isinstance(message,CCallin) 
            # check if method already inserted
            #TODO: this code will fail on concurrent imports, fix later, needs own transaction and lock on methods table

            method_dat = (signature,framework_override, is_callback, is_callin)
            method_id = self.get_method_id(method_dat, connection) 
            if method_id is None:
                cur = connection.cursor()
                cur.execute("""
                    INSERT INTO method (signature,first_framework_override,is_callback,is_callin)
                    VALUES (%s,%s,%s,%s);
                """, method_dat)
                cur.close()
            method_id = self.get_method_id(method_dat, connection) 
            assert(method_id is not None)
            
            # add relevant method_param entries to table

            # return value
            rval = None
            if message.return_value is not None:
                rval = message.return_value.object_id
            if rval is not None:
                if type(rval) != unicode:
                    assert(False)
                method_param_dat = (method_id,0) #0 for return value
                method_param_id = self.insert_method_param(method_param_dat, connection)
                oldset = object_method_param_map.get(rval,set())
                self.insert_trace_edge(method_param_id, oldset, connection,trace_id)
                object_method_param_map[rval] = oldset.union([method_param_id])
                del method_param_dat
                del method_param_id
                del oldset
            del rval
            # reciever and parameters
            paramcount = 0
            for param in message.params:
                paramcount += 1
                reval = param.object_id
                if reval is not None:
                    assert(type(reval) == unicode)
                    method_param_dat = (method_id,paramcount) #1 for reciever which is first in params
                    method_param_id = self.insert_method_param(method_param_dat, connection)
                    oldset = object_method_param_map.get(reval,set())
                    self.insert_trace_edge(method_param_id, oldset, connection,trace_id)
                    object_method_param_map[reval] = oldset.union([method_param_id])
                    del method_param_dat
                    del method_param_id
                    del oldset


                #TODO:loop over messages in ctrace (tree structure so probably recursive)


            for child in message.children:
                self.import_message(connection, object_method_param_map, child, trace_id)
                #TODO: put all objects in object_method_param_map
                #TODO: add edges for all methods already in object_method_param_map - aggrigate edge - trace_edge
                pass


    def import_trace(self,ctrace, connection, trace_id):
        #store relationship between trace objects and message positions
        object_method_param_map = {} #concrete objects in trace mapped to set of MethodParam objects
        for child in ctrace.children:
            self.import_message(connection,object_method_param_map, child, trace_id)
    #trace_dat_id is tuple of (trace_name,app_name)
    def get_trace_id(self,trace_dat_id, connection):
        cur = connection.cursor()
        cur.execute("""
            SELECT trace_id FROM traces WHERE trace_name = %s AND app_name = %s;
        """,trace_dat_id)
        trace_ids = cur.fetchall()
        cur.close()
        resultsize = len(trace_ids)
        assert(resultsize<2)
        return None if resultsize == 0 else trace_ids[0][0]

    def import_trace_data(self,trace_basepath,strict=True):
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
                trace_dat_id = (trace_name,app_name)
                #cur = conn.cursor()

                #cur.execute('SELECT trace_id FROM traces WHERE trace_name = %s AND app_name = %s;', (trace_name,app_name)) 
                existing_trace_id = self.get_trace_id(trace_dat_id, conn)
                if existing_trace_id is not None:
                    if(strict):
                        raise Exception("Trace already added") #TODO: should we do something better here?
                else:
                    # add trace to traces table
                    cur = conn.cursor()
                    trace_runner_version = trace['trace_runner_version']
                    query="""
                        INSERT INTO traces (app_name,trace_name,git_repo,trace_runner_version) 
                        VALUES (%s,%s,%s,%s);
                        """
                    cur.execute(query,(app_name,trace_name,git_repo,trace_runner_version))
                    
                    cur.close()
                existing_trace_id = self.get_trace_id(trace_dat_id, conn)
                self.import_trace(ctrace,conn, existing_trace_id)
                conn.commit()
                break
            

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
                        'git_repo':"todo",
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
