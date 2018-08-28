import os
import time
import sqlite3

sqlitefile = "vvserver.db"
# if os.path.isfile(sqlitefile):
#     os.remove(sqlitefile)
TASKTIMEOUT_MS = 600 * 1000 # only serve tasks created in the last 10 minutes

def current_db_timestamp():
    return int(time.time() * 1000)

def clear_timeout():
    with sqlite3.connect(sqlitefile) as conn:
        ctime = current_db_timestamp()
        deadtime = ctime-TASKTIMEOUT_MS
        conn.execute("DELETE FROM tasks WHERE id < ?", (deadtime,))
        conn.commit()

# Returns id if success, None if failure
def create_task(query,rule):
    with sqlite3.connect(sqlitefile) as conn:
        ctime = current_db_timestamp()
        for row in conn.execute("SELECT id FROM tasks WHERE id=?", (ctime,)):
            return None #Fail if id already exists, probably better id out there but this works for now
        conn.execute("""
            INSERT INTO tasks VALUES (?,?,?,?,?,?,?)
        """, (ctime, query, 0, -1, "{}", "",rule))
        conn.commit()
        return ctime

# Returns pair of (id,query,rule)
def claim_task():
    with sqlite3.connect(sqlitefile) as conn:
        ctime = current_db_timestamp()
        deadtime = ctime-TASKTIMEOUT_MS
        conn.isolation_level = 'EXCLUSIVE'
        conn.execute('BEGIN EXCLUSIVE')
        for row in conn.execute(
                "SELECT id,query,rule FROM tasks WHERE id > ? AND running=0", (deadtime,)):
            conn.execute("UPDATE tasks SET running=1 WHERE id=?", (row[0],))
            #TODO: check that this works
            conn.commit()
            return row
        conn.commit()
    return None

def finish_task_safe(id):
    with sqlite3.connect(sqlitefile) as conn:
        conn.execute("UPDATE tasks SET running=2,safe=1 WHERE id=?",(id,))
        conn.commit()
def finish_task_unsafe(id, counter_example):
    with sqlite3.connect(sqlitefile) as conn:
        conn.execute("UPDATE tasks SET running=2,safe=0,counter_example=? WHERE id=?",(counter_example,id))
        conn.commit()

def finish_task_error(id, error_message):
    with sqlite3.connect(sqlitefile) as conn:
        conn.execute("UPDATE tasks SET running=2,safe=2,error_message=? WHERE id=?",(error_message,id))
        conn.commit()


class TaskCompleteSafe:
    pass

    def status(self):
        return "SAFE"


class TaskRunning:
    pass

    def status(self):
        return "RUNNING"

class TaskCompleteUnsafe:
    def __init__(self, counterexample):
        self.counter_example = counterexample

    def status(self):
        return "UNSAFE"

class TaskCompleteError:
    def __init__(self, msg):
        self.msg = msg

    def status(self):
        return "ERROR"

def get_task(id):
    with sqlite3.connect(sqlitefile) as conn:
        for row in conn.execute("SELECT running,safe,counter_example,error_message FROM tasks WHERE id=?", (id,)):
            running = row[0]
            safe = row[1]
            counter_example = row[2]
            error_message = row[3]
            if running < 2:
                return TaskRunning()
            elif safe == 0:
                return TaskCompleteUnsafe(counter_example)
            elif safe == 1:
                return TaskCompleteSafe()
            else:
                return TaskCompleteError(error_message)
        return TaskCompleteError("no such task")


# Create sqlite table and clear out old junk
with sqlite3.connect(sqlitefile) as conn:
    #running: 0 if not started 1 if running 2 if finished
    #safe: 0 if unsafe 1 if safe, -1 if not started, 2 if failure
    #counterexample: ctrace for
    #id is start time in milliseconds
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id integer PRIMARY KEY,
            query VARCHAR(10),
            running integer,
            safe integer,
            counter_example VARCHAR(10),
            error_message VARCHAR(10),
            rule VARCHAR(10)
        );
    """)
    conn.commit()
    # clear_timeout()