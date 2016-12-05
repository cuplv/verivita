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

from pysmt.environment import reset_env, get_env
from pysmt.typing import BOOL
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

import pysmt.operators as op
from pysmt.shortcuts import Solver
from pysmt.shortcuts import simplify
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL



class AutoEnv(object):
    """ Environment used by the automaton class

    It hides the implementation details (e.g. SAT or BDD labels?)
    It keeps a unique environment for formulas.

    """

    auto_env = None

    def __init__(self, pysmt_env = None):

        if pysmt_env is None:
            self.pysmt_env = get_env()
        else:
            self.pysmt_env = pysmt_env

        # sat solver instance
        # For now use z3, we can switch to picosat if needed
        self.sat_solver = self.pysmt_env.factory.Solver(quantified=False,
                                                        name="z3",
                                                        logic=QF_BOOL)
        # TODO: add the bdd type of labels.
        # With our problem bdds should not explode and be fairly
        # efficient
        self.bdd_package = None

    def new_label(self, formula):
        # assume SAT labels
        # Here we can do memoization baed on the formula
        return SatLabel(formula)

    @staticmethod
    def get_global_auto_env():
        if AutoEnv.auto_env is None:
            AutoEnv.auto_env = AutoEnv()
        return AutoEnv.auto_env


class Automaton(object):
    def __init__(self, env=None):
        if env is None:
            self.env = AutoEnv.get_global_auto_env()
        else:
            self.env = env

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
            self.current_id = state_id

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
        return state in self.initial_states

    def is_final(self, state):
        return state in self.final_states

    def count_state(self):
        return len(self.states)

    def copy_reachable(self, copy=None, offset = 0):
        """ Copy the reachable state of self in a new automaton """

        if copy is None:
            copy = Automaton()

        stack = []
        visited = set()

        for s in self.initial_states:
            copy_s = s + offset
            copy._add_state(copy_s, self.is_initial(s), self.is_final(s))

            visited.add(s)
            stack.append(s)

        while (len(stack) != 0):
            s = stack.pop()
            copy_s = s + offset

            for (dst, label) in self.trans[s]:
                copy_dst = dst + offset
                if (dst not in visited):
                    copy._add_state(copy_dst, self.is_initial(dst), self.is_final(dst))
                    visited.add(dst)
                    stack.append(dst)

                trans = copy.trans[copy_s]
                trans.append((copy_dst,label))

        return copy


    def concatenate(self, other):
        """ Returns the automaton that recognize the concatenation
        of the language of self with the language of other_auto

        Algorithm:
          - copy the other automaton, removing its initial states
          -

        """

        # copy the other automaton
        new_auto = other.copy_reachable()
        new_auto.initial_states = set()

        stack = []
        visited = set()
        self_to_new = {}

        # copy in new_auto the initial states of self.
        # If the initial state is final in self, it should not be final in
        # new_auto (the word is accepted only after the concatenation
        for s in self.initial_states:
            new_s = new_auto._add_new_state(True, False)
            self_to_new[s] = new_s
            stack.append(s)

        # copy all self
        while (len(stack) != 0):
            s = stack.pop()
            visited.add(s)
            new_s = self_to_new[s]
            trans = new_auto.trans[new_s]

            # copy the transitions
            for (dst, label) in self.trans[s]:
                if (dst not in visited):
                    new_dst = new_auto._add_new_state(self.is_initial(dst), False)
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

        # corner case - no initial states
        if len(self.initial_states) == 0:
            res = Automaton()
            res._add_new_state(True,True)
            return res

        # copy the other automaton
        new_auto = self.copy_reachable()

        for final in new_auto.final_states:
            trans = new_auto.trans[final]
            for initial in new_auto.initial_states:
                for (dst, label) in new_auto.trans[initial]:
                    # Add a transition from the final state to the
                    # states reached by the initial states
                    trans.append((dst, label))

        # make all the initial also accepting
        for initial in new_auto.initial_states:
            new_auto.final_states.add(initial)

        return new_auto

    def union(self, other):
        """ Returns the automaton that accepts the language accepted
        by the union of self and other.
        """

        new_auto = self.copy_reachable()
        new_auto = other.copy_reachable(new_auto, new_auto.current_id+1)

        new_initial = new_auto._add_new_state(False, False)
        init_is_final = False
        for initial in new_auto.initial_states:
            init_is_final = init_is_final or new_auto.is_final(initial)
            for (dst_state, label) in new_auto.trans[initial]:
                new_auto._add_trans(new_initial, dst_state, label)

        new_auto.initial_states = {new_initial}
        if init_is_final:
            new_auto.final_states.add(new_initial)

        return new_auto

    def intersection(self, other):
        """ Returns the automaton that accepts the language accepted
        by the intersection of self and other.

        Compute A \cap B as \neg (\neg A \cub \neg B)
        """
        self_c = self.complement()
        other_c = other.complement()
        union = self_c.union(other_c)
        self_c = None
        other_c = None
        intersection = union.complement()

        return intersection

    def is_contained(self, other):
        """ Returns true if the language pf self is a.
        subset of the language of other.

        Not efficient.
        """
        neg_other = other.complement()
        res = self.intersection(neg_other)
        neg_other = None
        is_contained = res.is_empty()
        res = None

        return is_contained

    def complement(self):
        """ Returns a new automaton that accepts the complement of
        language accepted by self """

        if (len(self.initial_states) == 0 or len(self.final_states) == 0):
            res = Automaton()
            state_id = res._add_new_state(True,True)
            res._add_trans(state_id, state_id, self.env.new_label(TRUE()))
        else:
            # we need a complete automaton
            res = self.determinize()

            # swap the accepting and non accepting states
            non_accepting = res.states.difference(res.final_states)
            res.final_states = non_accepting

        return res

    def is_empty(self):
        """ Returns true if the language accepted by the automaton is empty.
        """
        if len(self.final_states) == 0:
            return True

        stack = []
        visited = set()
        for s in self.initial_states:
            stack.append(s)

        while (len(stack) != 0):
            s = stack.pop()
            visited.add(s)

            # can reach a final state
            if (self.is_final(s)):
                return False

            for (dst, label) in self.trans[s]:
                if (dst not in visited):
                    stack.append(dst)

        # cannot reach a final state
        return True

    def is_equivalent(self, other):
        """ Returns true iff the language accepted by self is the same
        of the language accepted by other.

        Warning: the implementation is not efficient, but it is ok for
        testing purposes

        Check is_empty(not (self U not (other)))
        """

        self_in_other = self.is_contained(other)
        if self_in_other:
            return other.is_contained(self)
        else:
            return False


    def accept(self, word):
        """ Returns true if self accepts the word.

        Word is a list of models represented as word
        """

        def accept_from(self, state, word):
            """ Returns true if word is accepted from state """

            if (len(word) == 0 and self.is_final(state)):
                return True

            if (len(word) == 0):
                return False

            current_letter = word[0]
            next_word = word[1:]
            accepted = False
            for (dst, label) in self.trans[state]:
                if (current_letter.is_intersecting(label)):
                    accepted = accepted or accept_from(self, dst, next_word)
                    if (accepted):
                        break;

            return accepted

        for s in self.initial_states:
            accepted = accept_from(self, s, word)
            if accepted:
                return True

        return False

    def determinize(self):
        """ Return a DFA that recognizes the same language of self
        (from here on the NFA).

        Implement the subset construction algorithm that uses the
        combination of the symbolic labels.

        The initial state of the DFA init_DFA is given by the set of all the
        initial states of the NFA.

        A state in the DFA is a set of states in the NFA.
        Givena a state q in the DFA, states(q) is the set of all the
        correspondent states in the NFA.

        stack.push(init_dfa)
        while (stack is not empty) {
           q = stack.pop

           for (trans, q'') in _sc_enum_trans(q, states):
             if q'' is new: stack.push(q')
             NFA.add_trans(q, trans, q'')
        }

        """

        dfa = Automaton()
        sc_map = SubsConsMap()

        is_final = False
        for s in self.initial_states:
            is_final = is_final or self.is_final(s)
        initial_set = frozenset(self.initial_states)
        initial_dfa = dfa._add_new_state(True, is_final)

        if (len(self.initial_states) == 0): return dfa


        sc_map.insert(initial_dfa, initial_set)

        stack = []
        stack.append(initial_dfa)
        while (len(stack) != 0):
            q = stack.pop()

            q_trans = dfa.trans[q]

            q_set = sc_map.lookup_set(q)
            next_trans = self._sc_enum_trans(q_set)
            for (nfa_states, comb_label) in next_trans:
                q_next = sc_map.lookup_state(nfa_states)

                if (None == q_next):
                    is_q_next_final = sc_map.is_final(self, nfa_states)
                    q_next = dfa._add_new_state(False, is_q_next_final)
                    sc_map.insert(q_next, nfa_states)
                    stack.append(q_next)

                q_trans.append((q_next, comb_label))

        return dfa

    def _sc_enum_trans(self, q_set):
        """ Given a set of NFA states, the function returns a list of
        possible successors in the DFA.

        The result is a list of pairs, where each pair contains a
        set of states in the NFA and a label.
        """

        # collect the set of labels
        label_to_states = {}
        labels_set = set()
        for q_nfa in q_set:
            for (dst_state, label) in self.trans[q_nfa]:
                try:
                    states_set = label_to_states[label]
                except KeyError:
                    states_set = set()
                    label_to_states[label] = states_set
                states_set.add(dst_state)
                labels_set.add(label)

        labels = list(labels_set) # works on list from now on
        # enumerate the set of the possible outgoing transitions
        trans = Automaton.enum_trans(labels, self.env.sat_solver)

        # construct the list formed by dst_set and labels
        results = []
        for res in trans:
            dst_set = set()
            label_formula = TRUE()
            for i in range(len(res)):

                label_formula = And(label_formula, res[i])
                label_formula = simplify(label_formula)

                if (res[i] == labels[i].get_formula()):
                    # same label, goes to the state with this label
                    dst_set.update(label_to_states[labels[i]])
            results.append((frozenset(dst_set), self.env.new_label(label_formula)))
        return results


    @staticmethod
    def enum_trans(labels, solver):
        """ labels is a list of labels, solver is an instance of a sat
        solver (the procedure is specific for sat, instead of BDDs.

        Returns a list of lists of *formulas*, and not labels
        """

        def _enum_trans_rec(solver, labels, index, results, trail):
            """ WARNING:
            side effects on results and trails
            """
            def _enum_trans_one_side(solver, labels, index, results,
                                     trail, label, negate=False):

                literal = label.get_formula()
                if negate:
                    literal = Not(literal)

                solver.push()
                solver.add_assertion(literal)
                if (solver.solve()):
                    trail.append(literal)
                    _enum_trans_rec(solver, labels, index, results, trail)
                    # side effect on trail, backtrack the trail of assignments
                    trail.pop()
                solver.pop()

            if index < len(labels):
                _enum_trans_one_side(solver, labels, index+1, results,
                                     trail, labels[index])

                _enum_trans_one_side(solver, labels, index+1, results,
                                     trail, labels[index], True)
            else:
                assert index == len(labels)
                # copy the result
                results.append(list(trail))

        results = []
        trail = []
        solver.reset_assertions()
        _enum_trans_rec(solver, labels, 0, results, trail)
        assert len(trail) == 0

        return results


    def to_dot(self, stream):
        stream.write("digraph {\n  " \
                     "center=true;\n" \
                     "edge [fontname=\"Courier\", fontsize=10];\n" \
                     "init [shape=plaintext,label=\"\"]\n")

        for s in self.states:
            if s in self.final_states:
                stream.write("node_%d [shape = doublecircle] " \
                             "[label = \"%d\"]\n" % (s,s))
            else:
                stream.write("node_%d [shape = circle] " \
                             "[label = \"%d\"]\n" % (s,s))
        for s in self.initial_states:
            stream.write("init -> node_%d\n" % s)

        for (src, lst) in self.trans.iteritems():
            for pair in lst:
                (dst, label) = pair
                stream.write("node_%d -> node_%d [label = \"%s\"]\n" % (src, dst, str(label)))
        stream.write("}\n")
        stream.flush()

    @staticmethod
    def get_singleton(label, env=None):
        aut = Automaton(env)
        init = aut._add_new_state(True, False)
        final = aut._add_new_state(False, True)
        aut._add_trans(init, final, label)
        return aut

    @staticmethod
    def get_empty(env=None):
        aut = Automaton(env)
        init = aut._add_new_state(True, False)
        return aut


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

    # subclasses must implement hash and eq
    def __hash__(self): return NotImplemented
    def __eq__(self, other): return NotImplemented

class SatLabel(Label):
    """ Represent a label with propositional formula and use a SAT
    solver to perform semantic checks.
    """
    def __init__(self, formula, env=None):
        if env is None:
            env = AutoEnv.get_global_auto_env()
        self.env = env
        self.solver = env.sat_solver
        self.formula = formula

    def intersect(self, other):
        if (self.get_formula() == other.get_formula()):
            return self
        if (self.get_formula() == TRUE()):
            return other
        elif (other.get_formula() == TRUE()):
            return self
        else:
            return SatLabel(And(self.get_formula(),
                                other.get_formula()),
                            self.env)

    def complement(self):
        return SatLabel(Not(self.get_formula()), self.env)

    def union(self, other):
        return SatLabel(Or(self.get_formula(), other.get_formula()),
                        self.env)

    def is_sat(self):
        return self.solver.is_sat(self.get_formula())

    def is_valid(self):
        return self.solver.is_valid(self.get_formula())

    def is_contained(self, other):
        return self.solver.is_valid(Implies(self.get_formula(),
                                            other.get_formula()))

    def is_intersecting(self, other):
        return self.solver.is_sat(And(self.get_formula(),
                                      other.get_formula()))

    def get_formula(self):
        return self.formula

    def __repr__(self):
        return str(self.formula)

    def __hash__(self):
        return hash(self.formula)

    def __eq__(self, other):
        return self.formula == other.formula


class SubsConsMap:
    def __init__(self):
        # Map from a set of states of the NFA to a single state of the
        # DFA
        self.nfa_to_dfa = {}
        # Map from a state of the DFA to a set of states in the NFA
        self.dfa_to_nfa = {}

    def insert(self, dfa_state, nfa_states):
        self.nfa_to_dfa[nfa_states] = dfa_state
        self.dfa_to_nfa[dfa_state] = nfa_states

    def lookup_set(self, dfa_states):
        try:
            return self.dfa_to_nfa[dfa_states]
        except KeyError:
            return None

    def lookup_state(self, nfa_states):
        try:
            return self.nfa_to_dfa[nfa_states]
        except KeyError:
            return None

    def is_final(self, nfa, nfa_states):
        return not nfa_states.isdisjoint(nfa.final_states)

