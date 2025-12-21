from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    """
    Logic for text fragmentation using LangChain's RecursiveCharacterTextSplitter.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        Initialize the Chunker with configurable size and overlap.
        
        Args:
            chunk_size (int): Maximum size of chunks. Defaults to 1000.
            chunk_overlap (int): Overlap between chunks. Defaults to 100.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split a text into chunks based on the configured settings.
        
        Args:
            text (str): The input text to be chunked.
            
        Returns:
            List[str]: list of text chunks.
        """
        return self._splitter.split_text(text)
