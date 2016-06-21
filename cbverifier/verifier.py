""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a specification (a set of rules)
  - a bound

The verifier finds a possible (spurious) permutation of the events in
the concrete trace that may cause a bug (a bug arises a disabled
callin is called).

The possible permutation of the events depend on the enabled/disabled
status of events/callins.
"""

from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, Xor

from counting.spec import SpecType, Spec, SpecStatus
from ctrace import ConcreteTrace

class Verifier:
    # 
    ENABLED_VAR_PREF  = "enabled_state"
    ALLOWED_VAR_PREF  = "allowed_state"
    
    def __init__(self, ctrace, specs):
        # concrete trace
        self.ctrace = ctrace
        # specification (list of rules)
        self.specs = specs

        # internal representation of the transition system
        self.ts_vars = None
        self.ts_init = None        
        self.ts_trans = None

        # Initialize the transition system
        self._init_ts()


    def _init_ts(self):
        """Initialize ts_vars and ts_trans."""

        self._init_ts_var()
        self._init_ts_init()        
        self._init_ts_trans()

    def _init_ts_var(self):
        """Initialize the ts variables.

        What are the state variable of the system?

        For each callin "ci" with the concrete object "o" as receiver
        we have a Boolean variable "allowed_state_ci_o".

        For each event "evt" with objects "o1, ..., on" appearing in
        the event's "evt" callbacks, we have a Boolean variable 
        "enabled_state_evt_o1_..._on".
        """

        self.ts_var = []
        
        assert False

    def _init_ts_init(self):
        """Initialize the ts init.

        In the initial state all the events and callins are enabled.
        """
        assert False        

    def _init_ts_trans(self):
        """Initialize the ts trans."""

        # a. Encode each event in the trace
        events_encoding = []
        for evt in self.ctrace.events:
            evt_encoding = self._encode_evt(evt)
            events_encoding.append(evt_encoding)
        
        self.ts_trans = And(spec_encoding)

    def _encode_evt(self, evt):
        """Encode the transition relation of a single event."""
        assert False
        
    def find_bug(self, steps):
        """Explore the system up to k steps.
        Steps correspond to the number of events executed in the
        system.

        Returns None if no bugs where found up to k or a
        counterexample otherwise (a list of events).
        """
        assert False

        #
        return None
