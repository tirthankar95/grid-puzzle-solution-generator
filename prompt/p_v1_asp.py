verifier_code_prompt = """
You generate ASP verifier code for logic-grid puzzles.
Return executable, deterministic, self-contained ASP code.

Contract:
- grid is a 2D list of strings, one solved row per inner list.
- Return (reward, failed_clues).
- reward is a float in [0, 1] computed as satisfied_clues / total_clues.
- failed_clues is a list[int] of 0-based clue indices that failed.

Hard constraints:
- Output only Python code: no markdown, prose, or backticks.
- Keep verify(grid) as the entry point.
- No external-library imports.
- Do not print or read input.

Implementation:
- Parse rows into useful maps by entity/category instead of relying on row order.
- Encode each clue as a boolean check that matches the clue text exactly.
- Use clear helper variables and straightforward logic.
- Handle malformed input defensively: if grid shape is invalid or required
    values are missing, return (0.0, list(range(total_clues))).
- Ensure reward is a float, not an int.

Reference example (style + contract):
[EXAMPLE PUZZLE]
Story:
Abbeville K-9 Academy puzzle: match each dog to its graduation month and assigned officer.

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

[EXAMPLE SOLUTION]
Example grid input the verifier should accept:
[
    ["March", "Aries", "Lyons"],
    ["April", "Barca", "Daugherty"],
    ["May", "Jaws", "Quinn"],
    ["June", "Hercules", "Salinas"]
]

The verifier code should process this grid correctly and satisfy all clues.
Now generate the verifier code for the target puzzle provided by the user.
"""


code_prompt = """
You are a Python code sanitizer.

Your task is to clean the provided LLM-generated verifier code so that the output is directly executable as a Python source file.

Rules:
1. Output ONLY valid, executable Python code.
2. Do NOT include Markdown code fences such as ```python or ```.
3. Do NOT include explanations, comments about the cleaning process, introductions, conclusions, or any other natural-language text outside the Python code.
4. Remove any Markdown formatting, special delimiters, or surrounding text that is not valid Python syntax.
5. Preserve the original Python code and its logic as much as possible. Only remove or fix content that prevents the code from being directly executable.
6. If the code is already valid Python, return it unchanged.
7. The final response must be suitable for saving directly to a `.py` file and executing with Python.

Return ONLY the cleaned Python source code.
"""