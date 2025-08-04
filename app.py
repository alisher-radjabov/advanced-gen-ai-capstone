import streamlit as st
import logging
from config import Config
from document_processor import DocumentProcessor
from qa_system import QASystem
from ticket_system import TicketSystem
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class SupportBotApp:
    """Main Streamlit application for the Support Bot."""
    
    def __init__(self):
        self.config = Config()
        self.document_processor = DocumentProcessor(self.config.data_directory)
        self.qa_system = None
        self.ticket_system = TicketSystem()
        
        self._setup_streamlit()
        self._initialize_session_state()
    
    def _setup_streamlit(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Support Bot",
            page_icon="🤖",
            layout="wide"
        )
        st.title("🤖 Product Support Chatbot")
        st.markdown("Ask questions about your product documentation!")
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "history" not in st.session_state:
            st.session_state.history = []
        if "tickets" not in st.session_state:
            st.session_state.tickets = []
    
    @st.cache_resource
    def load_qa_system(_self):
        """Load and cache the QA system."""
        return QASystem(_self.config, _self.document_processor)
    
    def handle_user_input(self, user_input: str):
        """Process user input and generate response."""
        if not self.qa_system:
            self.qa_system = self.load_qa_system()
        
        result = self.qa_system.ask_question(user_input)
        answer = result["answer"]
        sources = result.get("source_documents", [])
        
        # Add to history
        st.session_state.history.append((user_input, answer, sources))
        
        return answer, sources
    
    def create_support_ticket(self, question: str, answer: str):
        """Create a support ticket for unanswered questions."""
        # In a real app, you'd collect user details properly
        user_name = st.session_state.get("user_name", "Anonymous User")
        email = st.session_state.get("user_email", "user@example.com")
        
        ticket = self.ticket_system.create_ticket(
            user_name=user_name,
            email=email,
            summary=question,
            description=f"Bot response: {answer}"
        )
        
        st.session_state.tickets.append(ticket)
        return ticket
    
    def display_chat_history(self):
        """Display the chat history and handle ticket creation."""
        for i, (question, answer, sources) in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**You:** {question}")
            st.markdown(f"**Bot:** {answer}")
            
            # Display sources
            if sources:
                with st.expander("📄 Sources"):
                    for doc in sources:
                        source = doc.metadata.get('source', 'Unknown')
                        page = doc.metadata.get('page', '?')
                        st.markdown(f"• {source} (page {page})")
            
            # Show ticket creation button for uncertain answers
            if self.qa_system and self.qa_system.is_answer_uncertain(answer):
                ticket_key = f"ticket_btn_{len(st.session_state.history) - 1 - i}"
                if st.button(f"🎫 Create support ticket", key=ticket_key):
                    ticket = self.create_support_ticket(question, answer)
                    st.success(f"Support ticket created! Ticket ID: {ticket.id}")
            
            st.divider()
    
    def display_sidebar(self):
        """Display sidebar with user info and tickets."""
        with st.sidebar:
            st.header("User Information")
            st.session_state.user_name = st.text_input("Name", value="Alex Smith")
            st.session_state.user_email = st.text_input("Email", value="alex@example.com")
            
            st.header("Support Tickets")
            if st.session_state.tickets:
                for ticket in st.session_state.tickets:
                    with st.expander(f"Ticket {ticket.id}"):
                        st.write(f"**Summary:** {ticket.summary}")
                        st.write(f"**Status:** {ticket.status}")
                        st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.write("No tickets created yet.")
    
    def run(self):
        """Run the Streamlit application."""
        try:
            # Display sidebar
            self.display_sidebar()
            
            # Main chat interface
            col1, col2 = st.columns([3, 1])
            
            with col1:
                user_input = st.text_input(
                    "Ask a question about your documentation:",
                    key="user_input"
                )
                
                if user_input:
                    with st.spinner("Thinking..."):
                        self.handle_user_input(user_input)
                
                # Display chat history
                self.display_chat_history()
            
            with col2:
                st.subheader("System Status")
                if self.qa_system and self.qa_system.chain:
                    st.success("✅ QA System Ready")
                else:
                    st.error("❌ QA System Error")
                
                # Display document count
                docs = self.document_processor.load_documents()
                st.info(f"📚 {len(docs)} documents loaded")
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app = SupportBotApp()
    app.run()