from itertools import permutations
from utils import parse_puzzle, verify

puzzle = parse_puzzle()
dimensions = list(puzzle["Options"].keys())

def fn(grid, dindx):
    if dindx == len(dimensions):
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

    curr_dim = dimensions[dindx]

    for value in permutations(puzzle["Options"][curr_dim]):
        new_grid = grid.copy()
        new_grid[curr_dim] = value
        yield from fn(new_grid, dindx + 1)

curr_grid = puzzle["Grid"].copy()

def pretty_print(grid):
    widths = [
        max(len(str(row[col])) for row in grid)
        for col in range(len(grid[0]))
    ]
    for row in grid:
        print(" | ".join(
            f"{str(cell):<{widths[i]}}"
            for i, cell in enumerate(row)
        ))

for filled_grid in fn(curr_grid, 0):
    try:
        reward, fclues = verify(filled_grid)
    except Exception as e:
        print(f"Error:\n{e}\n{filled_grid}")
        continue
    if len(fclues) == 0:
        pretty_print(filled_grid)
        break