from utils.run_asp import solve as run_verify_from_code
from utils.utils import parse_puzzle
import pandas as pd
import traceback


def parse_solution(solution: str):
    edges, edge, active = [], '', False
    for ch in solution:
        if ch == '(':
            active = True 
        if active:
            edge += ch 
        if ch == ')':
            active = False 
            edges.append(edge)
            edge = ''
    def makeTuple(edge):
        edge = edge.replace('(', '').replace(')', '')
        e1, e2 = edge.split(',')
        e1 = e1.strip()
        e2 = e2.strip()
        return (e1, e2)
    edges = [makeTuple(edge) for edge in edges]
    return edges


def my_sol_main(row: pd.Series):
    puzzle, code = row['Puzzle'], row['Code']
    puzzle = parse_puzzle(puzzle)
    try:
        solution = run_verify_from_code(code)
        solution = parse_solution(solution)
    except Exception as e:
        print(f"Error:\n{e}")
        print(traceback.format_exc())
        return {
            "solution": "Incorrect verification code"
        }
    return {
        "solution": solution
    }