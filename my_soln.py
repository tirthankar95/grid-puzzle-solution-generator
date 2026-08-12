from itertools import permutations
from utils import parse_puzzle
from puzzle_verifier import run_verify_from_code
import pandas as pd

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
    grid = puzzle["Grid"].copy()
    if d_indx == len(dim):
        keys = list(grid.keys())
        nrows = len(grid[keys[0]])
        new_grid = []
        indx = 0
        while indx < nrows:
            row = []
            for key in keys:
                row.append(grid[key][indx])
            new_grid.append(row)
            indx += 1
        yield new_grid
        return
    curr_dim = dim[d_indx]
    for value in permutations(puzzle["Options"][curr_dim]):
        new_puzzle = puzzle.copy()
        new_puzzle["Grid"] = grid.copy()
        new_puzzle["Grid"][curr_dim] = value
        yield from _iter(new_puzzle, dim, d_indx + 1)


def my_sol_main(row: pd.Series):
    puzzle, code = row['Puzzle'], row['Verifier']
    puzzle = parse_puzzle(puzzle)
    dimensions = list(puzzle["Options"].keys())
    for filled_grid in _iter(puzzle, dimensions, 0):
        try:
            reward, f_clues = run_verify_from_code(code, filled_grid)
        except Exception as e:
            print(f"Error:\n{e}\n{filled_grid}")
            continue
        if len(f_clues) == 0:
            return {
                "reward": reward,
                "solution": pretty_print(filled_grid, console = True),
                "failed_clues": f_clues,
            }
    return {
        "reward": reward,
        "solution": "Incorrect verification code",
        "failed_clues": f_clues
    }