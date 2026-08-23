import os
from pathlib import Path
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage
from omegaconf import OmegaConf

LLM_REGISTRY: dict[str, type["BaseLLM"]] = {}


def register(name: str):
    """Decorator to register a concrete LLM implementation by name."""
    key = name.strip().lower()
    if not key:
        raise ValueError("LLM registration name cannot be empty.")
    def decorator(cls: type["BaseLLM"]):
        if key in LLM_REGISTRY:
            raise ValueError(f"LLM '{key}' is already registered.")
        if not issubclass(cls, BaseLLM):
            raise TypeError("Only BaseLLM subclasses can be registered.")
        LLM_REGISTRY[key] = cls
        return cls
    return decorator


def _load_llm_config(config_path: str | None = None):
    """Load LLM config from YAML, if available."""
    default_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    final_path = Path(config_path) if config_path else default_path
    if not final_path.exists():
        return None
    return OmegaConf.load(final_path)


def create_llm(name: str | None = None, **kwargs) -> "BaseLLM":
    """Factory method to instantiate an LLM implementation by name."""
    config = _load_llm_config(kwargs.pop("config_path", None))
    key = (name or (config.llm.provider if config else "openai")).strip().lower()
    llm_cls = LLM_REGISTRY.get(key)
    if llm_cls is None:
        available = ", ".join(sorted(LLM_REGISTRY)) or "none"
        raise ValueError(f"Unknown LLM '{key}'. Available LLMs: {available}.")
    llm_cfg = config.get("llm") if config else None
    if "model_name" not in kwargs and llm_cfg and llm_cfg.get("model_name"):
        kwargs["model_name"] = llm_cfg.model_name
    if "api_key" not in kwargs and llm_cfg and llm_cfg.get("api_key"):
        kwargs["api_key"] = llm_cfg.api_key
    return llm_cls(**kwargs)


class BaseLLM(ABC):
    """Base class for LLM implementations."""
    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self.model_name = model_name or os.environ.get("MODEL_NAME", "gpt-4")
        self.api_key = api_key or os.environ.get("API_KEY")
    @abstractmethod
    def get_client(self):
        """Return the underlying LLM client."""
        pass
    def get_response(self, prompt: str) -> str:
        """Get a response from the LLM for the given prompt."""
        client = self.get_client()
        return client.invoke(prompt).content