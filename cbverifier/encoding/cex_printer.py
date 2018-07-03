""" Utility used to print a counterexample.

"""

import sys
import collections
import logging

from cbverifier.specs.spec import Spec
from cbverifier.traces.ctrace import CTrace, CValue, CCallin, CCallback
from cbverifier.encoding.encoder import TSMapback
from cbverifier.encoding.encoder_utils import EncoderUtils


class CexPrinter:
    """ Base class used to print a cex.
    """

    def __init__(self, mapback, cex, out_stream=None, print_orig_spec=False):
        self._mapback = mapback

        assert cex is not None
        self._cex = cex
        if (None == out_stream):
            self.out_stream = sys.stdout
        else:
            self.out_stream = out_stream
        self.print_orig_spec = print_orig_spec

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


    def _print_state(self, step, i):
        """ Print the state of the system
        Useful for debug, not user friendly"""

        self._print_sep()
        self.out_stream.write("State: %d\n" % i)
        self._print_sep()

        for s in self._mapback.state_vars:
            assert s in step
            s_val = step[s]
            self.out_stream.write("  %s := %s\n" %  (s, s_val))

        if (i < (len(self._cex)-1)):
            s = self._mapback.msg_ivar
            s_val = self._mapback._get_pc_value(s, step)
            readable = self._mapback.get_trans_label(step)
            self.out_stream.write("  %s := %s (%s)\n" %  (s, s_val, readable))

            s = self._mapback.pc_var
            s_val = self._mapback._get_pc_value(s, step)
            self.out_stream.write("  %s := %s\n" %  (s, s_val))


    def print_cex(self):
        """ Print the cex. """

        self._print_cex_header()

        i = 0
        prev_step = None
        for step in self._cex:
            if (logging.getLogger().getEffectiveLevel() == logging.DEBUG):
                self._print_state(step, i)

            if (i == 0):
                if (self._mapback.is_error(step)):
                    # TODO: add precise list of callins that end in error
                    self._print_error(i, [])
            else:
                self._print_step_header(i)
                val = self._mapback.get_fired_trace_msg(prev_step, step)

                if (type(val) == tuple):
                    (is_entry, trace_msg) = val
                else:
                    is_entry = None
                    trace_msg = val

                assert trace_msg is not None
                msg = self._mapback.get_trans_label(prev_step)
                assert msg is not None

                #self.out_stream.write("%d) msg: %s\n" % (i, msg))
                if (isinstance(trace_msg, str)):
                    self.out_stream.write("[-] %s transition ---\n" % trace_msg)
                else:
                   if (is_entry == EncoderUtils.ENTRY):
                       trace_msg._print_entry(self.out_stream, "", False)
                   else:
                       trace_msg._print_exit(self.out_stream, "", False)

                # trace_desc = trace_msg.to_str()
                # self.out_stream.write("From trace: %s\n" % trace_desc)

                fired_specs = self._mapback.get_fired_spec(prev_step, step, True)
                if len(fired_specs) > 0:
                    sep = "    "
                    self.out_stream.write("%sMatched specifications:\n" % sep)
                    for s in fired_specs:
                        (ground, spec) = s
                        self.out_stream.write(sep)
                        ground.print_spec(self.out_stream)
                        self.out_stream.write("\n")

                        if self.print_orig_spec:
                            self.out_stream.write("%s%sGrounded from the spec:\n" % (sep,sep))
                            self.out_stream.write("%s%s" % (sep,sep))
                            spec.print_spec(self.out_stream)
                            self.out_stream.write("\n")


                if (self._mapback.is_error(step)):
                    # TODO: add precise list of callins that end in error
                    self._print_error(i, [])

                self._print_sep()

            prev_step = step
            i = i + 1

        self.out_stream.flush()

