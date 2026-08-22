verifier_code_response = '''
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
'''


solution = """March | Aries    | Lyons
April | Barca    | Daugherty
May   | Jaws     | Quinn
June  | Hercules | Salinas"""


verifier_asp = """
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
