from langchain_openai import ChatOpenAI
from llms.base import BaseLLM, register


@register("openai")
class OpenAILLM(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model_name = kwargs.get("model_name", 'local')
        self._api_key = kwargs.get("api_key", 'X')
        self._client = None
    def get_client(self):
        """Lazily initialize and return the OpenAI client."""
        if self._client is None:
            if self._model_name == "local":
                self._client = ChatOpenAI(
                    base_url = "http://localhost:8080/v1",
                    api_key = self._api_key
                )
            else:
                self._client = ChatOpenAI(
                    model_name=self._model_name,
                    api_key = self._api_key
                ) 
        return self._client