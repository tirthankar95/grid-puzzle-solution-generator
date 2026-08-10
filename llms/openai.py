from langchain_openai import ChatOpenAI
from llms.base import BaseLLM
import os 

class OpenAILLM(BaseLLM):
    
    def __init__(self):
        super().__init__()
        self._client = None
    
    def get_client(self):
        """Lazily initialize and return the OpenAI client."""
        
        if self._client is None:
            if self.model_name == "local":
                self._client = ChatOpenAI(
                    base_url = "http://localhost:8080/v1",
                    api_key = "X"
                )
            else:
                self._client = ChatOpenAI(
                    model_name=self.model_name,
                    api_key = os.environ["OPENAI_API_KEY"]
                ) 
        return self._client