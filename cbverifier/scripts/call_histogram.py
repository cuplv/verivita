import argparse
import fnmatch
import os
import sqlite3

def get_methods(ctr):
    pass

def load_trace_methdos(trace_path):
    ctr = CTraceSerializer.read_trace_file_name(trace_path, False, True)
    methods = get_methods(ctr)
    return methods

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="print out histogram of methods")
    parser.add_argument('--dir', type=str, help="directory to find trace files")
    parser.add_argument('--db', type=str, help="database to store summarized trace data", required=True)
    parser.add_argument('--opr', type=str, help="possible values: scan_traces, dump_histogram")
    args = parser.parse_args()

    # find all trace files in directory


    if(args.opr == "scan_traces"):
        matches = []
        basedir = args.dir
        for root, dirnames, filenames in os.walk(basedir):
            for filename in fnmatch.filter(filenames, '*.repaired'):
                matches.append(os.path.join(root, filename))
        for match in matches:
            identifier = match.split(basedir)[1]
            print match

