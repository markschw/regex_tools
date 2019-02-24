'''
Some functions for working with regular expressions, including parsing and
constructing matchers/recognizers (finite-state automata) for them.

Formal grammar for the regex dialect adapted here:
    R    -> Char | RR | R'|'R | R'*' | '('R')'
    Char -> 'a' | ... | 'z' | 'A' | ... | 'Z' | '0' | '1' | ... | '9'
In addition, whitespace may appear anywhere in the regex and
has no semantic meaning (only alphanumeric characters are currently supported)
'''

# todo: handle invalid inputs to functions
# todo: go over documentation

import unittest
from collections import namedtuple
from itertools import count
from dfa_nfa import NFA, NFA_to_DFA


def standardize(regex):
    '''
    Returns a modified regex with all the whitespace removed and
    with explicit concatenations (by inserting '.' where necessary).
    '''
    regex = [ch for ch in regex if not ch.isspace()]
    result = ''
    for i in range(len(regex)):
        result += regex[i]
        if i == len(regex) - 1:
            break
        pattern = ''.join('A' if ch.isalnum() else ch
                          for ch in regex[i:i + 2])
        concatenation_patterns = {'AA', 'A(', '*A', '*(', ')(', ')A'}
        if pattern in concatenation_patterns:
            result += '.'
    return result


class TestFunction_standardize(unittest.TestCase):
    def test_standardize(self):
        param_results = {' a |b c': 'a|b.c',
                         'ab| c ': 'a.b|c',
                         ' ( a * b c * ) *': '(a*.b.c*)*',
                         'd | (a*b |c *)e': 'd|(a*.b|c*).e'}

        for param, result in param_results.items():
            self.assertEqual(standardize(param), result)


def infix_to_prefix(regex):
    '''
    Returns a whitespace-free regex in prefix-form which is
    semantically equivalent to the given regex.
    Formal grammar for prefix-form regexes:
        R    -> Char | '.'RR | '|'RR | '*'R
        Char ->  'a' | ... | 'z' | 'A' | ... | 'Z' | '0' | ... | '9'
    '''
    # A version of Dijkstra's shunting-yard algorithm
    regex = standardize(regex)
    op_stack = []
    result = ''
    for ch in reversed(regex):
        if ch.isspace():
            continue
        if ch.isalnum():
            result += ch
        elif ch == '*':
            op_stack.append(ch)
        elif ch == '.':
            while op_stack and op_stack[-1] == '*':
                result += '*'
                op_stack.pop()
            op_stack.append(ch)
        elif ch == '|':
            while op_stack and op_stack[-1] in '.*':
                result += op_stack[-1]
                op_stack.pop()
            op_stack.append(ch)
        elif ch == ')':
            op_stack.append(ch)
        elif ch == '(':
            assert op_stack
            while op_stack[-1] != ')':
                result += op_stack[-1]
                op_stack.pop()
            op_stack.pop()  # pop the ')'
            if op_stack:
                result += op_stack[-1]
                op_stack.pop()
        else:
            raise ValueError('Given regex contains an invalid character.')
    result += ''.join(reversed(op_stack))
    result = result[::-1]
    return result


class TestFunction_infix_to_prefix(unittest.TestCase):
    def test_infix_to_prefix(self):
        param_results = {'a|b.c': '|a.bc',
                         'a.b|c': '|.abc',
                         '(a*.b.c*)*': '*..*ab*c',
                         'd|(a*.b|c*).e': '|d.|.*ab*ce'}

        for param, result in param_results.items():
            self.assertEqual(infix_to_prefix(param), result)


class Node:
    def __init__(self, data, left, right):
        self.data = data
        self.left = left
        self.right = right

    def __repr__(self):
        return f'Node({self.data}, {self.left}, {self.right})'

    def __str__(self):
        def aux(tree, indent=''):
            result = f'{indent}+- {tree.data!r}'
            if tree.left:
                result += '\n' + aux(tree.left, indent=indent + '|   ')
            if tree.right:
                result += '\n' + aux(tree.right, indent=indent + '|   ')
            return result

        return aux(self)


def construct_parse_tree(regex):
    '''
    Returns a parse tree for a given (infix-form) regex.
    '''
    regex = infix_to_prefix(standardize(regex))

    def construct_branch(tail):
        '''
        Given the suffix of a whitespace-free regex in prefix form,
        this function returns a parse tree for the maximal prefix of
        the input that forms a valid regex, along with the remainder
        of the regex. Thus the return value is a pair (tree, remainder).

        Example: construct_branch('.ab*c') should return the parse tree
                 for '.ab' along with the string '*c'.
        '''
        if tail == '':
            return None, ''
        ch = tail[0]
        if ch.isalnum():
            return Node(ch, None, None), tail[1:]
        elif ch == '*':
            left, remainder = construct_branch(tail[1:])
            return Node(ch, left, None), remainder
        elif ch in '.|':
            left, remainder = construct_branch(tail[1:])
            right, remainder = construct_branch(remainder)
            return Node(ch, left, right), remainder
        else:
            raise ValueError('Given input is not a suffix of a valid regex.')

    tree, _ = construct_branch(regex)
    return tree


# todo: rewrite as an automated test
def test_construct_parse_tree():
    regex = 'd|(a*b|c*)e'
    print('The following should be a parse tree for ' + regex + '...')
    tree = construct_parse_tree(regex)
    print(tree)
    print('Parse tree printed!')

if __name__ == '__main__':
    print('Testing function construct_parse_tree()...')
    test_construct_parse_tree()
    print('Done!')


def to_DOT_format(tree):
    '''
    Returns a string in the DOT format which represents the given tree.
    '''
    def format_branch(tree):
        if tree is None:
            return ''
        # todo: use a counter to label the states instead of node ids.
        sons = format_branch(tree.left) + format_branch(tree.right)
        father = str(id(tree)) + ' [label="' + str(tree.data) + '"];\n'
        edges = ''
        for node in [tree.left, tree.right]:
            if node is not None:
                edges += str(id(tree)) + ' -> ' + str(id(node)) + ';\n'
        return sons + father + edges

    return 'digraph { \n' + format_branch(tree) + '}\n'


# todo: rewrite as an automated test
def test_to_DOT_format():
    regex = 'd|(a*b|c*)e'
    tree = construct_parse_tree(regex)
    print('The following should be a representation of the parse tree of',
          regex, 'in the DOT format...')
    print(to_DOT_format(tree))
    print('DOT-format tree printed!')

if __name__ == '__main__':
    print('Testing function to_DOT_format()...')
    test_to_DOT_format()
    print('Done!')


def construct_matcher(regex):
    id_gen = count()

    def construct_NFA(tree):
        # Thompson's algorithm
        assert tree
        token = tree.data
        if token.isalnum():
            assert(not tree.left and not tree.right)
            q0 = next(id_gen)
            q1 = next(id_gen)
            delta = {(q0, token): {q1}}
            F = {q1}
        elif token == '*':
            assert(tree.left and not tree.right)
            son_nfa = construct_NFA(tree.left)
            q0 = son_nfa.q0
            delta = son_nfa.delta
            for q in son_nfa.F:
                delta.setdefault((q, ''), set()).add(q0)
            F = son_nfa.F | {q0}
        elif token == '.':
            assert(tree.left and tree.right)
            left_nfa = construct_NFA(tree.left)
            right_nfa = construct_NFA(tree.right)
            q0 = left_nfa.q0
            delta = {**left_nfa.delta, **right_nfa.delta}
            for q in left_nfa.F:
                delta.setdefault((q, ''), set()).add(right_nfa.q0)
            F = right_nfa.F
        elif token == '|':
            assert(tree.left and tree.right)
            left_nfa = construct_NFA(tree.left)
            right_nfa = construct_NFA(tree.right)
            q0 = next(id_gen)
            delta = {**left_nfa.delta, **right_nfa.delta}
            delta[q0, ''] = {left_nfa.q0, right_nfa.q0}
            F = left_nfa.F | right_nfa.F
        else:
            assert 0, 'Invalid token found in tree: ' + token
        return NFA(q0, delta, F)

    return NFA_to_DFA(construct_NFA(construct_parse_tree(regex)))


class TestFunction_construct_matcher(unittest.TestCase):
    def setUp(self):
        TestInput = namedtuple('TestInput',
                               'regex should_match should_not_match')
        self.test_inputs = []

        regex = 'd|(a*b|c*)e'
        should_match = ['d', 'e', 'ce', 'ccce', 'be', 'abe', 'aabe']
        should_not_match = ['', 'da', 'dabe' 'dae', 'db', 'de', 'dce', 'a',
                            'ab', 'abc', 'abce', 'ac', 'ace', 'ad', 'ae', 'b',
                            'ba', 'bc', 'bce', 'bd', 'bde', 'ea', 'eb', 'ec',
                            'ed', 'ee', 'cee', 'bee', 'abee', 'aabee']
        test_input = TestInput(regex=regex, should_match=should_match,
                               should_not_match=should_not_match)
        self.test_inputs.append(test_input)

        regex = 'a*b*'
        should_match = ['', 'a', 'aa', 'b', 'bb', 'ab', 'aab', 'abb', 'aabb']
        should_not_match = ['aba', 'aabba', 'ba', 'bba', 'bbab']
        test_input = TestInput(regex=regex, should_match=should_match,
                               should_not_match=should_not_match)
        self.test_inputs.append(test_input)

    def test_construct_matcher(self):
        for regex, should_match, should_not_match in self.test_inputs:
            matcher = construct_matcher(regex)
            for word in should_match:
                self.assertTrue(matcher.accepts(word), f'{word!r} rejected by'
                                f' the matcher constructed from {regex!r}'
                                f' despite being in the language of that'
                                f' regex. Here is the matcher:\n\t{matcher}')
            for word in should_not_match:
                self.assertTrue(matcher.rejects(word), f'{word!r} accepted by'
                                f' the matcher constructed from {regex!r}'
                                f' despite not being in the language of that'
                                f' regex. Here is the matcher:\n\t{matcher}')
