# This script takes a callin and a trace and prints out the callbacks which are contained

import argparse

from cbverifier.specs.spec import Spec
from cbverifier.traces.ctrace import CTraceSerializer, CCallin, CTrace, CCallback
import cbverifier.specs.spec_ast as ast

def methodName(ccallback):
    if ccallback.method_name == "<clinit>":
        return ccallback.method_name
    else:
        return ccallback.method_name.split(" ")[1].split("(")[0]

def getCallbacksForCallin(acc, classname_methodname_tup, trace):

    if isinstance(trace,CTrace):
        cacc = acc
    elif isinstance(trace,CCallback) or isinstance(trace,CCallin):
        cacc = acc + [(trace.class_name,methodName(trace))]

    for tlcb in trace.children:
        tlcb_methodname = methodName(tlcb)
        tlcb_classname = tlcb.class_name
        if isinstance(tlcb, CCallin):
            if tlcb_classname == classname_methodname_tup[0] and tlcb_methodname == classname_methodname_tup[1]:
                print "%s %s" % (str(cacc + []), str((tlcb_classname,tlcb_methodname)))
        getCallbacksForCallin(cacc, classname_methodname_tup, tlcb)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine possible method names with types in subexpressions (REGEXP)')
    parser.add_argument('--trace', type=str,
                        help="Trace to scan",required=True)
    parser.add_argument('--disallow', type=str,
                        help="Spec files associated with this disallow colon separated")

    args = parser.parse_args()

    spec_list = Spec.get_specs_from_files(args.disallow.split(":"))

    disallows = set()
    for spec in spec_list:
        rhs = ast.get_spec_rhs(spec.ast)
        if rhs[0] == ast.CALL_ENTRY:
            if rhs[1][0] == ast.CI:
                identifier = rhs[3][1]
                methodname = identifier.split(".")[-1]
                classname = ".".join(identifier.split(" ")[1].split(".")[:-1])
                disallows.add((classname,methodname))

    #read trace file into ctrace TODO
    trace = CTraceSerializer.read_trace_file_name(args.trace, False, False)
    for cmt in disallows:
        callbacks = getCallbacksForCallin([],cmt, trace)