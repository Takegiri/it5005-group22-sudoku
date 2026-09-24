"""Interactive Sudoku inference, using the shared assignment solver."""

import json
import time
from pathlib import Path

import streamlit as st
from sudoku_solver import (
    atom, build_definite_kb, build_general_kb, solve_full_grid_fc,
    solve_full_grid_bc, pl_bc_entails, backward_proof,
)


def describe(symbol):
    name = symbol.op
    prefix = 'Not' if name.startswith('Not') else 'Is'
    r, c, v = map(int, name[len(prefix):].split('_'))
    return prefix, r, c, v


def sentence(head, premises, box_h, box_w):
    kind, r, c, v = describe(head)
    if not premises:
        return f'Row {r}, column {c} is given as {v}.'
    if kind == 'Is':
        eliminated = ', '.join(str(describe(p)[3]) for p in premises)
        return (f'Row {r}, column {c} must be {v}: '
                f'all other values ({eliminated}) have been ruled out.')
    _, rr, cc, vv = describe(premises[0])
    if (r, c) == (rr, cc):
        reason = f'this cell already has value {vv}'
    elif r == rr:
        reason = f'row {r} already contains {v} in column {cc}'
    elif c == cc:
        reason = f'column {c} already contains {v} in row {rr}'
    else:
        br, bc = (r - 1) // box_h + 1, (c - 1) // box_w + 1
        reason = f'box ({br}, {bc}) already contains {v} at row {rr}, column {cc}'
    return f'Rule out {v} at row {r}, column {c}, because {reason}.'


def board(n, box_h, box_w, givens, values):
    html = ['<div style="overflow-x:auto"><table aria-label="Sudoku board" '
            'style="border-collapse:collapse;margin:12px 0;border:3px solid #334155">']
    for r in range(1, n + 1):
        html.append('<tr>')
        for c in range(1, n + 1):
            given = (r, c) in givens
            value = values.get((r, c), '')
            bg, color = ('#e2e8f0', '#0f172a') if given else ('#ffffff', '#0369a1')
            right = '3px solid #334155' if c % box_w == 0 else '1px solid #cbd5e1'
            bottom = '3px solid #334155' if r % box_h == 0 else '1px solid #cbd5e1'
            html.append(f'<td style="width:42px;min-width:32px;height:42px;text-align:center;'
                        f'font-size:21px;background:{bg};color:{color};'
                        f'font-weight:{700 if given else 400};border-right:{right};'
                        f'border-bottom:{bottom}" aria-label="Row {r}, column {c}: '
                        f'{value or "empty"}{", given" if given else ""}">{value}</td>')
        html.append('</tr>')
    html.append('</table></div>')
    st.markdown(''.join(html), unsafe_allow_html=True)
    st.caption('Bold on grey: given values. Blue on white: inferred values. Blank: not filled.')


st.set_page_config(page_title='Group 22 | Sudoku inference', page_icon='🧩', layout='wide')
st.title('Sudoku, one deduction at a time')
st.caption('IT5005 · Assignment and Project Group 22')

with Path(__file__).with_name('puzzles.json').open(encoding='utf-8') as f:
    raw = json.load(f)
n, box_h, box_w = raw['n'], raw['box_h'], raw['box_w']
# Deliberately discard the supplied answer keys at the UI boundary.
puzzles = [{tuple(map(int, key.split('_'))): value for key, value in p['givens'].items()}
           for p in raw['puzzles']]
index = st.selectbox('Puzzle', range(len(puzzles)),
                     format_func=lambda i: f'Puzzle {i + 1} · {len(puzzles[i])} givens')
givens = puzzles[index]
if st.session_state.get('puzzle_index') != index:
    st.session_state.puzzle_index = index
    st.session_state.pop('solved_result', None)
    st.session_state.pop('query_result', None)

left, right = st.columns([1.1, 1])
with left:
    st.subheader('Puzzle board')
    saved = st.session_state.get('solved_result')
    board(n, box_h, box_w, givens, saved['grid'] if saved else givens)
    algorithm = st.radio('Full-grid algorithm', ['Forward chaining', 'Backward chaining'], horizontal=True)
    if st.button('Solve full grid', type='primary'):
        solver = solve_full_grid_fc if algorithm == 'Forward chaining' else solve_full_grid_bc
        with st.spinner(f'Solving with {algorithm.lower()}…'):
            start = time.perf_counter()
            try:
                grid = solver(n, box_h, box_w, givens)
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state.solved_result = {
                    'grid': grid, 'seconds': time.perf_counter() - start, 'algorithm': algorithm}
                st.rerun()
    if saved:
        st.success(f"{saved['algorithm']}: 81/81 cells solved in {saved['seconds']:.3f} seconds.")
        st.caption('Time includes building a fresh KB and querying all cells. Run the other algorithm to compare.')

with right:
    st.subheader('Ask about a cell')
    with st.form('entailment'):
        a, b, c = st.columns(3)
        r = a.number_input('Row', 1, n, 1)
        col = b.number_input('Column', 1, n, 1)
        value = c.number_input('Value', 1, n, 1)
        tutor = st.checkbox('Tutor mode: explain the proof', value=True)
        submitted = st.form_submit_button('Check entailment')
    if submitted:
        with st.spinner('Tracing backward from your query…'):
            start = time.perf_counter()
            kb = build_definite_kb(n, box_h, box_w, givens)
            query = atom('Is', r, col, value)
            verdict = pl_bc_entails(kb, query)
            elapsed = time.perf_counter() - start
            proof = backward_proof(kb, query) if verdict and tutor else []
            refutation = False
            if not verdict and tutor:
                excluded = atom('Not', r, col, value)
                refutation = pl_bc_entails(kb, excluded)
                proof = backward_proof(kb, excluded) if refutation else []
            st.session_state.query_result = {
                'r': r, 'c': col, 'v': value, 'verdict': verdict,
                'seconds': elapsed, 'proof': proof, 'refutation': refutation, 'tutor': tutor}
    answer = st.session_state.get('query_result')
    if answer:
        st.markdown(f"**Row {answer['r']}, column {answer['c']} has value {answer['v']}: "
                    f"`{answer['verdict']}`**")
        st.caption(f"Backward-chaining verdict, including KB construction: {answer['seconds']:.3f} seconds.")
        if not answer['verdict']:
            st.info('The positive query is not entailed. False alone does not mean its negation is proved.')
        if answer['tutor']:
            if answer['refutation']:
                st.write('A separate elimination query proves why this value is excluded:')
            elif not answer['proof']:
                st.write('No proof was found with the available elimination rules.')
            if answer['proof']:
                st.write(f"{len(answer['proof'])} steps in the successful proof (premises first).")
                st.caption('These steps are recorded by the actual inference call; shared premises appear once.')
                step_ids = {h: i for i, (h, _) in enumerate(answer['proof'], 1)}
                for i, (head, premises) in enumerate(answer['proof'], 1):
                    with st.expander(f'{i}. {sentence(head, premises, box_h, box_w)}'):
                        if premises:
                            st.write('Uses step(s): ' + ', '.join(str(step_ids[p]) for p in premises))
                        else:
                            st.write('Starting fact from the puzzle.')
