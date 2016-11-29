""" Utility used to print a counterexample.

"""

import sys
import collections

from cbverifier.specs.spec import Spec
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.encoder import TSMapback



class CexPrinter:
    """ Base class used to print a cex.
    """

    def __init__(self, mapback, cex, out_stream=None):
        self._mapback = mapback

        assert cex is not None

        self._cex = cex

        if (None == out_stream):
            self.out_stream = sys.stdout
        else:
            self.out_stream = out_stream

    def _print_sep(self):
        sep = "----------------------------------------\n"
        self.out_stream.write(sep)

    def _print_cex_header(self):
        self.out_stream.write("\n         --- Counterexample ---         \n")
        self._print_sep()

    def _print_step_header(self, i):
        self.out_stream.write("Step: %d\n" % i)
        self._print_sep()

    def _print_error(self, step, disabled_ci):
        self.out_stream.write("    Reached an error state in step %d!\n" % step)

    def print_cex(self):
        """ Print the cex. """

        self._print_cex_header()

        i = 0
        prev_step = None
        for step in self._cex:
            if (i == 0):
                if (self._mapback.is_error(step)):
                    # TODO: add precise list of callins that end in error
                    self._print_error(i, [])
            else:
                self._print_step_header(i)

                trace_msg = self._mapback.get_fired_trace_msg(prev_step)
                assert trace_msg is not None
                msg = self._mapback.get_trans_label(prev_step)
                assert msg is not None

                #self.out_stream.write("%d) msg: %s\n" % (i, msg))
                if (isinstance(trace_msg, str)):
                    self.out_stream.write("[-] %s transition ---\n" % trace_msg)
                else:
                    trace_msg._print(self.out_stream, "", False)

                # trace_desc = trace_msg.to_str()
                # self.out_stream.write("From trace: %s\n" % trace_desc)

                fired_specs = self._mapback.get_fired_spec(prev_step, step, True)
                if len(fired_specs) > 0:
                    self.out_stream.write("    Matched specifications:\n")
                    for s in fired_specs:
                        (ground, spec) = s
                        self.out_stream.write("    ")
                        print ground.ast
                        ground.print_spec(self.out_stream)
                        self.out_stream.write("\n")

                if (self._mapback.is_error(step)):
                    # TODO: add precise list of callins that end in error
                    self._print_error(i, [])

                self._print_sep()

            prev_step = step
            i = i + 1

        self.out_stream.flush()

