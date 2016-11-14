""" Finite-state automata with symbolic lables.

The class implements a finite-state automaton that represents a
regular language. The represention of letters on the transition is
symbolic and not explicit, allowing for a more concise representation.

The class implements the following functionalities:
1. Represent the automaton with symbolic labels (propositional logic formulas)
2. Iterate the automaton
3. Print the automaton in dot format for inspection
4. Determinize the automaton
5. Build an automaton from a regular espression

The implemeted algorithms are described in:

Alessandro Cimatti, Sergio Mover, Marco Roveri, Stefano Tonetta:
From Sequential Extended Regular Expressions to NFA with Symbolic Labels. CIAA 2010: 87-94

and in the Sergio Mover's master thesis www.sergiomover.eu/paper/master_thesis.pdf
(here there is a pseudocode of the algorithms)

"""

from abc import ABCMeta

from pysmt.environment import reset_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL


auto_env = None

class AutoEnv(object):
    """ Environment used by the automaton class """
    def __init__(self):
        # sat solver instance
        assert False
        self.sat_solver = None
        self.bdd_package = None

    @staticmethod
    def get_global_auto_env():
        auto_env = AutoEnv()
        return auto_env


class Automaton(object):
    def __init__(self):
        # state ids start from 0
        self.current_id = -1
        self.states = set()
        # map from an id to a list of ids
        self.trans = {}
        self.initial_states = set()
        self.final_states = set()


    def _add_new_state(self, is_initial=False, is_final=False):
        """ Add a new state to the automaton """
        return self._add_state(self.current_id + 1, is_initial, is_final)

    def _add_state(self, state_id, is_initial=False, is_final=False):
        """ Add a new state to the automaton """

        assert state_id not in self.states
        if state_id >= self.current_id:
            self.current_id = state_id + 1

        self.states.add(state_id)
        self.trans[state_id] = []

        if is_initial:
            self.initial_states.add(state_id)
        if is_final:
            self.final_states.add(state_id)

        return state_id

    def _add_trans(self, src, dst, label):
        """ Add a transition """
        self.trans[src].append((dst,label))

    def is_initial(self, state):
        return state in self.final_states.contains

    def is_final(self, state):
        return state in self.final_states.contains

    def copy_reachable(self):
        """ Copy the reachable state of self in a new automaton """

        copy = Automaton()

        stack = []
        visited = set()

        for s in self.initial_states:
            copy._add_state(s, self.is_initial(s), self.is_final(s))
            stack.append(s)

        while (len(stack) == 0):
            s = stack.pop()

            for (dst, label) in self.trans[s]:
                if (dst not in visited):
                    copy._add_state(dst, self.is_initial(dst), self.is_final(dst))
                    stack.append(dst)
                trans = self.trans[s]
                trans.append((dst,label))

        return copy


    def concatenate(self, other):
        """ Returns the automaton that recognize the concatenation
        of the language of self with the language of other_auto
        """

        # copy the other automaton
        new_auto = other.get_reachable()
        new_auto.initial_states = set()

        stack = []
        visited = set()
        self_to_new = {}

        for s in self.initial_states:
            new_s = copy._add_new_state(s, self.is_initial(s), self.is_final(s))
            self_to_new[s] = new_s
            stack.append(s)

        while (len(stack) == 0):
            s = stack.pop()
            new_s = self_to_new[s]
            trans = self.trans[new_s]

            # copy the transitions
            for (dst, label) in self.trans[s]:
                if (dst not in visited):
                    new_dst = copy._add_new_state(dst, self.is_initial(dst), False)
                    self_to_new[dst] = new_dst
                    stack.append(dst)
                else:
                    new_dst = self_to_new[dst]
                trans.append((new_dst,label))

            # add transition from final state to all the states
            # reachable from an initial state  in other
            if (self.is_final(s)):
                for other_init in other.initial_states:
                    for (other_dst, other_label) in other.trans[other_init]:
                        trans.append((other_dst, other_label))

        return new_auto


    def klenee_star(self):
        """ Returns the automaton that recognize the kleene
        star operation applied to self.
        """
        # copy the other automaton
        new_auto = self.get_reachable()

        for final in new_auto.final_states:
            trans = new_auto.transp[final]
            for initial in new_auto.initial_states:
                for (dst, label) in new_auto.trans[initial]:
                    trans.append((dst, label))

        return new_auto


    def determinize(self):
        """ Return a DFA that recognizes the same language of self"""
        return NotImplemented


    def to_dot(self, stream):
        stream.write("digraph {\n  " \
                     "center=true;\n" \
                     "edge [fontname=\"Courier\", fontsize=10];\n" \
                     "init [shape=plaintext,label=\"\"]")

        for s in self.initial_states:
            stream.write("init -> node_%d\n" % s)
        for s in self.final_states:
            stream.write("node_%d [shape = doublecircle] " \
                         "[label = \"%d\"]\n" % (s,s))

        for (src,pair) in self.trans.iteritems():
            (dst, label) = pair
            stream.write("node_%d -> node_%d [label = \"%s\"]\n" % (src, dst, str(label)))
        stream.write("}")
        stream.flush()


class Label(object):
    """ Represent a lable of the automaton.
    The class is abstract.

    NOTE: labels should be immutable once created
    """
    __metaclass__ = ABCMeta

    def intersect(self, other): return NotImplemented
    def complement(self): return NotImplemented
    def union(self, other): return NotImplemented

    def is_sat(self): return NotImplemented
    def is_valid(self): return NotImplemented

    def is_contained(self, other_label): return NotImplemented
    def is_intersecting(self, other_label): return NotImplemented


class SatLabel(Label):
    """ Represent a label with propositional formula and use a SAT
    solver to perform semantic checks.
    """
    def __init__(self, formula, env=AutoEnv.get_global_auto_env):
        self.solver = env.sat_solver
        self.formula = formula

    def intersect(self, other):
        return And(self.get_formula(), other.get_formula())

    def complement(self):
        return Not(self.get_formula())

    def union(self):
        return Or(self.get_formula(), other.get_formula())

    def is_sat(self):
        self.solver.is_sat(self.get_formula())

    def is_valid(self):
        self.solver.is_valid(self.get_formula())

    def is_contained(self, other):
        self.solver.is_sat(Implies(self.get_formula(),
                                   other.get_formula()))

    def is_intersecting(self, other_label):
        self.solver.is_sat(And(self.get_formula(),
                               other.get_formula()))

    def get_formula(self):
        return self.formula
