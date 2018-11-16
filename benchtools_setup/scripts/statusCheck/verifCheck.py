import db
import sys

db_uri = "sqlite:///" + sys.argv[1]
dbc = db.get_db(db_uri)

groupname = "flowdroid_Fragment.startActivity"
group_id = dbc.get_group_id(groupname)

group = dbc.get_group(groupname)

experiments = [e for e in dbc.get_experiments_in_group(groupname)]

print "experiments run: %i" % len(experiments)


#print dir(experiments[0])

#print experiments[0].target
#for exp in experiments:
#    out = exp.get_stdout()
#    if "The trace cannot be simulated (it gets stuck at the" in out:
#        print exp.target

print "===stdout==="
print experiments[int(sys.argv[2])].get_stdout()
print "===stderr==="
print experiments[int(sys.argv[2])].get_stderr()
