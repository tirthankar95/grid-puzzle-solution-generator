import traceback
import pandas as pd
from pprint import pprint
import os
from utils.run_asp import solve
from prompt import p_v1_asp
from prompt import p_no_llm_v1
from langsmith import traceable
from llms import create_llm
from typing import Any, Literal, TypedDict
from langgraph.graph import END, START, StateGraph


graph = None
LLM = create_llm()
MAX_ATTEMPTS = 3

class VerifierRunResult(TypedDict):
    puzzle: str
    verifier_code: str
    clean_code: str
    execution_feedback: str 
    terminal_error: str
    chat_history: list[str]
    attempts: int
    no_llm: bool


@traceable
def get_verifier_code(state: VerifierRunResult):
    chat_history = state.get("chat_history", [])
    if chat_history:
        history_block = "\n\n".join(chat_history)
        prompt = (
            f"{p_v1_asp.verifier_code_prompt}\n\n{state['puzzle']}"
            f"\n\nPrevious attempts and errors:\n{history_block}\n"
            "Regenerate verifier code that fixes the previous issues.\n/no_think"
        )
    else:
        prompt = f"""{p_v1_asp.verifier_code_prompt}
        
[USER PUZZLE]
{state['puzzle']}
/no_think"""
    verifier_code = p_no_llm_v1.verifier_asp if state.get("no_llm", False) else LLM.get_response(prompt)
    return {
        "verifier_code": verifier_code,
        "chat_history": chat_history
        }


@traceable
def get_code(state: VerifierRunResult):
    prompt = f'{p_v1_asp.code_prompt}\n\n{state["verifier_code"]}\n/no_think'
    if state.get("no_llm", False):
        code = p_no_llm_v1.verifier_asp.strip()
    else:
        code = LLM.get_response(prompt).strip()
    return {"clean_code": code}


@traceable
def get_execution_feedback(state: VerifierRunResult):
    attempts = state.get("attempts", 0) + 1
    verifier_code = state.get("clean_code", "") or state.get("verifier_code", "")
    chat_history = list(state.get("chat_history", []))
    terminal_error = ""
    try:
        candidate = verifier_code.strip()
        if not candidate:
            raise ValueError("Empty ASP code.")
        solution = solve(candidate)
        print(solution)
        feedback = "verification_passed"
    except Exception as exc:
        terminal_error = traceback.format_exc()
        feedback = f"execution_error: {exc}"
    chat_history.append(
        "\n".join(
            [
                f"Attempt: {attempts}",
                f"Execution feedback: {feedback}",
                f"Verifier code:\n{verifier_code}"
            ]
        )
    )
    return {
        "execution_feedback": feedback,
        "attempts": attempts,
        "terminal_error": terminal_error,
        "chat_history": chat_history,
    }


@traceable
def route_after_execution_feedback(state: VerifierRunResult) -> Literal["safe_exit", "verifier_code"]:
    attempts = state.get("attempts", 0)
    feedback = state.get("execution_feedback", "")
    if (feedback == "verification_passed") or attempts >= MAX_ATTEMPTS:
        return "safe_exit"
    return "verifier_code"


def build_graph():
    grid_graph = StateGraph(VerifierRunResult)
    grid_graph.add_node("verifier_code", get_verifier_code)
    grid_graph.add_node("extract_code", get_code)
    grid_graph.add_node("execution_feedback", get_execution_feedback)
    # One attempt: generate verifier -> generate candidate solution -> verify it.
    grid_graph.add_edge(START, "verifier_code")
    grid_graph.add_edge("verifier_code", "extract_code")
    grid_graph.add_edge("extract_code", "execution_feedback")
    # If verification is good then exit, else retry until max attempts.
    grid_graph.add_conditional_edges(
        "execution_feedback",
        route_after_execution_feedback,
        {
            "safe_exit": END,
            "verifier_code": "verifier_code",
        },
    )
    return grid_graph


def llm_sol_main(row: pd.Series, no_llm: bool = False) -> dict[str, Any]:
    global graph
    if graph is None:
        graph = build_graph().compile()
    initial_state: VerifierRunResult = {
        "puzzle": row["Puzzle"],
        "verifier_code": "",
        "clean_code": "",
        "chat_history": [],
        "execution_feedback": "",
        "attempts": 0,
        "no_llm": no_llm,
        "terminal_error": "",
    }
    state = graph.invoke(initial_state)
    result = {
        "solution": None,
        "verifier_code": state["verifier_code"],
        "clean_code": state["clean_code"],
        "attempts": state["attempts"],
        "execution_feedback": state["execution_feedback"],
        "terminal_error": state.get("terminal_error", ""),
    }
    return result


if __name__ == "__main__":
    df = pd.read_csv("data/grid-puzzles-sample.csv")
    row = df.iloc[0]
    with open('logs.txt', 'w') as f:
        result = llm_sol_main(row, no_llm = True)
        pprint(result, stream=f)
