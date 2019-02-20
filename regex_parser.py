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

from dfa_nfa import NFA, NFA_to_DFA


def standardize(regex):
    '''
    Returns a modified regex with all the whitespace removed and
    with explicit concatenations (by inserting '.' where necessary).
    '''
    regex = [ch for ch in regex if not ch.isspace()]
    result = []
    for i in range(len(regex)):
        result.append(regex[i])
        if i == len(regex) - 1:
            break
        pattern = ''.join('A' if ch.isalnum() else ch
                          for ch in regex[i:i + 2])
        concatenation_patterns = {'AA', 'A(', '*A', '*(', ')(', ')A'}
        if pattern in concatenation_patterns:
            result.append('.')
    return ''.join(result)


def test_stanardize():
    assert standardize(' a |b c') == 'a|b.c'
    assert standardize('ab| c ') == 'a.b|c'
    assert standardize(' ( a * b c * ) *') == '(a*.b.c*)*'
    assert standardize('d | (a*b |c *)e') == 'd|(a*.b|c*).e'

if __name__ == '__main__':
    print('Testing function standardize(regex)...')
    test_stanardize()
    print('Test successful!')


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
    result = []
    for ch in reversed(regex):
        if ch.isspace():
            continue
        if ch.isalnum():
            result.append(ch)
        elif ch == '*':
            op_stack.append(ch)
        elif ch == '.':
            while op_stack and op_stack[-1] == '*':
                result.append('*')
                op_stack.pop()
            op_stack.append(ch)
        elif ch == '|':
            while op_stack and op_stack[-1] in '.*':
                result.append(op_stack[-1])
                op_stack.pop()
            op_stack.append(ch)
        elif ch == ')':
            op_stack.append(ch)
        elif ch == '(':
            assert op_stack
            while op_stack[-1] != ')':
                result.append(op_stack[-1])
                op_stack.pop()
            op_stack.pop()  # pop the ')'
            if op_stack:
                result.append(op_stack[-1])
                op_stack.pop()
        else:
            raise ValueError('Given regex contains an invalid character.')
    result.extend(reversed(op_stack))
    result.reverse()
    return ''.join(result)


def test_infix_to_prefix():
    assert infix_to_prefix('a|b.c') == '|a.bc'
    assert infix_to_prefix('a.b|c') == '|.abc'
    assert infix_to_prefix('(a*.b.c*)*') == '*..*ab*c'
    assert infix_to_prefix('d|(a*.b|c*).e') == '|d.|.*ab*ce'

if __name__ == '__main__':
    print('Testing function infix_to_frefix(regex)...')
    test_infix_to_prefix()
    print('Test successful!')


class Node:
    def __init__(self, data, left, right):
        self.data = data
        self.left = left
        self.right = right

    def __repr__(self):
        return 'Node({}, {}, {})'.format(self.data, self.left, self.right)


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
    state_counter = 0

    def construct_NFA(tree):
        # Thompson's algorithm
        nonlocal state_counter
        assert tree
        token = tree.data
        if token.isalnum():
            assert(not tree.left and not tree.right)
            q0 = state_counter
            q1 = state_counter + 1
            state_counter += 2
            delta = {(q0, token): {q1}}
            F = {q1}
        elif token == '*':
            assert(tree.left and not tree.right)
            son_nfa = construct_NFA(tree.left)
            q0 = son_nfa.q0
            delta = son_nfa.delta
            for q in son_nfa.F:
                if (q, '') not in delta:
                    delta[q, ''] = set()
                delta[q, ''].add(q0)
            F = son_nfa.F.union({q0})
        elif token == '.':
            assert(tree.left and tree.right)
            left_nfa = construct_NFA(tree.left)
            right_nfa = construct_NFA(tree.right)
            q0 = left_nfa.q0
            delta = {**left_nfa.delta, **right_nfa.delta}
            for q in left_nfa.F:
                if (q, '') not in delta:
                    delta[q, ''] = set()
                delta[q, ''].add(right_nfa.q0)
            F = right_nfa.F
        elif token == '|':
            assert(tree.left and tree.right)
            left_nfa = construct_NFA(tree.left)
            right_nfa = construct_NFA(tree.right)
            q0 = state_counter
            state_counter += 1
            delta = {**left_nfa.delta, **right_nfa.delta}
            delta[q0, ''] = {left_nfa.q0, right_nfa.q0}
            F = left_nfa.F.union(right_nfa.F)
        else:
            assert 0, 'Invalid token found in tree: ' + token
        return NFA(q0, delta, F)

    return NFA_to_DFA(construct_NFA(construct_parse_tree(regex)))


# todo: a more comprehensive test
def test_construct_matcher():
    matcher = construct_matcher('d|(a*b|c*)e')
    # review:
    # print(matcher.delta)
    assert matcher.accepts('d')
    assert matcher.accepts('e')
    assert matcher.accepts('ce')
    assert matcher.accepts('ccce')
    assert matcher.accepts('be')
    assert matcher.accepts('abe')
    assert matcher.accepts('aabe')
    assert matcher.rejects('')
    assert matcher.rejects('da')
    assert matcher.rejects('ec')
    assert matcher.rejects('de')
    assert matcher.rejects('b')
    assert matcher.rejects('a')
    assert matcher.rejects('ae')
    assert matcher.rejects('ab')
    assert matcher.rejects('ace')
    assert matcher.rejects('abce')
    assert matcher.rejects('dabe')

    # review:
    matcher2 = construct_matcher('a*b*')
    assert matcher2.accepts('')
    assert matcher2.accepts('a')
    assert matcher2.accepts('b')
    assert matcher2.accepts('ab')
    assert matcher2.accepts('aabb')
    assert matcher2.rejects('ba')
    assert matcher2.rejects('aba')

if __name__ == '__main__':
    print('Testing function construct_matcher(regex)...')
    test_construct_matcher()
    print('Test successful!')
