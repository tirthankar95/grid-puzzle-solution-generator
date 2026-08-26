import importlib.util
import multiprocessing as mp
import tempfile
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Tuple


VERIFY_TIMEOUT_SECONDS = 120


def _extract_python_source(code: str) -> str:
	"""Extract raw Python source from common wrapper formats."""
	if code is None:
		return ""
	src = code.strip()
	# Handle fenced blocks like ```python ... ```.
	if src.startswith("```") and src.endswith("```"):
		lines = src.splitlines()
		if len(lines) >= 2:
			src = "\n".join(lines[1:-1]).strip()
	# Handle triple-quoted blobs like ''' ... ''' or """ ... """.
	if (src.startswith("'''") and src.endswith("'''")) or (
		src.startswith('"""') and src.endswith('"""')
	):
		src = src[3:-3].strip()
	return src


def _load_module_from_file(file_path: Path) -> ModuleType:
	spec = importlib.util.spec_from_file_location("temp_verify_module", str(file_path))
	if spec is None or spec.loader is None:
		raise RuntimeError("Could not create import spec for generated verifier module.")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def _run_verify_worker(file_path: str, grid: list[list[Any]], result_queue: mp.Queue) -> None:
	"""Load and run generated verifier code in an isolated process."""
	try:
		module = _load_module_from_file(Path(file_path))
		verify_fn: Callable[..., Tuple[float, list[int]]] | None = getattr(module, "verify", None)
		if verify_fn is None or not callable(verify_fn):
			raise AttributeError("Generated module does not define a callable verify(grid).")
		result_queue.put(("ok", verify_fn(grid)))
	except Exception:
		result_queue.put(("error", traceback.format_exc()))


def run_verify_from_code(code: str, grid: list[list[Any]]) -> Tuple[float, list[int]]:
	"""
	Write verifier code to a temporary Python file, invoke verify(grid),
	and remove generated artifacts afterward.
	"""
	source = _extract_python_source(code)
	if not source:
		raise ValueError("Empty verifier code provided.")
	temp_path: Path | None = None
	pycache_path: Path | None = None
	process: mp.Process | None = None
	result_queue: mp.Queue | None = None
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as handle:
			handle.write(source)
			temp_path = Path(handle.name)
		result_queue = mp.Queue()
		process = mp.Process(target=_run_verify_worker, args=(str(temp_path), grid, result_queue))
		process.start()
		process.join(VERIFY_TIMEOUT_SECONDS)
		if process.is_alive():
			process.terminate()
			process.join()
			raise TimeoutError(f"Verifier execution exceeded {VERIFY_TIMEOUT_SECONDS} seconds.")
		if result_queue.empty():
			raise RuntimeError("Verifier process exited without returning a result.")
		status, payload = result_queue.get()
		if status == "error":
			raise RuntimeError(payload)
		pycache_path = temp_path.parent / "__pycache__"
		return payload
	finally:
		if process is not None and process.is_alive():
			process.terminate()
			process.join()
		if result_queue is not None:
			result_queue.close()
			result_queue.join_thread()
		if temp_path is not None and temp_path.exists():
			temp_path.unlink()
		if pycache_path is not None and pycache_path.exists():
			for child in pycache_path.iterdir():
				if child.name.startswith(temp_path.stem) and child.suffix == ".pyc":
					child.unlink()
			# Remove empty cache dir if this temp module was the only artifact.
			try:
				next(pycache_path.iterdir())
			except StopIteration:
				pycache_path.rmdir()
