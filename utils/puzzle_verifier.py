import importlib.util
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Tuple


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
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as handle:
			handle.write(source)
			temp_path = Path(handle.name)
		module = _load_module_from_file(temp_path)
		verify_fn: Callable[..., Tuple[float, list[int]]] | None = getattr(module, "verify", None)
		if verify_fn is None or not callable(verify_fn):
			raise AttributeError("Generated module does not define a callable verify(grid).")
		pycache_path = temp_path.parent / "__pycache__"
		return verify_fn(grid)
	finally:
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
