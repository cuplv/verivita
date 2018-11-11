import db
import sys

db_uri = "sqlite:///" + sys.argv[1]
dbc = db.get_db(db_uri)

groupname = "lifestate_va1"
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

matchingExp = [e for e in experiments if sys.argv[2] in e.target]

if(len(matchingExp) > 1):
    raise Exception("multiple matches")

if(len(matchingExp) == 0):
    raise Exception("no matches")

print matchingExp[0].get_stdout()
print matchingExp[0].get_stderr()
