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

from counting.spec import SpecType, Spec, SpecStatus
from ctrace import ConcreteTrace

class Verifier:
    def __init__(self, ctrace, specs):
        # concrete trace
        self.ctrace = ctrace
        # specification (list of rules)
        self.specs = specs

        # internal representation of the transition
        # system
        self.ts_vars = None
        self.ts_trans = None

        # Initialize the transition system
        self._init_ts()
        

    def _init_ts(self):
        """Initialize ts_vars and ts_trans."""
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
