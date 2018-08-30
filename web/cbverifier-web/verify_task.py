import time

from google.protobuf.json_format import Parse
import cbverifier.traces.ctrace as vtr
from cbverifier.driver import DriverOptions, Driver
import cbverifier.android_specs.gen_config as Speclist
import os
from QueryTrace_pb2 import CCallback, CVariable, Hole, CCommand, CCallin, CParam, CMessage, CTrace, CallbackOrHole
from google.protobuf.json_format import MessageToJson

import vv_database as db
from cbverifier.encoding.cex_printer import CexPrinter
import json


def fullSigConv(s):
    s = s.strip()
    s = " ".join([c for c in s.split(" ") if c != ""]) #remove duplicate spaces
    rtype = s.split(" ")[0]
    withoutreturn = " ".join(s.split(" ")[1:])
    if rtype == "class" or rtype == "interface":
        rtype = s.split(" ")[1]
        withoutreturn = " ".join(s.split(" ")[2:])
    methodname = s.split("(")[0].split(".")[-1]
    params = s.split("(")[1]
    sig = "%s %s(%s" % (rtype, methodname, params)
    fmwk = ".".join(withoutreturn.split("(")[0].split(".")[:-1])
    return (sig, fmwk)

def cTracePrototoVTrace(ctr,objmap, msgCounter):
    vtrace = vtr.CTrace()
    for cb in ctr.callbacks:
        cb = cCallbackOrHoleProtoToVTrace(cb,objmap, msgCounter)
        if cb is not None:
            vtrace.add_msg(cb)
    return vtrace
def cCommandProtoToVTrace(corh, objmap, msgCounter):
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
                         return_value=convertToCParam(callin.return_value, objmap),
                         message_id=msgCounter.next()
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
def cCallbackOrHoleProtoToVTrace(cbh,objmap,msgCounter):
    if cbh.WhichOneof("cb_command") == 'callback':
        return cCallbackProtoToVTrace(cbh, objmap, msgCounter)
    else:
        return None


def cCallbackProtoToVTrace(cbh, objmap, msgCounter):
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
                       return_value=convertToCParam(callback.return_value, objmap),
                       message_id= msgCounter.next())
    for ci in callback.nested_commands:
        vcallin = cCommandProtoToVTrace(ci, objmap, msgCounter)
        if vcallin is not None:
            cb.add_msg(vcallin)
    return cb


class ObjMap:
    def __init__(self):
        self.current = 0
        self.objmap = {}
        self.namemap = {}

    def new_obj(self, name):
        if name not in self.namemap:
            v = self.current
            self.current += 1
            self.objmap[v] = name
            self.namemap[name] = v
            return v
        else:
            return self.namemap[name]

    def new_noname_obj(self):
        name = str(self.current)
        return self.new_obj(name)

    def get_name(self, name):
        return self.objmap[name]


class MessageCounter():
    def __init__(self):
        self.count = 0
    def next(self):
        tmp = self.count
        self.count += 1
        return tmp


def ctrace_from_proto(content):
    proto_ctrace = Parse(content, CTrace())
    objmap = ObjMap()
    msgCounter = MessageCounter()
    vtrace = cTracePrototoVTrace(proto_ctrace, objmap,msgCounter)
    return (vtrace, objmap)


def verify_rule(spec_file_list, ctrace):

    driver_opts = DriverOptions("",
                                "",
                                spec_file_list,
                                False, #TODO: would like to turn off simplify
                                False, #debug
                                None, #filter
                                True,
                                False)
    driver = Driver(driver_opts, ctrace)
    res = driver.run_ic3(os.environ['NUXMV_PATH'], 40)
    print "done"
    return res


def fmwk_from_classmethod(classname, methodname):
    """return pair of (fmwk, sig)"""
    sp_split = methodname.split(" ")
    rettype = sp_split[0]
    rest = " ".join(sp_split[1:])
    return ("%s %s.%s" % (rettype, classname, methodname), methodname)


def cValue_to_proto(c, objmap):
    if c is None:
        return param_hole()
    elif c.value is not None:
        raise Exception("TODO: implement value back serialize")
    elif not c.is_null:
        cp = CParam()
        param = CVariable()
        param.name = objmap.get_name(c.object_id)
        cp.variable.CopyFrom(param)
        return cp

def param_hole():
    cp = CParam()
    param = Hole()
    cp.pr_hole.CopyFrom(param)
    return cp

def ccallin_as_proto(callin, objmap):
    cio = CCommand()
    ci = CCallin()
    classname = callin.class_name
    method_name = callin.method_name

    params = [cValue_to_proto(f,objmap) for f in callin.params]
    return_value = cValue_to_proto(callin.return_value, objmap)

    ci.parameters.extend(params[1:])
    ci.receiver.CopyFrom(params[0] if len(params) > 0 else param_hole())
    ci.return_value.CopyFrom(return_value)
    (fmwk,sig) = fmwk_from_classmethod(classname,method_name)
    ci.framework_class = fmwk
    ci.method_signature = sig
    cio.callin.CopyFrom(ci)
    return cio




def ctrace_as_proto(cb, objmap): # TODO: rename to callback_as_proto
    # cb = ctr[1]
    cbo = CCallback()
    proto_children = [ ccallin_as_proto(f, objmap) for f in cb.children ]
    cbo.nested_commands.extend(proto_children)
    classname = cb.class_name
    params = [cValue_to_proto(f,objmap) for f in cb.params]
    return_value = cValue_to_proto(cb.return_value, objmap)
    method_name = cb.method_name

    cbo.return_value.CopyFrom(return_value)
    cbo.receiver.CopyFrom(params[0])
    cbo.parameters.extend(params[1:])

    (fmwk,sig) = fmwk_from_classmethod(classname, method_name)
    cbo.method_signature = sig
    cbo.first_framework_overrride_class = fmwk
    cbho = CallbackOrHole()
    cbho.callback.CopyFrom(cbo)
    pass
    return cbho

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
                print "starting task: %s on thread %i" % (str(id), os.getpid())
                ctr, objmap = ctrace_from_proto(query)
                rules = Speclist.allow_disallow_rules[rule][1]
                spec_file_list = []
                for s in [enable_rules, rules, Speclist.subexpressions]:
                    spec_file_list += [os.path.join(basepath, v) for v in s]

                (res, cex, mapback) = verify_rule(spec_file_list, ctr)
                if res == 'SAFE':
                    db.finish_task_safe(id)
                elif res == 'UNSAFE':
                    import sys
                    printer = CexPrinter(mapback, cex, sys.stdout, False)
                    printer.print_cex()

                    cex_ctrace = []
                    i = 0
                    prev_step = None
                    last_entry = None
                    for step in cex:
                        if i == 0:
                            pass
                        else:
                            dir,val = mapback.get_fired_trace_msg(prev_step, step)
                            if isinstance(val,vtr.CCallback):
                                if (dir == 'EXIT') and (val.message_id == last_entry):
                                    pass #don't add if same as last entry
                                elif dir == 'ENTRY':
                                    last_entry = val.message_id
                                    cex_ctrace.append(ctrace_as_proto(val,objmap))
                                else:
                                    cex_ctrace.append(ctrace_as_proto(val,objmap))
                        prev_step = step
                        i += 1
                    print "TODO"
                    ctr = CTrace()
                    ctr.callbacks.extend(cex_ctrace)
                    db.finish_task_unsafe(id, MessageToJson(ctr))
                else:
                    db.finish_task_error()
            except Exception as e:
                db.finish_task_error(id, "Thrown error: {}".format(e))