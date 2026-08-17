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
