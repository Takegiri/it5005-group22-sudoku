"""Sudoku constraints and propositional inference for IT5005."""

from utils import *
from logic_ import *


# Do not change this function; it is used to create atomic propositions.
def atom(prefix, r, c, v):
    """prefix is 'Is' or 'Not'. Returns the Expr for e.g. Is3_2_4."""
    return expr(f'{prefix}{r}_{c}_{v}')


def _validate(n, box_h, box_w, givens):
    if any(type(x) is not int or x < 1 for x in (n, box_h, box_w)):
        raise ValueError('Grid and box dimensions must be positive integers.')
    if box_h * box_w != n or n % box_h or n % box_w:
        raise ValueError('Boxes must partition the grid and contain n cells.')
    for cell, v in givens.items():
        if (not isinstance(cell, tuple) or len(cell) != 2 or
                any(type(x) is not int or not 1 <= x <= n for x in (*cell, v))):
            raise ValueError('Givens must map (row, column) to values in 1..n.')
    for unit in _units(n, box_h, box_w):
        values = [givens[cell] for cell in unit if cell in givens]
        if len(values) != len(set(values)):
            raise ValueError('Conflicting givens in a row, column, or box.')


def _units(n, box_h, box_w):
    rows = [[(r, c) for c in range(1, n + 1)] for r in range(1, n + 1)]
    cols = [[(r, c) for r in range(1, n + 1)] for c in range(1, n + 1)]
    boxes = [[(r, c) for r in range(br, br + box_h)
              for c in range(bc, bc + box_w)]
             for br in range(1, n + 1, box_h)
             for bc in range(1, n + 1, box_w)]
    return rows + cols + boxes


def _peers(n, box_h, box_w):
    peers = {(r, c): set() for r in range(1, n + 1) for c in range(1, n + 1)}
    for unit in _units(n, box_h, box_w):
        for cell in unit:
            peers[cell].update(set(unit) - {cell})
    return peers


def build_general_kb(n, box_h, box_w, givens):
    """Exact Sudoku CNF, using only Is atoms and their logical negations."""
    _validate(n, box_h, box_w, givens)
    kb = PropKB()
    peers = _peers(n, box_h, box_w)
    symbols = {(r, c, v): atom('Is', r, c, v)
               for r, c in peers for v in range(1, n + 1)}
    for r, c in peers:
        values = [symbols[r, c, v] for v in range(1, n + 1)]
        kb.tell(associate('|', values))
        for a, b in combinations(values, 2):
            kb.tell(~a | ~b)
        for rr, cc in sorted(peers[r, c]):
            if (r, c) < (rr, cc):
                for v in range(1, n + 1):
                    kb.tell(~symbols[r, c, v] | ~symbols[rr, cc, v])
    for (r, c), v in sorted(givens.items()):
        kb.tell(symbols[r, c, v])
    return kb


class _IndexedDefiniteKB(PropDefiniteKB):
    """Index premise lookup; the supplied forward-chaining algorithm is unchanged."""

    def __init__(self):
        super().__init__()
        self._premises = {}

    def tell(self, sentence):
        super().tell(sentence)
        if sentence.op == '==>':
            for p in set(conjuncts(sentence.args[0])):
                self._premises.setdefault(p, []).append(sentence)

    def retract(self, sentence):
        super().retract(sentence)
        if sentence.op == '==>':
            for p in set(conjuncts(sentence.args[0])):
                self._premises[p].remove(sentence)

    def clauses_with_premise(self, p):
        return self._premises.get(p, [])


def build_definite_kb(n, box_h, box_w, givens):
    """Elimination and last-candidate rules; no search or solution data."""
    _validate(n, box_h, box_w, givens)
    kb = _IndexedDefiniteKB()
    peers = _peers(n, box_h, box_w)
    yes = {(r, c, v): atom('Is', r, c, v)
           for r, c in peers for v in range(1, n + 1)}
    no = {(r, c, v): atom('Not', r, c, v)
          for r, c in peers for v in range(1, n + 1)}
    for (r, c), v in sorted(givens.items()):
        kb.tell(yes[r, c, v])
    for r, c in peers:
        for v in range(1, n + 1):
            for w in range(1, n + 1):
                if w != v:
                    kb.tell(Expr('==>', yes[r, c, v], no[r, c, w]))
            for rr, cc in sorted(peers[r, c]):
                kb.tell(Expr('==>', yes[r, c, v], no[rr, cc, v]))
            remaining = [no[r, c, w] for w in range(1, n + 1) if w != v]
            kb.tell(Expr('==>', associate('&', remaining), yes[r, c, v])
                    if remaining else yes[r, c, v])
    return kb


def _bc_state(kb):
    # Compare contents, not just length: tell/retract or direct replacement
    # must not leave answers cached against an older KB.
    snapshot = tuple(kb.clauses)
    state = getattr(kb, '_bc_state_cache', None)
    if state is None or state['snapshot'] != snapshot:
        facts, rules = set(), {}
        for clause in snapshot:
            premises, head = parse_definite_clause(clause)
            if premises:
                rules.setdefault(head, []).append(tuple(dict.fromkeys(premises)))
            else:
                facts.add(head)
        state = {'snapshot': snapshot, 'known': facts, 'rules': rules,
                 'proof': {p: () for p in facts}, 'false': set()}
        kb._bc_state_cache = state
    return state


def pl_bc_entails(kb, query):
    """Tabled, goal-directed AND/OR proof with repeated passes for cycles.

    A failed branch is only provisional. Retry the query when a pass proves
    new atoms, and cache False only after a pass makes no progress. Suspended
    generators implement recursive subgoals without Python call-stack limits.
    Only successful premises are stored as the reasoning trace.
    """
    if not isinstance(query, Expr) or query.args or not is_prop_symbol(query.op):
        raise ValueError('The query must be one positive propositional atom.')
    state = _bc_state(kb)
    known, rules = state['known'], state['rules']
    if query in known:
        return True
    if query in state['false']:
        return False

    def prove(goal, expanded):
        if goal in known:
            return True
        if goal in expanded or goal in state['false']:
            return False
        expanded.add(goal)
        for premises in rules.get(goal, ()):
            for premise in premises:
                ok = yield premise
                if not ok:
                    break
            else:
                known.add(goal)
                state['proof'][goal] = premises
                return True
        return False

    while True:
        before = len(known)
        expanded = set()
        stack = [prove(query, expanded)]
        result = None
        while stack:
            try:
                subgoal = stack[-1].send(result)
                stack.append(prove(subgoal, expanded))
                result = None
            except StopIteration as done:
                stack.pop()
                result = done.value
        if result:
            return True
        if len(known) == before:
            state['false'].add(query)
            return False


def backward_proof(kb, query):
    """Return a premise-first proof DAG recorded by the actual BC execution.

    Each entry is (conclusion, premises); empty premises denote a KB fact.
    Unproved queries have no successful proof and return an empty list.
    """
    if not pl_bc_entails(kb, query):
        return []
    proof = _bc_state(kb)['proof']
    result, seen = [], set()
    stack = [(query, False)]
    while stack:
        goal, ready = stack.pop()
        if goal in seen:
            continue
        if ready:
            seen.add(goal)
            result.append((goal, proof[goal]))
        else:
            stack.append((goal, True))
            stack.extend((p, False) for p in reversed(proof[goal]))
    return result


def _solve(n, box_h, box_w, givens, entails):
    kb = build_definite_kb(n, box_h, box_w, givens)
    solved = {}
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                if entails(kb, atom('Is', r, c, v)):
                    solved[r, c] = v
                    break
    if len(solved) != n * n:
        raise ValueError(f'Only {len(solved)}/{n*n} cells are entailed by these '
                         'Horn rules. More givens or stronger rules are needed.')
    for unit in _units(n, box_h, box_w):
        if {solved[cell] for cell in unit} != set(range(1, n + 1)):
            raise ValueError('The inferred grid violates a Sudoku constraint.')
    if any(solved[cell] != v for cell, v in givens.items()):
        raise ValueError('The inferred grid contradicts a given.')
    return solved


def solve_full_grid_fc(n, box_h, box_w, givens):
    """Try each candidate with the supplied pl_fc_entails, using a fresh KB."""
    return _solve(n, box_h, box_w, givens, pl_fc_entails)


def solve_full_grid_bc(n, box_h, box_w, givens):
    """Try each candidate with pl_bc_entails; reuse proofs within this solve."""
    return _solve(n, box_h, box_w, givens, pl_bc_entails)
