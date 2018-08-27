#!flask/bin/python
import subprocess

from flask import Flask, jsonify, request
from cbverifier.specs.spec_parser import spec_parser
import cbverifier.specs.spec_ast as sast
from QueryTrace_pb2 import CCallback, CVariable, Hole, CCommand, CCallin, CParam, CMessage, CTrace
from google.protobuf.json_format import MessageToJson
import cbverifier.android_specs.gen_config as Speclist
import vv_database as db
import subprocess

NUM_WORKERS = 1

for i in xrange(NUM_WORKERS):
    subprocess.Popen(["python", "verify_task.py"])




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







@app.route('/get_disallow_list', methods = ['GET'])
def get_disallow_list_task():
    return jsonify(Speclist.allow_disallow_rules.keys())


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/verify', methods=['POST'])
def verify_task():
    print "verify start"
    rule = request.args.get('rule')
    if rule is None:
        raise InvalidUsage("Please specify disallow rule")
    content = request.data

    id = db.create_task(content, rule)
    return jsonify({"id":id})


@app.route('/status', methods=['GET'])
def get_task():
    id = request.args.get('id')
    if id is None:
        raise InvalidUsage("Please specify disallow rule")
    status = db.get_status(id)

    res = {"status" : status.status()}

    if isinstance(status, db.TaskCompleteError):
        res["msg"] = status.msg
    elif isinstance(status, db.TaskCompleteUnsafe):
        res["counter_example"] = status.counter_example

    return jsonify(res)


if __name__ == '__main__':
        app.run(debug=True)

