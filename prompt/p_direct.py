solution_format = """
You are an expert at solving logic grid puzzles.
You will be given a story, a set of clues, and an empty grid to fill in.

Solving procedure:
1. List all entities per category.
2. Work through each clue in order, deriving concrete assignments or eliminations.
3. After each deduction, note which cells become determined.
4. Once all cells are filled, verify every clue holds against your solution.
5. If any clue fails, revise and re-verify before outputting.

Output rules:
- Output ONLY the filled grid — no prose, no reasoning, no markdown.
- Use the exact row and column order from the input grid.
- Separate values with " | " and pad with spaces so columns align.
- Each row must contain exactly one value per category.
- Every entity must appear exactly once.

Reference example (style + contract):
[EXAMPLE PUZZLE]
Story:
Abbeville K-9 Academy puzzle: match each dog to its graduation month and assigned officer.

Clues:
1. The canine that graduated in May was either the dog assigned to Officer Salinas or the dog assigned to Officer Quinn.
2. Barca graduated in April.
3. The K-9 unit assigned to Officer Lyons graduated 1 month before the K-9 unit assigned to Officer Daugherty.
4. The four dogs were the K-9 unit assigned to Officer Lyons, the dog that graduated in June, Jaws and the K-9 unit that graduated in April.
5. The canine assigned to Officer Salinas was either Hercules or Barca.

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

[EXAMPLE SOLUTION]
March | Aries    | Lyons
April | Barca    | Daugherty
May   | Jaws     | Quinn
June  | Hercules | Salinas
"""