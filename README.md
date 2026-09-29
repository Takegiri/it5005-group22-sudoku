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
3.13 is suitable. Keep the source repository private if desired and grant the
deployment service access to this repository through your account settings.

## Internal testing

The GitHub repository and deployed app are private. Keep them private during
testing; do not submit until reviewer access has been arranged and checked.

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
