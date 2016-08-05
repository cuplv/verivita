""" Performs the runtime verification.
"""

import sys
import os
import optparse
import logging


from spec import SpecType, SpecSerializer, Spec

from ctrace import CTraceSerializer, ConcreteTrace
from verifier import Verifier

def read_from_files(spec_file_list):
    file_list = []
    for fname in spec_file_list:
        f = open(fname, "r")
        file_list.append(f)
    specs_map = SpecSerializer.read_multiple_specs(file_list)
    for f in file_list: f.close()
    return specs_map

def main():
    # Common to all modes
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    p = optparse.OptionParser()
    p.add_option('-t', '--tracefile',
                 help="File containing the concrete trace")
    p.add_option('-s', '--specfile', help="Specification file (: separated list of files)")
    p.add_option('-k', '--depth', help="Depth of the search")
    p.add_option('-i', '--inc', action="store_true",
                 default=False, help="Incremental search")
    p.add_option('-d', '--debugenc', action="store_true",
                 default=False,help="Use the debug encoding")

    p.add_option('-f', '--smvfile', help="Output smv file")
    p.add_option('-c', '--coi', action="store_true",
                 default=False, help="Apply cone of influence")

    p.add_option('-m', '--mode', type='choice',
                 choices= ["bmc","check-files", "print-trace","to-smv"],
                 help="bmc: run bmc on the trace." \
                 "check-files: check if the input files are well formed.",
                 default = "bmc")

    def usage(msg=""):
        if msg: print "----%s----\n" % msg
        p.print_help()
        sys.exit(1)

    opts, args = p.parse_args()

    if (opts.mode == "bmc" or opts.mode == "to-smv"):
        if (not opts.tracefile): usage("Missing trace file (-t)")
        if (not opts.specfile): usage("Missing specification file (-s)")
        if (not opts.depth): usage("Missing BMC depth")

        if (not os.path.exists(opts.tracefile)):
            usage("Trace file %s does not exists!" % opts.tracefile)

        spec_file_list = opts.specfile.split(":")
        for f in spec_file_list:
            print "Checking %s " % f
            if (not os.path.exists(f)):
                usage("Specification file %s does not exists!" % f)
        try:
            depth = int(opts.depth)
        except:
            usage("%s must be a natural number!" % opts.depth)
        if (depth < 0): usage("%s must be positive!" % opts.depth)

        if (opts.mode == "to-smv"):
            if (not opts.smvfile):
                usage("Destination smv file not specified!")

        # Parse the trace file
        with open(opts.tracefile, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)

        # Parse the specification file
        specs_map = read_from_files(spec_file_list)

        not_mapped = ctrace.rename_trace(specs_map["mappings"], True)
        logging.debug("\n---Not mapped symbols:---")
        for a in not_mapped: logging.debug(a)

        # Call the verifier
        verifier = Verifier(ctrace, specs_map["specs"],
                            specs_map["bindings"],
                            opts.debugenc,
                            opts.coi)
        if (opts.mode == "bmc"):
            if (not opts.inc):
                cex = verifier.find_bug(depth)
            else:
                cex = verifier.find_bug_inc(depth)

            if (logging.getLogger().getEffectiveLevel() >= logging.INFO):
                ctrace.print_trace()
                if verifier.debug_encoding:
                    verifier.msgs.print_info()

            if None != cex:
                print "Found bug"
                verifier.print_cex(cex, True, True)

                #     verifier.debug_cex(cex)
            else:
                print "No bugs found up to %d steps" % (depth)
        elif (opts.mode == "to-smv"):
            with open(opts.smvfile, 'w') as smvfile:
                verifier.to_smv(smvfile)
                smvfile.close()
        else:
            assert False

    elif (opts.mode == "check-files"):
        if (opts.tracefile):
            if (not os.path.exists(opts.tracefile)):
                usage("Trace file %s does not exists!" % opts.tracefile)
            with open(opts.tracefile, "r") as infile:
                ctrace = CTraceSerializer.read_trace(infile)
            print "Trace file %s read succesfully" % opts.tracefile
        if (opts.specfile):
            spec_file_list = opts.specfile.split(":")
            for f in spec_file_list:
                print "Checking %s " % f
                if (not os.path.exists(f)):
                    usage("Specification file %s does not exists!" % f)
            specs_map = read_from_files(spec_file_list)

            print "Spec file %s read succesfully" % opts.specfile
    elif (opts.mode == "print-trace"):
        if (not opts.tracefile): usage("Missing trace file (-t)")
        if (not os.path.exists(opts.tracefile)):
            usage("Trace file %s does not exists!" % opts.tracefile)

        with open(opts.tracefile, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)

        if (opts.specfile):
            if (not os.path.exists(opts.specfile)):
                usage("Spec file %s does not exists!" % opts.specfile)
            with open(opts.specfile, "r") as infile:
                specs_map = SpecSerializer.read_specs(infile)

            ctrace.rename_trace(specs_map["mappings"], True)

        ctrace.print_trace()




if __name__ == '__main__':
    main()
