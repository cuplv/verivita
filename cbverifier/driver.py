""" Performs the runtime verification.
"""

import sys
import os
import optparse
import logging


from cbverifier.traces.ctrace import CTraceSerializer
from cbverifier.specs.spec import Spec
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.bmc.bmc import BMC


def main(input_args=None):
    # Common to all modes
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    p = optparse.OptionParser()
    p.add_option('-t', '--tracefile',
                 help="File containing the concrete trace (protobuf format)")

    p.add_option('-f', '--traceformat', type='choice',
                 choices= ["bin","json"],
                 help="Choose between the binary and json proto formats (default bin)",
                 default = "bin")

    p.add_option('-s', '--specfile', help="Colon (:) seperated list" \
                 "of specifications.")

    # Encoding options
    p.add_option('-c', '--enc_coi', action="store_true",
                 default=False, help="Apply cone of influence")

    p.add_option('-d', '--debugenc', action="store_true",
                 default=False,help="Use the debug encoding")

    p.add_option('-m', '--mode', type='choice',
                 choices= ["bmc","check-files","to-smv"],
                 help=('bmc: run bmc on the trace; '
                       'check-files: check if the input files are well formed and prints them; ' 
                       'to-smv: prints the SMV file of the generated transition system.'),
                 default = "bmc")

    # Bmc options
    p.add_option('-k', '--bmc_depth', help="Depth of the search")
    p.add_option('-i', '--bmc_inc', action="store_true",
                 default=False, help="Incremental search")

    p.add_option('-o', '--smv_file', help="Output smv file")


    def usage(msg=""):
        if msg: print "----%s----\n" % msg
        p.print_help()
        sys.exit(1)

    if (input_args is None):
        input_args = sys.argv[1:]
    opts, args = p.parse_args(input_args)

    if (not opts.tracefile): usage("Missing trace file (-t)")
    if (not os.path.exists(opts.tracefile)):
        usage("Trace file %s does not exists!" % opts.tracefile)
    if (not opts.specfile): usage("Missing specification file (-s)")

    spec_file_list = opts.specfile.split(":")
    for f in spec_file_list:
        if (not os.path.exists(f)):
            usage("Specification file %s does not exists!" % f)

    if (opts.mode == "bmc"):
        if (not opts.bmc_depth): usage("Missing BMC depth")
        try:
            depth = int(opts.bmc_depth)
        except:
            usage("%s must be a natural number!" % opts.bmc_depth)
        if (depth < 0): usage("%s must be positive!" % opts.bmc_depth)
    else:
        bmc_opt = [(opts.bmc_depth, "--bmc_depth"),
                   (opts.bmc_inc, "--bmc_inc")]
        for (opt, desc) in bmc_opt:
            if opt:
                usage("%s options cannot use in mode %s\n" % (desc, opts.mode))

    if (opts.mode == "--smv_file"):
        if (not opts.smv_file): usage("Destination smv file not specified!")
        usage("SMV translation still not implemented")
    else:
        if opts.smv_file:
            usage("%s options cannot use in mode " % ("", opts.mode))



    # Parse the trace
    try:
        trace = CTraceSerializer.read_trace_file_name(opts.tracefile,
                                                      opts.traceformat == "json")
    except IOError as e:
        print("An error happened reading the trace in %s" % opts.tracefile)
        sys.exit(1)

    # Parse the specs
    spec_list = Spec.get_specs_from_files(spec_file_list)

    if (opts.mode == "check-files"):

        sys.stdout.write("SPECIFICATIONS:\n")
        for spec in spec_list:
            spec.print_spec(sys.stdout)

        sys.stdout.write("\nTRACE:\n")
        trace.print_trace(sys.stdout)
        sys.stdout.write("\n")

        return 0

    elif (opts.mode == "bmc"):
        ts_enc = TSEncoder(trace, spec_list)

        bmc = BMC(ts_enc.helper,
                  ts_enc.get_ts_encoding(),
                  ts_enc.error_prop)
        cex = bmc.find_bug(depth)

        if (cex is not None):
            printer = CexPrinter(ts_enc.mapback, cex, sys.stdout)
            printer.print_cex()
        else:
            print "No bugs found up to %d steps" % (depth)

        return 0
    elif (opts.mode == "to_smv"):
        assert False

        return 1

        # # Call the verifier
        # verifier = Verifier(ctrace, specs_map["specs"],
        #                     specs_map["bindings"],
        #                     opts.debugenc,
        #                     opts.coi)
        # if (opts.mode == "bmc"):
        #     try:
        #         if (not opts.inc):
        #             cex = verifier.find_bug(depth)
        #         else:
        #             cex = verifier.find_bug_inc(depth)
        #     finally:
        #         if (logging.getLogger().getEffectiveLevel() >= logging.INFO):
        #             ctrace.print_trace()
        #             if verifier.debug_encoding:
        #                 verifier.msgs.print_info()

        #     if None != cex:
        #         print "Found bug"
        #         printer = EventCexPrinter(verifier, cex)
        #         printer.print_cex(True, True)
        #     else:
        #         print "No bugs found up to %d steps" % (depth)

        # elif (opts.mode == "to-smv"):
        #     with open(opts.smv_file, 'w') as smvfile:
        #         verifier.to_smv(smvfile)
        #         smvfile.close()
        # else:
        #     assert False




if __name__ == '__main__':
    main()
