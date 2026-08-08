import re
import string
from pprint import pprint

def getGraph(puzzle: str):
    dim, grid = [], {}
    for line in puzzle.split('\n'):
        line = line.strip()
        if line == '':
            continue
        if line[0] == '|':
            if len(dim) == 0:
                dim = [x.strip() for x in line.split('|') if x.strip() != '']
                for i in range(len(dim)):
                    grid[dim[i]] = []
            else:
                rows = [x.strip() for x in line.split('|') if x.strip() != '']
                for i, row in enumerate(rows):
                    grid[dim[i]].append(row)
    return dim, grid


def getOptions(puzzle: str, graph):
    def getEachOption(puzzle: str, prefix: str):
        for line in puzzle.split('\n'):
            sol, words = None, line.split(' ')
            for word in words:
                if word == prefix:
                    sol = words[1:]
                    return [x.strip().translate(str.maketrans('', '', string.punctuation)) for x in sol] \
                        if sol is not None else []
    options = {}
    for k, v in graph.items():
        if len(v) == 0:
            options[k] = getEachOption(puzzle, k + ":")
    return options


def getClues(puzzle: str):
    def fetch_clues_now(allLines):
        clues, pattern = [], r"\d+\."
        for line in allLines:
            first_element = line.split(' ')[0]
            if re.search(pattern, first_element):
                clues.append(line.strip())
        return clues
    tokens_to_search = ["Clues:", "clues:"]
    allLines = puzzle.split('\n')
    for idx, line in enumerate(allLines):
        words = line.split(' ')
        if words[0].strip() in tokens_to_search:
            return fetch_clues_now(allLines)


def parse_puzzle(puzzle: str):
    dim, grid = getGraph(puzzle)
    n, m = len(grid), len(grid[dim[0]])
    options = getOptions(puzzle, grid)
    clues = getClues(puzzle)
    return {
        'Puzzle': f'{n}X{m}',
        'Clues': clues,
        'Grid': grid,
        'Options': options
    }


if __name__ == "__main__":
    puzzle = """
Story:
The Abbeville K-9 Academy trains dogs for use by a number of different county police forces.  Using only the clues below, match each of their most recent "students" to the month in which they graduated and the name of the officer and county to which they were assigned. Remember, as with all grid-based logic puzzles, no option in any category will ever be used more than once.  If you get stuck or run into problems, try the "Clear Errors" button to remove any mistakes that might be present on the grid, or the "Hint" button to see the next logical step in the puzzle.

Clues:
1.The canine that graduated in May was either the dog assigned to Officer Salinas or the dog assigned to Officer Quinn.
2.Barca graduated in April.
3.The K-9 unit assigned to Officer Lyons graduated 1 month before the K-9 unit assigned to Officer Daugherty.
4.The four dogs were the K-9 unit assigned to Officer Lyons, the dog that graduated in June, Jaws and the K-9 unit that graduated in April.
5.The canine assigned to Officer Salinas was either Hercules or Barca.

Solve the grid puzzle by filling the table:
+----------+--------+------------+
| Months   | Dogs   | Officers   |
+==========+========+============+
| March    |        |            |
+----------+--------+------------+
| April    |        |            |
+----------+--------+------------+
| May      |        |            |
+----------+--------+------------+
| June     |        |            |
+----------+--------+------------+

Use the clues to fill the table with the following categories:
Dogs: Aries, Barca, Hercules, Jaws
Officers: Daugherty, Lyons, Quinn, Salinas

"""
    result = parse_puzzle(puzzle)
    pprint(result)
    