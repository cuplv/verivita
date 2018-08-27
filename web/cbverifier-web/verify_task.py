import time

from google.protobuf.json_format import Parse
import cbverifier.traces.ctrace as vtr
from cbverifier.driver import DriverOptions, Driver
import cbverifier.android_specs.gen_config as Speclist
import os
from QueryTrace_pb2 import CCallback, CVariable, Hole, CCommand, CCallin, CParam, CMessage, CTrace
from google.protobuf.json_format import MessageToJson

import vv_database as db

def fullSigConv(s):
    s = s.strip()
    s = " ".join([c for c in s.split(" ") if c != ""]) #remove duplicate spaces
    rtype = s.split(" ")[0]
    methodname = s.split("(")[0].split(".")[-1]
    params = s.split("(")[1]
    sig = "%s %s(%s" % (rtype, methodname, params)
    withoutreturn = " ".join(s.split(" ")[1:])
    fmwk = ".".join(withoutreturn.split("(")[0].split(".")[:-1])
    return (sig, fmwk)

def cTracePrototoVTrace(ctr,objmap):
    vtrace = vtr.CTrace()
    for cb in ctr.callbacks:
        cb = cCallbackOrHoleProtoToVTrace(cb,objmap)
        if cb is not None:
            vtrace.add_msg(cb)
    return vtrace
def cCommandProtoToVTrace(corh, objmap):
    typeof = corh.WhichOneof("ci_command")
    if typeof == "callin":
        callin = corh.callin
        sig,fmwk = fullSigConv(callin.framework_class)
        pr = [convertToCParam(p,objmap) for p in callin.parameters]
        pr.insert(0, convertToCParam(callin.receiver, objmap))
        ci = vtr.CCallin(class_name=fmwk,
                         method_name=sig, #TODO: make sure this format is right
                         thread_id=1,
                         params=pr,
                         return_value=convertToCParam(callin.return_value, objmap)
                         )
        for cb in callin.nested_callbacks:
            cbv = cCallbackProtoToVTrace(cb, objmap)
            ci.add_msg(cbv)
        return ci
    elif typeof == "ci_hole":
        return None #ignore holes in verif


#TODO: current behavior is to replace holes with a new object, we may want something else here
def convertToCParam(p, objmap):
    paramtype = p.WhichOneof("param")
    c = vtr.CValue()
    c.is_null = False
    c.fmwk_type = "java.lang.Object"
    if paramtype == "pr_hole":
        c.object_id = objmap.new_noname_obj()
    elif paramtype == "variable":
        c.object_id = objmap.new_obj(p.variable.name)
    elif paramtype is None:
        return None #TODO: when does it do this instead of hole?
    elif paramtype == "primitive":
        raise Exception("unimp")
    elif paramtype == "object":
        raise Exception("unimp")
    else:
        raise Exception("unknown param type")
    return c
def cCallbackOrHoleProtoToVTrace(cbh,objmap):
    if cbh.WhichOneof("cb_command") == 'callback':
        return cCallbackProtoToVTrace(cbh, objmap)
    else:
        return None


def cCallbackProtoToVTrace(cbh, objmap):
    callback = cbh.callback
    # sig,fmwk = callback.method_signature
    full_sig = "class " + callback.first_framework_overrride_class
    sig, fmwk = fullSigConv(full_sig)
    pr = [convertToCParam(p, objmap) for p in callback.parameters]
    pr.insert(0, convertToCParam(callback.receiver, objmap))
    override = vtr.FrameworkOverride(fmwk, sig, False) # TODO: is_interface?
    cb = vtr.CCallback(class_name=fmwk,
                       method_name=sig,
                       thread_id=1,
                       fmwk_overrides=[override],
                       params=pr,
                       return_value=convertToCParam(callback.return_value, objmap))
    for ci in callback.nested_commands:
        vcallin = cCommandProtoToVTrace(ci, objmap)
        if vcallin is not None:
            cb.add_msg(vcallin)
    return cb


class ObjMap:
    def __init__(self):
        self.current = 0
        self.objmap = {}

    def new_obj(self, name):
        v = self.current
        self.current += 1
        self.objmap[v] = name
        return v

    def new_noname_obj(self):
        name = str(self.current)
        return self.new_obj(name)

    def getName(self,value):
        return self.objmap[value]


def ctrace_from_proto(content):
    proto_ctrace = Parse(content, CTrace())
    objmap = ObjMap()
    vtrace = cTracePrototoVTrace(proto_ctrace, objmap)
    return vtrace


def verify_rule(spec_file_list, ctrace):

    driver_opts = DriverOptions("",
                                "",
                                spec_file_list,
                                True, #TODO: would like to turn off simplify
                                False, #debug
                                None, #filter
                                True,
                                False)
    driver = Driver(driver_opts, ctrace)
    res = driver.run_ic3(os.environ['NUXMV_PATH'], 40)
    print "done"
    return res


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description='Verify a Serialized Ctrace for web server (see app.py)')
    # parser.add_argument('--file', type=str, description='sqlite file to get commands and store results')
    #
    # args = parser.parse_args()

    enable_rules = Speclist.enable_disable_rules["lifestate_va1"]
    basepath = os.environ['VERIVITA_PATH']
    while True:
        time.sleep(0.5)
        task = db.claim_task()
        if task is not None:
            id,query,rule = task
            try:
                print "starting task: %s" % str(id)
                ctr = ctrace_from_proto(query)
                rules = Speclist.allow_disallow_rules[rule][1]
                spec_file_list = []
                for s in [enable_rules, rules, Speclist.subexpressions]:
                    spec_file_list += [os.path.join(basepath, v) for v in s]
                (res, cex, mapback) = verify_rule(spec_file_list, ctr)

                if res == 'SAFE':
                    db.finish_task_safe(id)
                elif res == 'UNSAFE':
                    print "TODO"
                    db.finish_task_unsafe(id, "{}")
                else:
                    db.finish_task_error()
            except Exception as e:
                db.finish_task_error(id, "Thrown error: {}".format(e))

# print "verif process: %s" % str(r)

# print "verif task done: %s" % str(r)
# f.write("{}") #TODO: serialize here
# f.close()
#
# elif r > 0:
# f.close()
# pid,status = os.waitpid(r,0)
# if status == 0:
#     print "success fork closed"
#     f = open(fname,'r')
#     dat = f.read()
# else:
#     print "fail verifier fork"
# try:
#     os.remove(fname)
# except:
#     pass # ignore error here
# else:
# raise InvalidUsage("internal error")
# pass