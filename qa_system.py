from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import FAISS
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# client = OpenAI()
# response = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[{"role": "user", "content": "Test"}],
#     max_tokens=500
# )

class QASystem:
    """Question-Answering system using RAG (Retrieval-Augmented Generation)."""
    
    def __init__(self, config, document_processor):
        self.config = config
        self.document_processor = document_processor
        self.chain = None
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the conversational retrieval chain."""
        try:
            # Load documents
            documents = self.document_processor.load_documents()
            
            if not documents:
                logger.error("No documents loaded. QA system will not function properly.")
                return
            
            # Initialize embeddings
            embedding_model = HuggingFaceEmbeddings(
                model_name=self.config.embedding_model_name
            )
            
            # Create vector store
            vectorstore = FAISS.from_documents(documents, embedding_model)
            
            # Initialize memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Create conversational chain
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=ChatOpenAI(openai_api_key=self.config.openai_api_key),
                retriever=vectorstore.as_retriever(
                    search_kwargs={"k": self.config.retriever_k}
                ),
                memory=memory,
                return_source_documents=True,
                output_key="answer"
            )
            
            logger.info("QA system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing QA system: {str(e)}")
            self.chain = None
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Process a question and return the answer with sources."""
        if not self.chain:
            return {
                "answer": "QA system is not properly initialized. Please check the logs.",
                "source_documents": []
            }
        
        try:
            result = self.chain({"question": question})
            return result
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "source_documents": []
            }
    
    def is_answer_uncertain(self, answer: str) -> bool:
        """Check if the answer indicates uncertainty."""
        uncertainty_indicators = [
            "i don't know",
            "i'm not sure",
            "unsure",
            "unclear",
            "cannot find",
            "no information",
            "not mentioned"
        ]
        return any(indicator in answer.lower() for indicator in uncertainty_indicators)
