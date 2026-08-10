import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage


class BaseLLM(ABC):
    """Base class for LLM implementations."""
    def __init__(self):
        load_dotenv()  
        self.model_name = os.environ.get("MODEL_NAME", "gpt-4") 

    @abstractmethod
    def get_client(self):
        """Return the underlying LLM client."""
        pass

    def get_response(self, prompt: str) -> str:
        """Get a response from the LLM for the given prompt."""
        client = self.get_client()
        messages = [HumanMessage(content=prompt)]
        return client.invoke(messages).content