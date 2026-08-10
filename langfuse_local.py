import os
import uuid
from langfuse import Langfuse
from typing import Any, Mapping
TRACE_REGISTRY: dict[str, Any] = {}
_LANGFUSE = Langfuse()

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
