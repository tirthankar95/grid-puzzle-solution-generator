import ast
import os
import uuid
import pandas as pd
from prompt import p_v1
from langfuse import Langfuse
from llms.openai import OpenAILLM
from puzzle_verifier import run_verify_from_code
from langgraph.graph import END, START, StateGraph
from typing import Any, Literal, Mapping, TypedDict


graph = None
LLM = OpenAILLM()
MAX_ATTEMPTS = 3
TRACE_REGISTRY: dict[str, Any] = {}

_LANGFUSE = None
if Langfuse is not None:
    try:
        _LANGFUSE = Langfuse()
    except Exception:
        _LANGFUSE = None


class VerifierRunResult(TypedDict):
    puzzle: str
    verifier_code: str
    example_solution: str
    execution_feedback: str
    reward: float
    failed_clues: list[int]
    attempts: int
    trace_id: str


def _is_langfuse_enabled() -> bool:
    return _LANGFUSE is not None and bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))


def _log_generation(
    state: Mapping[str, Any],
    name: str,
    model: str,
    input_payload: Any,
    output_payload: Any,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    if not _is_langfuse_enabled():
        return
    trace = TRACE_REGISTRY.get(state.get("trace_id", ""))
    if trace is None:
        return
    try:
        generation = trace.generation(
            name=name,
            model=model,
            input=input_payload,
            metadata=dict(metadata or {}),
        )
        generation.end(output=output_payload)
    except Exception:
        # Never let observability break the solver path.
        return


def _start_trace(puzzle: str) -> str:
    trace_id = str(uuid.uuid4())
    if not _is_langfuse_enabled():
        return trace_id
    try:
        trace = _LANGFUSE.trace(
            id=trace_id,
            name="grid-puzzle-solver",
            input={"puzzle": puzzle},
            metadata={"component": "llm_soln"},
        )
        TRACE_REGISTRY[trace_id] = trace
    except Exception:
        return trace_id
    return trace_id


def _finish_trace(trace_id: str, output: Mapping[str, Any]) -> None:
    if not _is_langfuse_enabled():
        return
    trace = TRACE_REGISTRY.get(trace_id)
    if trace is None:
        return
    try:
        trace.update(output=dict(output))
    except Exception:
        pass
    finally:
        TRACE_REGISTRY.pop(trace_id, None)


def get_verifier_code(state: VerifierRunResult) -> VerifierRunResult:
    prompt = f"{p_v1.verifier_code_prompt}\n\n{state['puzzle']}"
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
    example_solution = LLM.get_response(prompt)
    _log_generation(
        state,
        name="generate_example_solution",
        model=LLM.model_name,
        input_payload=prompt,
        output_payload=example_solution,
    )
    return {"example_solution": example_solution}


def _parse_solution(solution_text: str) -> list[list[Any]]:
    parsed = ast.literal_eval(solution_text)
    if not isinstance(parsed, list) or any(not isinstance(row, list) for row in parsed):
        raise ValueError("Generated solution is not a 2D list.")
    return parsed


def get_execution_feedback(state: VerifierRunResult) -> VerifierRunResult:
    attempts = state.get("attempts", 0) + 1
    verifier_code = state.get("verifier_code", "")
    example_solution = state.get("example_solution", "")
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
        feedback = f"execution_error: {exc}"

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


def llm_sol_main(row: pd.Series):
    global graph
    if graph is None:
        graph = build_graph().compile()

    trace_id = _start_trace(row["Puzzle"])
    initial_state: VerifierRunResult = {
        "puzzle": row["Puzzle"],
        "verifier_code": "",
        "example_solution": "",
        "execution_feedback": "",
        "reward": 0.0,
        "failed_clues": [],
        "attempts": 0,
        "trace_id": trace_id,
    }
    state = graph.invoke(initial_state)

    result = {
        "reward": state["reward"],
        "solution": state["example_solution"],
        "failed_clues": state["failed_clues"],
        "verifier_code": state["verifier_code"],
        "attempts": state["attempts"],
        "execution_feedback": state["execution_feedback"],
    }
    _finish_trace(trace_id, result)
    return result


if __name__ == "__main__":
    df = pd.read_csv("data/grid-puzzles-sample.csv")
    row = df.iloc[0]
    result = llm_sol_main(row)
    print(result)
