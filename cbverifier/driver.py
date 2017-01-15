""" Performs the runtime verification.
"""

import sys
import os
import optparse
import logging


from cbverifier.traces.ctrace import CTraceSerializer, CCallin, CCallback, MessageFilter
from cbverifier.specs.spec import Spec
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.bmc.bmc import BMC


class DriverOptions:
    def __init__(self,
                 tracefile,
                 traceformat,
                 spec_file_list,
                 simplify_trace,
                 debug,
                 filter_msgs):
        self.tracefile = tracefile
        self.traceformat = traceformat
        self.spec_file_list = spec_file_list
        self.simplify_trace = simplify_trace
        self.debug = debug
        self.filter_msgs = filter_msgs


class Driver:
    def __init__(self, opts):
        self.opts = opts

        # Parse the trace
        try:
            self.trace = CTraceSerializer.read_trace_file_name(self.opts.tracefile,
                                                               self.opts.traceformat == "json")
        except IOError as e:
            raise Exception("An error happened reading the trace in %s" % self.opts.tracefile)

        # Parse the specs
        self.spec_list = Spec.get_specs_from_files(self.opts.spec_file_list)
        if self.spec_list is None:
            raise Exception("Error parsing the specification file!")


    def check_files(self, stream):
        stream.write("SPECIFICATIONS:\n")
        for spec in self.spec_list:
            spec.print_spec(stream)
            stream.write("\n")

        stream.write("\nTRACE:\n")
        if (self.opts.filter_msgs != None):
            self.trace.print_trace(stream, self.opts.debug,
                              MessageFilter.typeFilterFrom(self.opts.filter_msgs))
        else:
            self.trace.print_trace(stream, self.opts.debug)
        stream.write("\n")

    def get_ground_specs(self):
        ts_enc = TSEncoder(self.trace, self.spec_list)
        ground_specs = ts_enc.get_ground_spec()
        return ground_specs


    def run_bmc(self, depth, inc):
        ts_enc = TSEncoder(self.trace, self.spec_list, self.opts.simplify_trace)

        bmc = BMC(ts_enc.helper,
                  ts_enc.get_ts_encoding(),
                  ts_enc.error_prop)

        cex = bmc.find_bug(depth, inc)

        return (cex, ts_enc.mapback)


def print_ground_spec(ground_specs, out=sys.stdout):
    out.write("List of ground specifications:\n")
    for spec in ground_specs:
        spec.print_spec(out)
        out.write("\n")


def main(input_args=None):
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

    p.add_option('-z', '--simplify_trace', action="store_true",
                 default=False, help="Simplify the trace (possibly unsound)")

    p.add_option('-d', '--debug', action="store_true",
                 default=False,
                 help="Output debug informations")

    p.add_option('-m', '--mode', type='choice',
                 choices= ["bmc","check-files","to-smv","show-ground-specs"],
                 help=('bmc: run bmc on the trace; '
                       'check-files: check if the input files are well formed and prints them; ' 
                       'show-ground-specs: shows the specifications instantiateed by the given trace; ' 
                       'to-smv: prints the SMV file of the generated transition system.'),
                 default = "bmc")

    # Bmc options
    p.add_option('-k', '--bmc_depth', help="Depth of the search")
    p.add_option('-i', '--bmc_inc', action="store_true",
                 default=False, help="Incremental search")

    p.add_option('-o', '--smv_file', help="Output smv file")
    p.add_option('-l', '--filter', help="When running check-files this will only: filter all messages to the ones"
                                        "where type is matched")


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

    if (opts.debug):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    driver_opts = DriverOptions(opts.tracefile,
                                opts.traceformat,
                                spec_file_list,
                                opts.simplify_trace,
                                opts.debug,
                                opts.filter)

    driver = Driver(driver_opts)

    if (opts.mode == "check-files"):
        driver.check_files(sys.stdout)
        return 0

    elif (opts.mode == "show-ground-specs"):
        ground_specs = driver.get_ground_specs()
        print_ground_spec(ground_specs)

    elif (opts.mode == "bmc"):
        (cex, mapback) = driver.run_bmc(depth, opts.bmc_inc)

        if (cex is not None):
            printer = CexPrinter(mapback, cex, sys.stdout)
            printer.print_cex()
        else:
            print "No bugs found up to %d steps" % (depth)

        return 0

    elif (opts.mode == "to_smv"):
        assert False
        return 1



if __name__ == '__main__':
    main()
