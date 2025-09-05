import streamlit as st
import os
from datetime import datetime
import json
from typing import List, Dict, Any
import openai
from pathlib import Path
from document_processor import DocumentProcessor
from github_integration import SupportTicketManager
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure page
st.set_page_config(
    page_title="Customer Support Assistant",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize OpenAI client
client = openai.OpenAI()

class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self):
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session_id,
            'metadata': metadata or {}
        }
        st.session_state.conversation_history.append(message)
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation context for AI"""
        recent_messages = st.session_state.conversation_history[-max_messages:]
        return [{'role': msg['role'], 'content': msg['content']} for msg in recent_messages]
    
    def clear_conversation(self):
        """Clear conversation history"""
        st.session_state.conversation_history = []
        st.session_state.current_session_id = self._generate_session_id()

def main():
    st.title("🎧 Customer Support Assistant")
    st.markdown("---")
    
    # Initialize managers
    conv_manager = ConversationManager()
    doc_processor = DocumentProcessor()
    ticket_manager = SupportTicketManager()
    
    # Initialize document processor in session state
    if 'doc_processor' not in st.session_state:
        st.session_state.doc_processor = doc_processor
    
    # Sidebar for configuration and actions
    with st.sidebar:
        st.header("Configuration")
        
        # GitHub Configuration Section
        st.subheader("⚙️ GitHub Integration")
        with st.expander("GitHub Settings", expanded=not ticket_manager.is_github_configured()):
            st.write("Configure GitHub repository for support ticket creation:")
            
            github_token = st.text_input(
                "GitHub Personal Access Token",
                type="password",
                value=st.session_state.get('github_token', ''),
                help="Create a token at https://github.com/settings/tokens with 'repo' permissions"
            )
            
            github_repo = st.text_input(
                "Repository (owner/repo)",
                value=st.session_state.get('github_repo', ''),
                placeholder="e.g., username/support-tickets",
                help="Format: owner/repository-name"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Test Connection"):
                    if github_token and github_repo:
                        with st.spinner("Testing connection..."):
                            result = ticket_manager.test_github_connection(github_token, github_repo)
                            if result['success']:
                                st.success(f"✅ Connected as {result['user']}")
                                st.info(f"Repository: {result['repo']}")
                            else:
                                st.error(f"❌ Connection failed: {result['error']}")
                    else:
                        st.error("Please provide both token and repository")
            
            with col2:
                if st.button("Save Configuration"):
                    if github_token and github_repo:
                        if ticket_manager.configure_github(github_token, github_repo):
                            st.success("✅ GitHub configured successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to configure GitHub")
                    else:
                        st.error("Please provide both token and repository")
        
        # Show GitHub status
        if ticket_manager.is_github_configured():
            github_info = ticket_manager.get_github_info()
            if github_info.get('configured'):
                st.success(f"✅ GitHub: {github_info['repo_name']}")
                st.caption(f"Open issues: {github_info.get('open_issues', 'N/A')}")
        
        st.markdown("---")
        
        # Document upload section
        st.subheader("📄 Documents")
        uploaded_files = st.file_uploader(
            "Upload support documents",
            type=['pdf', 'txt', 'md'],
            accept_multiple_files=True,
            help="Upload PDF, TXT, or Markdown files for the AI to reference"
        )
        
        if uploaded_files:
            for file in uploaded_files:
                # Save uploaded files
                file_path = doc_processor.documents_dir / file.name
                with open(file_path, 'wb') as f:
                    f.write(file.getbuffer())
                
                # Process the document
                if doc_processor.process_document(file_path):
                    st.success(f"✅ Processed: {file.name}")
                else:
                    st.error(f"❌ Failed to process: {file.name}")
        
        # Document statistics
        doc_stats = doc_processor.get_document_stats()
        if doc_stats['total_documents'] > 0:
            st.info(f"📊 **Documents**: {doc_stats['total_documents']} files, {doc_stats['total_pages']} pages")
            
            with st.expander("Document Details"):
                for doc_name in doc_stats['documents']:
                    st.write(f"• {doc_name}")
        
        # Process all documents button
        if st.button("🔄 Reprocess All Documents"):
            with st.spinner("Processing documents..."):
                processed = doc_processor.process_all_documents()
                st.success(f"Processed {processed} documents")
                st.rerun()
        
        st.markdown("---")
        
        # Conversation management
        st.subheader("💬 Conversation")
        if st.button("Clear Chat History"):
            conv_manager.clear_conversation()
            st.rerun()
        
        # Display conversation stats
        total_messages = len(st.session_state.conversation_history)
        st.metric("Total Messages", total_messages)
        
        st.markdown("---")
        
        # Support ticket section
        st.subheader("🎫 Create Support Ticket")
        with st.expander("Ticket Details"):
            if not ticket_manager.is_github_configured():
                st.warning("⚠️ Please configure GitHub integration first")
            
            user_name = st.text_input("Your Name")
            user_email = st.text_input("Your Email")
            ticket_summary = st.text_input("Issue Summary")
            ticket_description = st.text_area("Detailed Description")
            
            include_conversation = st.checkbox(
                "Include conversation history", 
                value=True,
                help="Include recent chat messages in the ticket"
            )
            
            if st.button("Create Ticket"):
                if all([user_name, user_email, ticket_summary, ticket_description]):
                    with st.spinner("Creating support ticket..."):
                        conversation_history = None
                        if include_conversation and st.session_state.conversation_history:
                            conversation_history = st.session_state.conversation_history
                        
                        result = ticket_manager.create_ticket(
                            user_name, user_email, ticket_summary, 
                            ticket_description, conversation_history
                        )
                        
                        if result['success']:
                            st.success("✅ Support ticket created successfully!")
                            st.info(f"**Ticket #{result['issue_number']}**: {result['issue_title']}")
                            st.markdown(f"[View Ticket]({result['issue_url']})")
                        else:
                            st.error(f"❌ Failed to create ticket: {result['error']}")
                else:
                    st.error("Please fill in all fields")
    
    # Main chat interface
    st.subheader("💬 Chat with Support Assistant")
    
    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.conversation_history:
            with st.chat_message(message['role']):
                st.write(message['content'])
                
                # Show metadata if available
                if message.get('metadata') and message['metadata'].get('sources'):
                    with st.expander("📚 Sources"):
                        for source in message['metadata']['sources']:
                            st.write(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about our products or services..."):
        # Add user message to conversation
        conv_manager.add_message('user', prompt)
        
        # Display user message
        with st.chat_message('user'):
            st.write(prompt)
        
        # Process the query
        with st.chat_message('assistant'):
            with st.spinner("Searching documents and thinking..."):
                # Search documents first
                doc_result = doc_processor.search_documents(prompt)
                
                if doc_result['found']:
                    # Answer found in documents
                    response = doc_result['answer']
                    sources = doc_result['sources']
                    
                    st.write(response)
                    
                    if sources:
                        with st.expander("📚 Sources"):
                            for source in sources:
                                st.write(f"• {source}")
                    
                    # Add assistant message with sources
                    conv_manager.add_message(
                        'assistant', 
                        response, 
                        {'sources': sources}
                    )
                else:
                    # No answer found in documents, use AI with conversation context
                    context = conv_manager.get_conversation_context()
                    
                    # Add system message for context
                    messages = [
                        {
                            'role': 'system',
                            'content': '''You are a helpful customer support assistant. 
                            If you cannot find the answer in the provided documents or context, 
                            politely suggest that the user create a support ticket for personalized assistance.
                            Be friendly, professional, and concise in your responses.'''
                        }
                    ] + context + [{'role': 'user', 'content': prompt}]
                    
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            max_tokens=500,
                            temperature=0.7
                        )
                        
                        ai_response = response.choices[0].message.content
                        
                        # Check if we should suggest creating a ticket
                        if any(phrase in ai_response.lower() for phrase in ['support ticket', 'contact support', 'cannot find']):
                            ai_response += "\n\n💡 **Suggestion**: If you need more specific help, you can create a support ticket using the sidebar. Our team will get back to you with personalized assistance!"
                        
                        st.write(ai_response)
                        
                        # Add assistant message
                        conv_manager.add_message('assistant', ai_response)
                        
                    except Exception as e:
                        # Show the document search message if available
                        if doc_result.get('message'):
                            error_msg = doc_result['message']
                        else:
                            error_msg = "I'm sorry, I'm having trouble processing your request right now. Please try again or create a support ticket for assistance."
                        
                        st.write(error_msg)
                        conv_manager.add_message('assistant', error_msg)

if __name__ == "__main__":
    main()

