# todo: more extensive documentation

import unittest
from collections import namedtuple
from itertools import chain, combinations_with_replacement


class DFA:
    def __init__(self, q0, delta, F):
        self.q0 = q0
        self.delta = delta
        self.F = F

    def __repr__(self):
        return f'DFA(q0={self.q0}, delta={self.delta}, F={self.F}'

    def accepts(self, word):
        current_state = self.q0
        for ch in word:
            if (current_state, ch) not in self.delta:
                return False
            current_state = self.delta[current_state, ch]
        return (current_state in self.F)

    def rejects(self, word):
        return not self.accepts(word)


class TestDFAMethods(unittest.TestCase):
    def setUp(self):
        q0 = 0
        F = {1}
        delta = {(0, 'a'): 1, (1, 'a'): 0}
        self.dfa = DFA(q0, delta, F)
        self.should_accept = ['a', 'aaa']
        self.should_reject = ['', 'aa', 'b', 'ab']

    def test_accepts_and_rejects(self):
        for word in self.should_accept:
            self.assertTrue(self.dfa.accepts(word), f"{word} not accepted"
                            f" by {self.dfa} despite being in its language")
            self.assertFalse(self.dfa.rejects(word), f"{word} rejected"
                             f" by {self.dfa} despite being in its language")
        for word in self.should_reject:
            self.assertFalse(self.dfa.accepts(word), f"{word} accepted by"
                             f" {self.dfa} despite not being in its language")
            self.assertTrue(self.dfa.rejects(word), f"{word} not rejected by"
                            f" {self.dfa} despite being in its language")


class NFA:  # supports epsilon transitions
    def __init__(self, q0, delta, F):
        self.q0 = q0
        self.delta = delta
        self.F = F

    def __repr__(self):
        return f'NFA(q0={self.q0}, delta={self.delta}, F={self.F}'

    def Delta(self, states, ch):
        '''
        An extention of delta to a set function on states.
        '''
        result = set()
        for q in states:
            result.update(self.delta.get((q, ch), set()))
        return result

    def _epsilon_closure(self, states):
        result = set()
        new_states = states
        while new_states:
            result.update(new_states)
            new_states = self.Delta(new_states, '') - result
        return result

    def accepts(self, word):
        current_state_set = self._epsilon_closure({self.q0})
        for ch in word:
            current_state_set = self.Delta(current_state_set, ch)
            current_state_set = self._epsilon_closure(current_state_set)
        return bool(current_state_set & self.F)

    def rejects(self, word):
        return not self.accepts(word)


class TestNFAMethods(unittest.TestCase):
    def setUp(self):
        TestInput = namedtuple('TestData', 'nfa should_accept should_reject')
        self.test_inputs = []

        nfa = NFA(q0=0,
                  delta={(0, 'a'): {1, 3}, (0, 'b'): {7}, (1, 'b'): {2},
                         (2, 'c'): {6}, (3, 'a'): {5}, (3, 'b'): {4},
                         (5, 'a'): {4}},
                  F={2, 5})
        should_accept = ['ab', 'aa']
        should_reject = ['abc', 'a', 'b', 'bbbbbb', 'aab', 'aaaaaaabc', 'aaa']
        test_input = TestInput(nfa=nfa, should_accept=should_accept,
                               should_reject=should_reject)
        self.test_inputs.append(test_input)

        nfa = NFA(q0=0,
                  delta={(0, ''): {1, 2}, (1, 'a'): {3}, (2, 'b'): {3}},
                  F={3})
        should_accept = ['a', 'b']
        should_reject = ['ab', 'aa', 'bba']
        test_input = TestInput(nfa=nfa, should_accept=should_accept,
                               should_reject=should_reject)
        self.test_inputs.append(test_input)

        nfa = NFA(q0=0,
                  delta={(0, ''): {1, 2}, (1, 'a'): {1, 3}, (2, ''): {3},
                         (3, 'c'): {4}},
                  F={3, 4})
        should_accept = ['a', 'aa', 'c', 'ac', 'aac']
        should_reject = ['b', 'ab', 'bba', 'ca']
        test_input = TestInput(nfa=nfa, should_accept=should_accept,
                               should_reject=should_reject)
        self.test_inputs.append(test_input)

    def test_Delta(self):
        # todo: write test
        pass

    def test_accepts_and_rejects(self):
        for nfa, should_accept, should_reject in self.test_inputs:
            for word in should_accept:
                self.assertTrue(nfa.accepts(word), f"{word} not accepted by"
                                f" {nfa} despite being in its language")
                self.assertFalse(nfa.rejects(word), f"{word} rejected by"
                                 f" {nfa} despite being in its language")
            for word in should_reject:
                self.assertFalse(nfa.accepts(word), f"{word} accepted by"
                                 f" {nfa} despite not being in its language")
                self.assertTrue(nfa.rejects(word), f"{word} not rejected by"
                                f" {nfa} despite not being in its language")


def NFA_to_DFA(nfa):
    def NFA_to_eps_free_NFA(nfa):
        new_q0 = nfa.q0
        other_start_states = nfa._epsilon_closure({nfa.q0}) - {nfa.q0}
        new_delta = {}
        for (q, ch), R in nfa.delta.items():
            if ch == '':
                continue
            R = nfa._epsilon_closure(R)
            new_delta.setdefault((q, ch), set()).update(R)
            if q in other_start_states:
                new_delta.setdefault((new_q0, ch), set()).update(R)
        new_F = nfa.F
        if new_F & other_start_states:
            new_F.add(new_q0)
        return NFA(new_q0, new_delta, new_F)

    def eps_free_NFA_to_DFA(nfa):
        # The classical subset construction
        alphabet = set(ch for _, ch in nfa.delta)
        assert '' not in alphabet
        state_counter = 0
        new_q0 = state_counter
        new_states = {state_counter: {nfa.q0}}
        state_counter += 1
        new_delta = {}
        work_set = {new_q0}
        while work_set:
            q = work_set.pop()
            state_set = new_states[q]
            for ch in alphabet:
                next_state_set = nfa.Delta(state_set, ch)
                if not next_state_set:
                    continue
                if next_state_set in new_states.values():
                    next_q = {r for r in new_states
                              if new_states[r] == next_state_set}.pop()
                else:
                    next_q = state_counter
                    new_states[state_counter] = next_state_set
                    state_counter += 1
                    work_set.add(next_q)
                assert (q, ch) not in new_delta
                new_delta[q, ch] = next_q
        new_F = set()
        for q in new_states:
            if new_states[q] & nfa.F:
                new_F.add(q)
        return DFA(new_q0, new_delta, new_F)

    return eps_free_NFA_to_DFA(NFA_to_eps_free_NFA(nfa))


class TestFunction_nfa_to_dfa(unittest.TestCase):
    def setUp(self):
        self.test_inputs = []

        nfa = NFA(q0=0,
                  delta={(0, ''): {1, 2}, (1, 'a'): {1, 3}, (2, ''): {3},
                         (3, 'c'): {4}},
                  F={3, 4})
        self.test_inputs.append(nfa)

        nfa = NFA(q0=1,
                  delta={(1, ''): {3}, (1, '0'): {2}, (2, '1'): {2, 4},
                         (3, ''): {2}, (3, '0'): {4}, (4, '0'): {3}},
                  F={3, 4})
        self.test_inputs.append(nfa)

    # todo: add meaningful error messages
    def test_for_equivalence(self):
        for nfa in self.test_inputs:
            dfa = NFA_to_DFA(nfa)
            length_bound = 5
            combs = chain.from_iterable(
                        combinations_with_replacement('abc01', l)
                        for l in range(length_bound))
            for comb in combs:
                word = ''.join(comb)
                nfa_accepts = nfa.accepts(word)
                dfa_accepts = dfa.accepts(word)
                self.assertEqual(nfa_accepts, dfa_accepts,
                                 f"d={dfa} should be equivalent to n={nfa},"
                                 f" but only one of them accepts w={word!r}:\n"
                                 f"\tn.accepts(w) == {nfa_accepts}, "
                                 f"d.accepts(w) == {dfa_accepts}")
                nfa_rejects = nfa.rejects(word)
                dfa_rejects = dfa.rejects(word)
                self.assertEqual(nfa_rejects, dfa_rejects,
                                 f"d={dfa} should be equivalent to n={nfa},"
                                 f" but only one of them rejects w={word!r}:\n"
                                 f"\tn.rejects(w) == {nfa_rejects},"
                                 f"d.rejects(w) == {dfa_rejects}")
