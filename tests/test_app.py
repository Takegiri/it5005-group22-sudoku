from pathlib import Path
import sys
from streamlit.testing.v1 import AppTest

root = Path(__file__).resolve().parents[1]
folder = root
sys.path.insert(0, str(folder))
app = AppTest.from_file(str(folder / 'sudoku_app.py'), default_timeout=90).run()
assert not app.exception
assert len(app.selectbox[0].options) == 5
# A long proof must paginate without losing steps; a new short query resets it.
app.button[1].click().run()
assert len(app.session_state['query_result']['proof']) > 20
assert len(app.expander) == 20
last_page = (len(app.session_state['query_result']['proof']) - 1) // 20
app.selectbox(key='proof_page').set_value(last_page).run()
assert 1 <= len(app.expander) <= 20
app.number_input[1].set_value(2)
app.button[1].click().run()
assert not app.exception
assert app.session_state['query_result']['verdict'] is False
assert app.session_state['query_result']['refutation'] is True
assert len(app.expander) > 0
app.number_input[0].set_value(1)
app.number_input[1].set_value(2)
app.number_input[2].set_value(3)
app.button[1].click().run()
assert app.session_state['query_result']['verdict'] is True
assert app.session_state['proof_page'] == 0
assert not app.exception
app.radio[0].set_value('Backward chaining').run()
app.button[0].click().run()
assert not app.exception
assert len(app.session_state['solved_result']['grid']) == 81
app.radio[0].set_value('Forward chaining').run()
app.button[0].click().run()
assert not app.exception
assert len(app.session_state['solved_result']['grid']) == 81
assert set(app.session_state['solve_timings']) == {'Forward chaining', 'Backward chaining'}
assert len(app.table[0].value) == 2
app.selectbox[0].set_value(4).run()
assert 'solved_result' not in app.session_state
assert 'query_result' not in app.session_state
assert 'solve_timings' not in app.session_state
print('PASS: initial render, five puzzles, true/false queries, genuine traces, both solvers, puzzle-switch reset.')
