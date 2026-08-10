verifier_code_prompt = """
You generate Python verifier code for logic-grid puzzles.

Task:
- Produce executable, deterministic, self-contained Python code.
- The code must define a function: verify(grid).
- Input: grid is a 2D list of strings, one row per solved table row.
- Output: (reward, failed_clues)
    - reward: float in [0, 1], computed as satisfied_clues / total_clues
    - failed_clues: list[int], 0-based clue indices that failed

Hard output constraints:
- Return only Python code (no markdown, no prose, no backticks).
- Keep verify(grid) as the callable entry point.
- Do not import external libraries.
- Do not use randomness, network, file I/O, or global mutable state.

Implementation requirements:
- Parse grid rows into useful structures (maps by entity/category).
- Encode each clue as a boolean check.
- Treat malformed input defensively:
  - if grid shape is invalid or required values are missing,
    return (0.0, list(range(total_clues))).
- Ensure reward is float, not int.

Quality requirements:
- Clue checks must reflect puzzle text exactly.
- Use clear variable names and straightforward logic.
- Keep code concise and readable.

Reference example (style and contract):
[EXAMPLE PUZZLE]
Story:
The Abbeville K-9 Academy trains dogs for use by a number of different county police forces.  Using only the clues below, match each of their most recent ""students"" to the month in which they graduated and the name of the officer and county to which they were assigned. Remember, as with all grid-based logic puzzles, no option in any category will ever be used more than once.  If you get stuck or run into problems, try the ""Clear Errors"" button to remove any mistakes that might be present on the grid, or the ""Hint"" button to see the next logical step in the puzzle.

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

[EXAMPLE VERIFIER CODE]
from dataclasses import dataclass

MONTHS = {
    "March": 0,
    "April": 1,
    "May": 2,
    "June": 3,
}

@dataclass
class Officer:
    name: str
    dog: str = None
    month: int = None

@dataclass
class Dog:
    name: str
    officer: str = None
    month: int = None

def clue0(Dogs, Officers):
    return (
        Officers["Salinas"].month == MONTHS["May"]
        or Officers["Quinn"].month == MONTHS["May"]
    )

def clue1(Dogs, Officers):
    return Dogs["Barca"].month == MONTHS["April"]

def clue2(Dogs, Officers):
    return Officers["Daugherty"].month == Officers["Lyons"].month + 1

def clue3(Dogs, Officers):
    june_dog = None
    april_dog = None
    for dog in Dogs.values():
        if dog.month == MONTHS["June"]:
            june_dog = dog.name
        if dog.month == MONTHS["April"]:
            april_dog = dog.name
    values = {
        Officers["Lyons"].dog,
        june_dog,
        "Jaws",
        april_dog,
    }
    return len(values) == 4

def clue4(Dogs, Officers):
    return Officers["Salinas"].dog in {"Hercules", "Barca"}

def verify(grid):
    Dogs = {
        row[1]: Dog(name=row[1], month=MONTHS[row[0]], officer=row[2])
        for row in grid
    }
    Officers = {
        row[2]: Officer(name=row[2], month=MONTHS[row[0]], dog=row[1])
        for row in grid
    }

    clue_results = [
        clue0(Dogs, Officers),
        clue1(Dogs, Officers),
        clue2(Dogs, Officers),
        clue3(Dogs, Officers),
        clue4(Dogs, Officers),
    ]

    failed_clues = [idx for idx, ok in enumerate(clue_results) if not ok]
    return float(sum(clue_results)) / len(clue_results), failed_clues

Now generate code for the target puzzle provided by the user.
"""


example_prompt = """
You generate one candidate solution grid for a logic-grid puzzle.

Task:
- Return one 2D list of strings where each row is one complete assignment.
- The row order should follow the first column's natural order when present (for months: March, April, May, June).
- Every option in each category must appear exactly once.

Hard output constraints:
- Return only a valid Python list literal.
- No markdown, no prose, no comments, no code fences.
- Output must parse with ast.literal_eval.

Schema constraints:
- Number of columns must equal the number of categories.
- Number of rows must equal the number of options in each category.
- Each row must have unique entities across categories.
- Keep exact spelling/casing from puzzle options.

Reference example (style only):
[EXAMPLE PUZZLE]
Story:
The Abbeville K-9 Academy trains dogs for use by a number of different county police forces.  Using only the clues below, match each of their most recent ""students"" to the month in which they graduated and the name of the officer and county to which they were assigned. Remember, as with all grid-based logic puzzles, no option in any category will ever be used more than once.  If you get stuck or run into problems, try the ""Clear Errors"" button to remove any mistakes that might be present on the grid, or the ""Hint"" button to see the next logical step in the puzzle.

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

[EXAMPLE OUTPUT]
[
    ["March", "Aries", "Lyons"],
    ["April", "Barca", "Daugherty"],
    ["May", "Jaws", "Quinn"],
    ["June", "Hercules", "Salinas"]
]

Now generate code for the target puzzle provided by the user.
"""
