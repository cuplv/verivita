""" Performs the runtime verification.
"""

import sys
import os
import optparse
import logging


from spec import SpecType, SpecSerializer, Spec

from ctrace import CTraceSerializer, ConcreteTrace
from verifier import Verifier

def main():
    # Common to all modes
    logging.basicConfig(level=logging.INFO)

    p = optparse.OptionParser()
    p.add_option('-t', '--tracefile',
                 help="File containing the concrete trace")
    p.add_option('-s', '--specfile', help="Specification file")
    p.add_option('-k', '--depth', help="Depth of the search")
    p.add_option('-d', '--debugenc', action="store_true",
                 default=False,help="Use the debug encoding")

    p.add_option('-m', '--mode', type='choice',
                 choices= ["bmc","check-files"],
                 help="bmc: run bmc on the trace." \
                 "check-files: check if the input files are well formed.",
                 default = "bmc")

    def usage(msg=""):
        if msg: print "----%s----\n" % msg
        p.print_help()
        sys.exit(1)

    opts, args = p.parse_args()

    if (opts.mode == "bmc"):
        if (not opts.tracefile): usage("Missing trace file (-t)")
        if (not opts.specfile): usage("Missing specification file (-s)")
        if (not opts.depth): usage("Missing BMC depth")

        if (not os.path.exists(opts.tracefile)):
            usage("Trace file %s does not exists!" % opts.tracefile)
        if (not os.path.exists(opts.specfile)):
            usage("Specification file %s does not exists!" % opts.specfile)
        try:
            depth = int(opts.depth)
        except:
            usage("%s must be a natural number!" % opts.depth)
        if (depth < 0): usage("%s must be positive!" % opts.depth)

        # Parse the trace file
        with open(opts.tracefile, "r") as infile:
            ctrace = CTraceSerializer.read_trace(infile)

        # Parse the specification file
        with open(opts.specfile, "r") as infile:
            specs_map = SpecSerializer.read_specs(infile)

        # Call the verifier
        verifier = Verifier(ctrace, specs_map["specs"],
                            specs_map["bindings"],
                            opts.debugenc)
        cex = verifier.find_bug(depth)

        if None != cex:
            verifier.print_cex(cex, False)
            if (opts.debugenc):
                verifier.debug_cex(cex)
        else:
            print "No bugs found up to %d steps" % (depth)


    elif (opts.mode == "check-files"):
        if (opts.tracefile):
            if (not os.path.exists(opts.tracefile)):
                usage("Trace file %s does not exists!" % opts.tracefile)
            with open(opts.tracefile, "r") as infile:
                ctrace = CTraceSerializer.read_trace(infile)
            print "Trace file %s read succesfully" % opts.tracefile
        if (opts.specfile):
            if (not os.path.exists(opts.specfile)):
                usage("Spec file %s does not exists!" % opts.specfile)
            with open(opts.specfile, "r") as infile:
                specs = SpecSerializer.read_specs(infile)
            print "Spec file %s read succesfully" % opts.specfile



if __name__ == '__main__':
    main()
