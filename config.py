import os
from dotenv import load_dotenv

class Config:
    """Configuration settings for the Support Bot."""
    
    def __init__(self):
        load_dotenv()
        self._validate_environment()
    
    @property
    def openai_api_key(self) -> str:
        return os.environ.get("OPENAI_API_KEY")
    
    @property
    def data_directory(self) -> str:
        return os.environ.get("DATA_DIRECTORY", "data")
    
    @property
    def embedding_model_name(self) -> str:
        return os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    @property
    def retriever_k(self) -> int:
        return int(os.environ.get("RETRIEVER_K", "3"))
    
    def _validate_environment(self):
        """Validate required environment variables."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
