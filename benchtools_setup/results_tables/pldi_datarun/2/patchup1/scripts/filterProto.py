import argparse
from cbverifier.traces.ctrace import CTraceSerializer, CCallin, CTrace, CCallback

def contains_callin_method(filter_class, filter_method, trace):

    for child in trace.children:
        if child.class_name == filter_class:
            if child.method_name == filter_method:
                return True
        if contains_callin_method(filter_class, filter_method, child):
            return True

    return False
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="filter list of proto files for ones which contain given callin")
    parser.add_argument('--filter_class', help='class of method', required=False)
    parser.add_argument('--filter_method', help='method signature, can be : separated list', required=False)
    parser.add_argument('--trace', help="single trace to check, prints trace path if found")
    args = parser.parse_args()

    try:
        trace = CTraceSerializer.read_trace_file_name(args.trace, False,False)
        if contains_callin_method(args.filter_class, args.filter_method, trace):
            print args.trace
    except:
        pass # ignore bad traces