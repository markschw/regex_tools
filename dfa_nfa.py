# review: do i really need this?
''' from itertools import chain, combinations
def powerset(iterable):
    orig_set = set(iterable)
    return set(chain.from_iterable(combinations(orig_set, size)
               for size in range(len(s)+1)))
'''
# todo: more extensive documentation


class DFA:
    def __init__(self, q0, delta, F):
        self.q0 = q0
        self.delta = delta
        self.F = F

    def accepts(self, word):
        current_state = self.q0
        for ch in word:
            if (current_state, ch) not in self.delta:
                return False
            current_state = self.delta[current_state, ch]
        return (current_state in self.F)

    def rejects(self, word):
        return not self.accepts(word)


def test_DFA():
    q0 = 0
    F = {1}
    delta = {(0, 'a'): 1, (1, 'a'): 0}
    dfa = DFA(q0, delta, F)
    assert dfa.rejects('')
    assert dfa.accepts('a')
    assert dfa.rejects('aa')
    assert dfa.accepts('aaa')
    assert dfa.rejects('b')
    assert dfa.rejects('ab')

if __name__ == '__main__':
    print('Testing class DFA...')
    test_DFA()
    print('Test successful!')


class NFA:  # supports epsilon transitions
    def __init__(self, q0, delta, F):
        self.q0 = q0
        self.delta = delta
        self.F = F

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


def test_NFA():
    q0 = 0
    F = {2, 5}
    delta = {(0, 'a'): {1, 3}, (0, 'b'): {7}, (1, 'b'): {2}, (2, 'c'): {6},
             (3, 'a'): {5}, (3, 'b'): {4}, (5, 'a'): {4}}
    nfa = NFA(q0, delta, F)
    assert nfa.accepts('ab')
    assert nfa.accepts('aa')
    assert nfa.rejects('abc')
    assert nfa.rejects('a')
    assert nfa.rejects('b')
    assert nfa.rejects('bbbbbb')
    assert nfa.rejects('aab')
    assert nfa.rejects('aaaaaaabc')
    assert nfa.rejects('aaa')

    q0 = 0
    F = {3}
    delta = {(0, ''): {1, 2}, (1, 'a'): {3}, (2, 'b'): {3}}
    nfa = NFA(q0, delta, F)
    assert nfa.accepts('a')
    assert nfa.accepts('b')
    assert nfa.rejects('ab')
    assert nfa.rejects('aa')
    assert nfa.rejects('bba')

    q0 = 0
    F = {3, 4}
    delta = {(0, ''): {1, 2}, (1, 'a'): {1, 3}, (2, ''): {3}, (3, 'c'): {4}}
    nfa = NFA(q0, delta, F)
    assert nfa.accepts('a')
    assert nfa.rejects('b')
    assert nfa.rejects('ab')
    assert nfa.accepts('aa')
    assert nfa.rejects('bba')
    assert nfa.accepts('c')
    assert nfa.accepts('ac')
    assert nfa.accepts('aac')
    assert nfa.rejects('ca')

if __name__ == '__main__':
    print('Testing class NFA...')
    test_NFA()
    print('Test successful!')

# note: All that follows is incomplete and untested.


def NFA_to_DFA(nfa):
    def NFA_to_eps_free_NFA(nfa):
        # Create an initial state mimicking the epsilon closure of nfa.q0
        new_q0 = nfa.q0
        other_start_states = nfa._epsilon_closure({nfa.q0}) - {nfa.q0}
        new_delta = {}
        for (q, ch), R in nfa.delta.items():
            if ch == '':
                continue
            if q in other_start_states:
                q = new_q0
            R = nfa._epsilon_closure(R)
            if R & other_start_states:
                R = (R - other_start_states) | {new_q0}
            if (q, ch) not in new_delta:
                new_delta[q, ch] = set()
            new_delta[q, ch].update(R)
        new_F = nfa.F
        if new_F & other_start_states:
            new_F = (new_F - other_start_states) | {new_q0}
        return NFA(new_q0, new_delta, new_F)

    # fixme:
    def eps_free_NFA_to_DFA(nfa):
        assert '' not in (ch for _, ch in nfa.delta())
        new_q0 = set(nfa.q0)
        new_delta = {}

        transitions_left = nfa.delta()
        # todo: replace with deque from collections lib
        queue = [key for key in nfa.delta() if key[0] == nfa.q0]
        current_q = nfa.q0
        # while transitions_left:
        #     for q in
        #     (q, ch in nfa.delta() if state)


#       new_delta = { (q_set, ch): set().union( *(self.delta.get((q, ch), {}))
#                     for q in q_set) for q_set in powerset(Q) }
#       new_F = powerset(q for (q, _) in nfa.delta())
#        return NFA(new_q0, new_delta, new_F)

    return eps_free_NFA_to_DFA(NFA_to_eps_free_NFA(nfa))


# todo:
def test_NFA_to_DFA():
    q0 = 0
    F = {3, 4}
    delta = {(0, ''): {1, 2}, (1, 'a'): {1, 3}, (2, ''): {3}, (3, 'c'): {4}}
    nfa = NFA(q0, delta, F)
    print(NFA_to_DFA(nfa))

if __name__ == '__main__':
    print('Testing function NFA_to_DFA(nfa)...')
    test_NFA_to_DFA()
    print('Test successful!')