"""Independent truth-table checks, not another implementation of chaining."""
import itertools
import random
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from sudoku_solver import *

# Enumerate every Boolean interpretation of a 2x2 encoding. Exactly the
# two Latin squares satisfy it, with and without each possible given.
symbols = [atom('Is', r, c, v) for r in (1, 2) for c in (1, 2) for v in (1, 2)]
for givens in [{}, {(1, 1): 1}, {(1, 1): 2}]:
    kb = build_general_kb(2, 1, 2, givens)
    count = 0
    for bits in itertools.product([False, True], repeat=8):
        model = dict(zip(symbols, bits))
        cells = {(r,c): [v for v in (1,2) if model[atom('Is',r,c,v)]]
                 for r in (1,2) for c in (1,2)}
        legal = (all(len(vs)==1 for vs in cells.values()) and
                 all(cells[r,1] != cells[r,2] for r in (1,2)) and
                 all(cells[1,c] != cells[2,c] for c in (1,2)) and
                 all(cells[cell] == [v] for cell,v in givens.items()))
        result = all(pl_true(clause, model) for clause in kb.clauses)
        assert result == legal
        count += result
    assert count == (1 if givens else 2)
print('PASS: all 768 Boolean interpretations of tiny Sudoku encodings.')

# Use actual classical model enumeration as the oracle; keep duplicate
# rules and repeated premises, and ask queries in shuffled order.
rng = random.Random(225005)
atoms = [expr(f'T{i}') for i in range(5)]
for trial in range(300):
    kb = PropDefiniteKB()
    for a in atoms:
        if rng.random() < .2:
            kb.tell(a)
    for _ in range(12):
        premises = [rng.choice(atoms) for _ in range(rng.randint(1,3))]
        rule = Expr('==>', associate('&', premises), rng.choice(atoms))
        kb.tell(rule)
        if rng.random() < .15:
            kb.tell(rule)
    models = [dict(zip(atoms,bits)) for bits in itertools.product([False,True],repeat=5)]
    models = [m for m in models if all(pl_true(c,m) for c in kb.clauses)]
    assert models
    for q in rng.sample(atoms,5):
        assert pl_bc_entails(kb,q) == all(m[q] for m in models), (trial,q)
        proof = backward_proof(kb,q)
        seen = set()
        for head, premises in proof:
            assert set(premises) <= seen
            assert any(h == head and set(ps) == set(premises)
                       for ps,h in map(parse_definite_clause,kb.clauses))
            seen.add(head)
print('PASS: 1500 Horn queries against exhaustive truth tables, with cycles and duplicate premises/rules.')
