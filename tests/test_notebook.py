"""Run the complete notebook in a fresh Jupyter kernel, without injected imports.

Install nbclient, nbformat and ipykernel in the test environment first.
Run from any directory: python tests/test_notebook.py
"""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
path = root / 'Sudoku_Assignment.ipynb'
nb = nbformat.read(path, as_version=4)
for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.execution_count = None
        cell.outputs = []

def progress(cell, cell_index, **kwargs):
    print(f'Executing notebook cell {cell_index}', flush=True)

NotebookClient(nb, timeout=900, kernel_name='python3',
               resources={'metadata': {'path': str(root)}},
               on_cell_start=progress).execute()
code_cells = [c for c in nb.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs)
nbformat.validate(nb)
nbformat.write(nb, path)
print(f'PASS: all {len(code_cells)} code cells executed in a fresh Jupyter kernel.', flush=True)
