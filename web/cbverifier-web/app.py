#!flask/bin/python
from flask import Flask, jsonify, request
from cbverifier.specs.spec_parser import spec_parser
import cbverifier.specs.spec_ast as sast
from QueryTrace_pb2 import CCallback, CVariable, Hole, CCommand, CCallin, CParam, CMessage, CTrace
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse
import cbverifier.traces.ctrace as vtr


app = Flask(__name__)

def specASTtoCTrace(ast):
    
    # import ipdb; ipdb.set_trace() #TODO

    is_entry = sast.get_node_type(ast) == sast.CALL_ENTRY
    assert(is_entry != (sast.get_node_type(ast) == sast.CALL_EXIT))
    is_callin = ast[1][0] == sast.CI
    assert (is_callin != (ast[1][0] == sast.CB)) #assert callin or callback

    combname = ast[3][1]
    assert(ast[3][0] == 2) #not sure when this wouldn't be an identifier

    paramlist_head = ast[4]

    paramlist_types = []
    paramlist_vals = []
    while paramlist_head[0] != sast.NIL:
        paramlist_types.append(paramlist_head[2][1])
        var_place = paramlist_head[1]
        v = astToCParam(var_place)
        paramlist_vals.append(v)
        paramlist_head = paramlist_head[3]

    receiver = astToCParam(ast[2])
    spsp = combname.split(" ")
    paramtypes = "(" + ",".join(paramlist_types) + ")"
    signature = spsp[0] + " " + combname.split(".")[-1] + paramtypes
    # framework_class = ".".join(combname.split(".")[0:-1])
    framework_class = combname + paramtypes
    returnval = astToCParam(ast[5])
    ccommand = CMessage()
    if(is_callin):
        pb = CCallin()
        pb.method_signature = signature
        pb.framework_class = framework_class
        pb.parameters.extend(paramlist_vals)
        pb.receiver.CopyFrom(receiver)
        pb.return_value.CopyFrom(returnval)
        ccommand.m_callin.CopyFrom(pb)
    else:
        pb = CCallback()
        pb.method_signature = signature
        pb.first_framework_overrride_class = framework_class
        pb.parameters.extend(paramlist_vals)
        pb.receiver.CopyFrom(receiver)
        pb.return_value.CopyFrom(returnval)
        ccommand.m_callback.CopyFrom(pb)



    return ccommand


def astToCParam(var_place):
    lv = var_place[0]
    v = CParam()
    if lv == sast.ID:
        # cvar = CVariable()
        # cvar.name = paramlist_head[2][1]
        # v.variable = cvar
        v.variable.name = var_place[1]
    elif lv in [sast.DONTCARE, sast.NIL]:
        # hole = Hole()
        # hole.is_selected = False
        # v.pr_hole.CopyFrom(hole)
        v.pr_hole.is_selected = False  # TODO: this seems strange, test it
    else:
        raise Exception("unimplemented")  # TODO: handle other cases
    return v


@app.route('/')
def index():
    return "Verivita verifier web server."

@app.route('/parse_ls', methods=['POST'])
def parse_task():
    content = request.json
    try:
        if "msg" in content:
            if content["msg"] == "callback":
                joinm = "= [CB] [EXIT]"
            elif content["msg"] == "callin":
                joinm = "= [CI] [EXIT]"
            else:
                raise Exception("too msg must be callback or callin")
            cbm = joinm.join(content['specline'].split("="))
            parsed = spec_parser.parse_call(cbm)


        else:
            parsed = spec_parser.parse_call(content["specline"])
        assert(parsed is not None)
    except:
        em = CMessage()
        em.m_problem.description = "parse failure"
        return MessageToJson(em)
    c_trace = specASTtoCTrace(parsed)
    # return jsonify({"stuff": "stuff"})
    return MessageToJson(c_trace)

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
def cCommandProtoToVTrace(corh, objmap):
    typeof = corh.WhichOneof("ci_command")
    if typeof == "callin":
        callin = corh.callin
        sig,fmwk = fullSigConv(callin.framework_class)
        pr = [convertToCParam(p,objmap) for p in callin.parameters]
        pr.insert(0, convertToCParam(callin.receiver, objmap))
        
        raise Exception("unimp")
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
    elif paramtype == "primitive":
        raise Exception("unimp")
    elif paramtype == "object":
        raise Exception("unimp")
    else:
        raise Exception("unknown param type")
    return c
def cCallbackOrHoleProtoToVTrace(cbh,objmap):
    if cbh.WhichOneof("cb_command") == 'callback':
        callback = cbh.callback
        # sig,fmwk = callback.method_signature
        full_sig = "class " + callback.first_framework_overrride_class
        sig,fmwk = fullSigConv(full_sig)
        pr = [convertToCParam(p, objmap) for p in callback.parameters]
        pr.insert(0, convertToCParam(callback.receiver, objmap))
        cb = vtr.CCallback(class_name=fmwk,
                           method_name=sig,
                           thread_id=1,
                           fmwk_overrides=[full_sig],
                           params=pr,
                           return_value=convertToCParam(callback.return_value, objmap))
        for ci in callback.nested_commands:
            vcallin = cCommandProtoToVTrace(ci, objmap)
            if vcallin is not None:
                cb.add(vcallin)
        return cb
    else:
        return None

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
        return self.newObj(name)
    def getName(self,value):
        return self.objmap[value]

@app.route('/verify', methods=['POST'])
def verify_task():
    content = request.data
    proto_ctrace = Parse(content, CTrace())
    objmap = ObjMap()
    cTracePrototoVTrace(proto_ctrace, objmap)
    return "[]"



if __name__ == '__main__':
        app.run(debug=True)

