verifier_code_prompt = """
You generate ASP (clingo) code for logic-grid puzzles.
Return executable, deterministic, self-contained ASP code that models the
entire puzzle and enforces all clues exactly.

Goal:
- Encode the puzzle as an ASP program whose answer set(s) represent valid
    completed grids.

Hard constraints:
- Output only ASP code: no markdown, prose, or backticks.
- Include complete domain facts for every category mentioned in the puzzle.
- Enforce one-to-one assignments (bijections) between linked categories.
- Encode each clue as ASP constraints/rules that match the clue text exactly.
- Keep naming consistent and lowercase-safe for ASP atoms.
- Do not include Python code, wrappers, or execution instructions.

Implementation guidance:
- Define domain predicates first (for timeline/category/entity values).
- Add relation predicates needed by clues (for example adjacency/order).
- Add choice rules and uniqueness constraints for assignments.
- Add clue constraints in a clearly separated section.
- End with #show directives for assignment predicates needed to read the
    solution.

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

[EXAMPLE ASP CODE]
% ============================================================
% Abbeville K-9 Academy grid puzzle - ASP (clingo) encoding
% ============================================================

% ---- Domains ----
months(march;april;may;june).
dogs(aries;barca;hercules;jaws).
officers(daugherty;lyons;quinn;salinas).

% "1 month before" relation over the timeline
order(march,april).
order(april,may).
order(may,june).

% ---- Assignment: each month gets exactly one dog, and vice versa ----
1 { dog(M,D) : dogs(D) } 1 :- months(M).
1 { dog(M,D) : months(M) } 1 :- dogs(D).

% ---- Assignment: each month gets exactly one officer, and vice versa ----
1 { officer(M,O) : officers(O) } 1 :- months(M).
1 { officer(M,O) : months(M) } 1 :- officers(O).

% ============================================================
% Clues
% ============================================================

% Clue 1: The dog that graduated in May was assigned to
%         Officer Salinas or Officer Quinn.
:- officer(may,O), O != salinas, O != quinn.

% Clue 2: Barca graduated in April.
:- dog(april,D), D != barca.

% Clue 3: Officer Lyons's dog graduated exactly 1 month
%         before Officer Daugherty's dog.
:- officer(M1,lyons), officer(M2,daugherty), not order(M1,M2).

% Clue 4: Lyons's dog, the June dog, Jaws, and the April dog
%         are four DIFFERENT dogs (pairwise distinct):
%   - Lyons's dog is not the June dog
:- officer(june,lyons).
%   - Lyons's dog is not the April dog
:- officer(april,lyons).
%   - Jaws is not the June dog
:- dog(june,jaws).
%   - Jaws is not the April dog (also follows from clue 2)
:- dog(april,jaws).
%   - Lyons's dog is not Jaws
:- officer(M,lyons), dog(M,jaws).

% Clue 5: Officer Salinas's dog was Hercules or Barca.
:- officer(M,salinas), dog(M,D), D != hercules, D != barca.

% ============================================================
% Output
% ============================================================
#show dog/2.
#show officer/2.
"""


code_prompt = """
You are an ASP code extractor and sanitizer.

Your task is to clean the provided LLM-generated ASP output so that the final
result is directly executable by clingo as a .lp/.asp source file.

Rules:
1. Output ONLY valid, executable ASP code.
2. Do NOT include Markdown code fences such as ```asp, ```prolog, or ```.
3. Do NOT include explanations, introductions, conclusions, or any
    natural-language text outside ASP code.
4. Remove markdown formatting, XML-style tags, and wrappers that are not ASP.
5. Preserve the original ASP logic as much as possible. Only remove or fix
    content that prevents direct execution in clingo.
6. If the input is already valid ASP code, return it unchanged.
7. Keep ASP comments only if they are already part of the generated code.
8. The final response must be suitable for saving directly to a `.lp` or
    `.asp` file and executing with clingo.

Return ONLY the cleaned ASP source code.
"""