import pandas as pd
from pprint import pprint
from prompt import p_direct
from prompt import p_no_llm_v1
from dotenv import load_dotenv
from langsmith import traceable
from llms.openai import OpenAILLM
from typing import Any, TypedDict
from langgraph.graph import END, START, StateGraph


graph = None
load_dotenv()
LLM = OpenAILLM()


class DirectSolution(TypedDict):
    puzzle: str
    solution: str
    no_llm: bool


@traceable
def get_puzzle(state: DirectSolution):
    prompt = f"""{p_direct.solution_format}
        
[USER PUZZLE]
{state['puzzle']}

/no_think"""
    solution = p_no_llm_v1.solution if state.get("no_llm", False) else LLM.get_response(prompt)
    return {
        "solution": solution,
    }


def build_graph():
    grid_graph = StateGraph(DirectSolution)
    grid_graph.add_node("puzzle", get_puzzle)
    grid_graph.add_edge(START, "puzzle")
    grid_graph.add_edge("puzzle", END)    
    return grid_graph


def llm_direct_main(row: pd.Series, no_llm: bool = False) -> dict[str, Any]:
    global graph
    if graph is None:
        graph = build_graph().compile()
    initial_state: DirectSolution = {
        "puzzle": row["Puzzle"],
        "no_llm": no_llm
    }
    state = graph.invoke(initial_state)
    result = {
        "solution": state.get("solution", "")
    }
    return result


if __name__ == "__main__":
    df = pd.read_csv("data/old_csv/grid-puzzles-sample.csv")
    row = df.iloc[0]
    with open('logs.txt', 'w') as f:
        result = llm_direct_main(row, no_llm = True)
        pprint(result, stream=f)
