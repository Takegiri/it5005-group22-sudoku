# Sudoku inference | IT5005 Group 22

A Streamlit interface for the assignment's shared propositional-logic solver.

```sh
pip install -r requirements.txt
streamlit run sudoku_app.py
```

Select any of the five supplied puzzles, choose forward or backward chaining,
and solve the board. A separate cell query uses backward chaining; tutor mode
shows its recorded proof, including the premises used at every step.

The solver imports only the original `utils.py` and `logic_.py`. Those files and
`puzzles.json` are course support files and are unchanged. The answer keys in the
puzzle file are never used for inference. The app discards them when loading.

The full-grid timer includes building a fresh KB. Forward chaining calls the
supplied algorithm for each candidate, with indexed premise lookup. Backward
chaining reuses completed proofs within a single KB and handles cyclic rules
without treating a cut branch as a permanent negative result.

## Streamlit Community Cloud

Use `main` and entrypoint `sudoku_app.py`. Install the dependencies listed in
`requirements.txt`; NumPy is required by the original utilities. Python 3.12 or
3.13 is suitable. The course deployment guide specifies a public GitHub
repository and a public app so the grader can open the app without signing in.

## Review and validation

[Open the deployed app](https://it5005-group22-sudoku-mcvpsg3aywdudne6ouc6hj.streamlit.app/).
The notebook contains the conceptual answers, measured timings, and executed
correctness checks. To review the interface, solve the same puzzle with both
algorithms, then submit a cell query with tutor mode enabled and inspect its
proof steps. If the app is sleeping, use its wake-up button and allow it to load.

Before submission, open the app URL in an incognito window without signing in
to GitHub or Streamlit. The puzzle selector should appear without a login prompt;
check a full-grid solve and a cell query in that window.

Run the independent logic checks and UI regression tests from the repository root:

```sh
python tests/test_semantics.py
python tests/test_app.py
pip install nbclient nbformat ipykernel
python tests/test_notebook.py
```

The first test checks 768 Boolean Sudoku interpretations and 1,500 Horn queries
against exhaustive truth tables, including cyclic and duplicate rules. The second
checks both solvers, true and false queries, proof pagination, retained timings,
and state reset when changing puzzles. The executed notebook also verifies all
3,645 candidate queries against both chaining algorithms and the puzzle answers.
The notebook test starts a fresh Jupyter kernel and executes every code cell in
order. It does not supply additional imports or reuse an interactive session.

The coursework submission itself contains only the notebook and two Python
implementation files, in a folder named `Assignment and Project Group 22`.
