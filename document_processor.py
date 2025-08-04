import os
from typing import List
from langchain.document_loaders import PyPDFLoader
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles loading and processing of PDF documents."""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
    
    def load_documents(self) -> List[Document]:
        """Load all PDF documents from the data directory."""
        documents = []
        
        if not os.path.exists(self.data_directory):
            logger.warning(f"Data directory '{self.data_directory}' does not exist")
            return documents
        
        pdf_files = [f for f in os.listdir(self.data_directory) if f.endswith(".pdf")]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in '{self.data_directory}'")
            return documents
        
        for file in pdf_files:
            try:
                file_path = os.path.join(self.data_directory, file)
                loader = PyPDFLoader(file_path)
                docs = loader.load_and_split()
                
                # Add source metadata to each document
                for doc in docs:
                    doc.metadata["source"] = file
                
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} pages from {file}")
                
            except Exception as e:
                logger.error(f"Error loading {file}: {str(e)}")
        
        return documents
