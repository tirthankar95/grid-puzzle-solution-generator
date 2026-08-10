import ast
import traceback
import pandas as pd
from prompt import p_v1
from prompt import no_llm_v1
from pprint import pprint
from langfuse_local import (
    _log_generation,
    _start_trace,
    _finish_trace,
)
from llms.openai import OpenAILLM
from typing import Any, Literal, TypedDict
from puzzle_verifier import run_verify_from_code
from langgraph.graph import END, START, StateGraph


graph = None
LLM = OpenAILLM()
MAX_ATTEMPTS = 3

class VerifierRunResult(TypedDict):
    puzzle: str
    verifier_code: str
    example_solution: str
    chat_history: list[str]
    execution_feedback: str
    reward: float
    failed_clues: list[int]
    attempts: int
    trace_id: str
    no_llm: bool
    terminal_error: str


def get_verifier_code(state: VerifierRunResult) -> VerifierRunResult:
    chat_history = state.get("chat_history", [])
    if chat_history:
        history_block = "\n\n".join(chat_history)
        prompt = (
            f"{p_v1.verifier_code_prompt}\n\n{state['puzzle']}"
            f"\n\nPrevious attempts and errors:\n{history_block}\n"
            "Regenerate verifier code that fixes the previous issues."
        )
    else:
        prompt = f"{p_v1.verifier_code_prompt}\n\n{state['puzzle']}"
    if state.get("no_llm", False):
        verifier_code = no_llm_v1.verifier_code_response
    else:
        verifier_code = LLM.get_response(prompt)
    _log_generation(
        state,
        name="generate_verifier_code",
        model=LLM.model_name,
        input_payload=prompt,
        output_payload=verifier_code,
    )
    return {"verifier_code": verifier_code}


def get_example_sol(state: VerifierRunResult) -> VerifierRunResult:    
    prompt = f"{p_v1.example_prompt}\n\n{state['puzzle']}"
    if state.get("no_llm", False):
        example_solution = no_llm_v1.example_solution_response
    else:
        example_solution = LLM.get_response(prompt)
    _log_generation(
        state,
        name="generate_example_solution",
        model=LLM.model_name,
        input_payload=prompt,
        output_payload=example_solution,
    )
    return {"example_solution": example_solution}


def get_execution_feedback(state: VerifierRunResult) -> VerifierRunResult:
    def _parse_solution(solution_text: str) -> list[list[Any]]:
        parsed = ast.literal_eval(solution_text)
        if not isinstance(parsed, list) or any(not isinstance(row, list) for row in parsed):
            raise ValueError("Generated solution is not a 2D list.")
        return parsed
    attempts = state.get("attempts", 0) + 1
    verifier_code = state.get("verifier_code", "")
    example_solution = state.get("example_solution", "")
    chat_history = list(state.get("chat_history", []))
    terminal_error = ""
    try:
        filled_grid = _parse_solution(example_solution)
        reward, failed_clues = run_verify_from_code(verifier_code, filled_grid)
        feedback = (
            "verification_passed"
            if len(failed_clues) == 0
            else f"verification_failed: failed_clues={failed_clues}"
        )
    except Exception as exc:
        reward, failed_clues = 0.0, []
        terminal_error = traceback.format_exc()
        feedback = f"execution_error: {exc}"

    short_verifier = verifier_code[:800]
    chat_history.append(
        "\n".join(
            [
                f"Attempt: {attempts}",
                f"Execution feedback: {feedback}",
                f"Verifier code:\n{short_verifier}",
                f"Example solution:\n{example_solution}"
            ]
        )
    )
    _log_generation(
        state,
        name="verify_solution",
        model="python_verifier",
        input_payload={
            "attempt": attempts,
            "example_solution": example_solution,
            "verifier_code": verifier_code,
        },
        output_payload={
            "reward": float(reward),
            "failed_clues": failed_clues,
            "execution_feedback": feedback,
        },
        metadata={"attempt": attempts},
    )
    return {
        "execution_feedback": feedback,
        "reward": float(reward),
        "failed_clues": failed_clues,
        "attempts": attempts,
        "terminal_error": terminal_error,
        "chat_history": chat_history,
    }


def route_after_execution_feedback(state: VerifierRunResult) -> Literal["safe_exit", "verifier_code"]:
    attempts = state.get("attempts", 0)
    reward = state.get("reward", 0.0)
    failed_clues = state.get("failed_clues", [])

    if (reward > 0 and not failed_clues) or attempts >= MAX_ATTEMPTS:
        return "safe_exit"
    return "verifier_code"


def build_graph():
    grid_graph = StateGraph(VerifierRunResult)
    grid_graph.add_node("verifier_code", get_verifier_code)
    grid_graph.add_node("example_solution", get_example_sol)
    grid_graph.add_node("execution_feedback", get_execution_feedback)

    # One attempt: generate verifier -> generate candidate solution -> verify it.
    grid_graph.add_edge(START, "verifier_code")
    grid_graph.add_edge("verifier_code", "example_solution")
    grid_graph.add_edge("example_solution", "execution_feedback")

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

    trace_id = _start_trace(row["Puzzle"])
    initial_state: VerifierRunResult = {
        "puzzle": row["Puzzle"],
        "verifier_code": "",
        "example_solution": "",
        "chat_history": [],
        "execution_feedback": "",
        "reward": 0.0,
        "failed_clues": [],
        "attempts": 0,
        "trace_id": trace_id,
        "no_llm": no_llm,
        "terminal_error": "",
    }
    state = graph.invoke(initial_state)
    result = {
        "reward": state["reward"],
        "solution": state["example_solution"],
        "failed_clues": state["failed_clues"],
        "verifier_code": state["verifier_code"],
        "attempts": state["attempts"],
        "execution_feedback": state["execution_feedback"],
        "terminal_error": state.get("terminal_error", ""),
    }
    _finish_trace(trace_id, result)
    return result


if __name__ == "__main__":
    df = pd.read_csv("data/grid-puzzles-sample.csv")
    row = df.iloc[1]
    with open('logs.txt', 'w') as f:
        result = llm_sol_main(row, False)
        pprint(result, stream=f)
