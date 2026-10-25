from utils.puzzle_verifier import run_verify_from_code
from itertools import permutations
from utils.utils import parse_puzzle
import pandas as pd
import traceback
import time


SOLVER_TIMEOUT_SECONDS = 120

def pretty_print(grid, console=True):
    widths = [
        max(len(str(row[col])) for row in grid)
        for col in range(len(grid[0]))
    ]
    output = []
    for row in grid:
        output.append(" | ".join(
            f"{str(cell):<{widths[i]}}"
            for i, cell in enumerate(row)
        ))
    if console:
        for line in output:
            print(line)
    return "\n".join(output)


def _iter(puzzle, dim, d_indx):
    if d_indx == len(dim):
        grid = puzzle["Grid"]
        keys = list(grid.keys())
        nrows = len(grid[keys[0]])
        new_grid, indx = [], 0
        while indx < nrows:
            row = []
            for key in keys:
                row.append(grid[key][indx])
            new_grid.append(row)
            indx += 1
        yield new_grid
        return
    curr_dim = dim[d_indx]
    curr_options = puzzle["Options"].get(curr_dim) or []
    if len(curr_options) == 0:
        return
    p_options = permutations(curr_options)
    new_puzzle = puzzle.copy()
    for value in p_options:
        new_puzzle["Grid"][curr_dim] = value
        yield from _iter(new_puzzle, dim, d_indx + 1)


def my_sol_main(row: pd.Series):
    puzzle, code = row['Puzzle'], row['Code']
    puzzle = parse_puzzle(puzzle)
    dimensions = list(puzzle["Options"].keys())
    message = ""
    deadline = time.monotonic() + SOLVER_TIMEOUT_SECONDS
    for filled_grid in _iter(puzzle, dimensions, 0):
        if time.monotonic() > deadline:
            print(f"Timeout: solver exceeded {SOLVER_TIMEOUT_SECONDS} seconds")
            message = "Code timed out"
            break
        try:
            reward, f_clues = run_verify_from_code(code, filled_grid)
        except RuntimeError as e:
            print(f"Error:\n{e}")
            print(traceback.format_exc())
            print(f"Filled grid candidate:\n{filled_grid}")
            message = "Incorrect verification code"
            break
        except TimeoutError as e:
            print(f"Timeout:\n{e}")
            print(f"Filled grid candidate:\n{filled_grid}")
            message = "Code timed out"
            break
        if len(f_clues) == 0:
            return {
                "reward": reward,
                "solution": pretty_print(filled_grid, console = True),
                "failed_clues": f_clues,
            }
    return {
        "reward": -1,
        "solution": message,
        "failed_clues": None
    }