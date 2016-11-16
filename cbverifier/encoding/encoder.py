""" Encode and solve the verification problem

The input are:
  - a concrete trace
  - a specification

The verifier finds a possible (spurious) permutation of the events in
the concrete trace that may cause a bug (a bug arises a disabled
callin is called).

The possible permutation of the events depend on the enabled/disabled
status of events/callins.



PLAN:
  a. compute the ground specifications
    - TEST
  b. create the symbolic automata for the specifications
    - TEST
  b. create the encoding for the event transitions
  We cannot statically encode the effect of each callback and
  callin, since it depends on the whole history, and not on the
  callin/callback that we are computing.
  Hence, we need to encode one callin/callback per step and let the
  model checker figure out the state of the system.


OPTIMIZATIONS
The length of the sequence that must be explored can be quite high.
We need to optimize the encoding as much as we can.

Ideas:
  - Cone of influence reduction (harder due to regexp)

  - Merge (union) the regexp automata and reduce the state space
  Same settings of the CIAA 10 for PSL
  (From Sequential Extended Regular Expressions to NFA with Symbolic Labels, CIAA 10)
    - Automata with symbolic labels
    - The size of the alphabet is huge

  - Group the execution of callins and callbacks:
    - If two callin must be executed in sequence and they are
    independent one from each other, then there is no reason to not
    group them togheter.
    TODO: define when two callins and callbacks are independent.

  - Encode a callback and its descendant messages in a single transition
  This is similar to SSA construction

"""

# TODOs:
# - implement pre for the simplification
# - fix encoding (and trace construction) using the simplification

import logging
from cStringIO import StringIO

from pysmt.environment import reset_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
from cbverifier.traces.ctrace import CTrace
from cbverifier.encoding.automata import Automaton, AutoEnv


from cbverifier.helpers import Helper

class TransitionSystem:
    """ (symbolic) Transition system"""
    def __init__(self):
        # internal representation of the transition system
        self.state_vars = set()
        self.input_vars = set()
        self.init = TRUE()
        self.trans = TRUE()

    def product(self, other_ts):
        """ Computes the synchronous product of self with other_ts,
        storing the product in self.

        Given TS1 = <V1, W1, I1, T1> and TS2 = <V2, W2, I2, T2>
        the product is the transition system
        TSP = <V1 union V2, W1 union W2, I1 and I2, T1 and T2>

        (V are the state variables, W the input variables,
        I is the initial condition, T the transition relation)
        """

        self.state_vars.update(other_ts.state_vars)
        self.input_vars.update(other_ts.input_vars)
        self.init = And(self.init, other_ts.init)
        self.trans = And(self.trans, other_ts.trans)


class TSEncoder:
    """
    Encodes the dynamic verification problem in a transition system.

    """

    def __init__(self, trace, specs):
        self.trace = trace
        self.specs = specs
        self.ts = None
        self.error_prop = None

        self.ground_specs = self._compute_ground_spec()
        self.r2a = RegExpToAuto()

    def get_ts_encoding(self):
        """ Returns the transition system encoding of the dynamic
        verification problem.
        """
        if (self.ts is None): self._encode()
        return self.ts


    def _encode(self):
        """ Function that performs the actual encoding of the TS.

        The function performs the following steps:

        """
        self.ts = TransitionSystem()

        # Disjunction of the error states
        self.error_prop = FALSE()

        # Encode the effects of the specifications
        spec_id = 0
        for ground_spec in self.ground_specs:
            (gs_ts, updates) = self._get_ground_spec_ts(ground_spec, spec_id)
            self.ts.product(gs_ts)

        # Encode the callbacks and callins defined in the
        # concrete trace
        #


    def _compute_ground_spec(self):
        """ Computes all the ground specifications from the
        specifications with free variables in self.spec and the
        concrete trace self.trace

        Return a list of ground specifications.
        """

        ground_specs = []

        gs = GroundSpecs(self.trace)

        for spec in self.specs:
            tmp = gs.ground_spec(spec)
            ground_specs.extend(tmp)

        return ground_specs


    def _get_ground_spec_ts(self, ground_spec, spec_id):
        """ Given a ground specification, returns the transition
        system that encodes the updates implied by the specification.

        We apply the same encoding used in:
        Symbolic Compilation of PSL, Cimatti, Roveri, Tonetta, TCAD
        Section 5, subsection A.
        """

        auto = self.r2a.get_from_regexp(ground_spec)
        self._get_auto_ts(auto, spec_id)


        raise Exception("Not implemented")


    def _get_auto_ts(self, auto):
        """ Encodes the automaton auto in a transition system """
        



class RegExpToAuto():
    """ Utility class to convert a regular expression in an automaton.

    TODO: We can implement memoization of the intermediate results

    TODO: all the recursive functions should become iterative

    """
    def __init__(self, auto_env=None):
        if auto_env is None:
            auto_env = AutoEnv.get_global_auto_env()
        self.auto_env = auto_env

    def get_atom_var(self, call_node):
        out = StringIO()
        pretty_print(call_node, out)
        atom_name = out.getvalue()
        return Symbol(atom_name, BOOL)


    def get_from_regexp(self, regexp, env=None):
        node_type = get_node_type(regexp)

        if (node_type in [TRUE,FALSE,CALL,AND_OP,OR_OP,NOT_OP]):
            # base case
            # accept the atoms in the bexp
            formula = self.get_be(regexp)
            label = self.auto_env.new_label(formula)
            automaton = Automaton.get_singleton(label)
            return automaton
        elif (node_type == SEQ_OP):
            lhs = self.get_from_regexp(regexp[1])
            rhs = self.get_from_regexp(regexp[2])
            automaton = lhs.concatenate(rhs)
            lhs = None
            rhs = None
            return automaton
        elif (node_type == STAR_OP):
            lhs = self.get_from_regexp(regexp[1])
            automaton = lhs.klenee_star()
            lhs = None
            return automaton
        else:
            # Should not see them, the boolean atoms are the CALLS node
            # ID, INT, FLOAT, PARAM_LIST, NIL, DONTCARE, STRING, VALUE
            #
            # Should not even see the higher level nodes:
            # SPEC_SYMB
            # ENABLE_OP
            # DISABLE_OP
            # SPEC_LIST
            raise UnexpectedSymbol(regexp)

    def get_be(self, be_node):
        """ Given a node that represent a Boolean expression returns
        the correspondent formula in PySMT """
        node_type = get_node_type(be_node)

        if (node_type == TRUE):
            return TRUE()
        elif (node_type == FALSE):
            return FALSE()
        elif (node_type == CALL):
            # generate a boolean atom for the call
            atom_var = self.get_atom_var(be_node)
            return atom_var
        elif (node_type == AND_OP):
            return And(self.get_be(be_node[1]),
                       self.get_be(be_node[2]))
        elif (node_type == OR_OP):
            return Or(self.get_be(be_node[1]),
                      self.get_be(be_node[2]))
        elif (node_type == NOT_OP):
            return Not(self.get_be(be_node[1]))
        else:
            raise UnexpectedSymbol(be_node)

