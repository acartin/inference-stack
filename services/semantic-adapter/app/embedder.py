import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class GeminiEmbedder:
    """
    Implementation of the embedding service using Google Gemini.
    Designed to be replaceable without affecting the rest of the Semantic Adapter.
    """

    def __init__(self, model: str = "models/text-embedding-004"):
        """
        Initialize the Gemini embedder.
        reads GOOGLE_API_KEY from environment variables.
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        
        self._client = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=self.api_key
        )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents asynchronously.
        """
        return await self._client.aembed_documents(texts)

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query asynchronously.
        """
        return await self._client.aembed_query(text)
