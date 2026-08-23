from langchain_google_genai import ChatGoogleGenerativeAI
from llms.base import BaseLLM, register
import os


@register("gemini")
class GeminiLLM(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model_name = kwargs.get("model_name", "gemini-2.5-flash")
        self._api_key = kwargs.get("api_key", os.environ.get("GOOGLE_API_KEY"))
        self._client = None
    def get_client(self):
        """Lazily initialize and return the Gemini client."""
        if self._client is None:
            self._client = ChatGoogleGenerativeAI(
                model=self._model_name,
                temperature=0.2,
                vertexai=True,                  # <--- Force Vertex AI backend
                project="gd-gcp-gridu-genai",  # <--- Your GCP Project ID
            )
        return self._client