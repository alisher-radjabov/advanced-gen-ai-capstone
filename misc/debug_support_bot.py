import streamlit as st
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Minimal debug version to test basic functionality."""
    
    st.set_page_config(
        page_title="Support Bot Debug",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Support Bot - Debug Mode")
    st.markdown("Minimal version to test configuration and basic functionality")
    
    # Configuration Status
    st.header("Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Environment Variables")
        
        # Check OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            st.success("✅ OPENAI_API_KEY found")
            st.text(f"Key preview: {openai_key[:8]}...")
        else:
            st.error("❌ OPENAI_API_KEY not found")
        
        # Check GitHub credentials
        github_token = os.getenv("GITHUB_TOKEN")
        github_owner = os.getenv("GITHUB_REPO_OWNER")
        github_repo = os.getenv("GITHUB_REPO_NAME")
        
        if github_token:
            st.success("✅ GITHUB_TOKEN found")
        else:
            st.warning("⚠️ GITHUB_TOKEN not found")
            
        if github_owner:
            st.success(f"✅ GITHUB_REPO_OWNER: {github_owner}")
        else:
            st.warning("⚠️ GITHUB_REPO_OWNER not set")
            
        if github_repo:
            st.success(f"✅ GITHUB_REPO_NAME: {github_repo}")
        else:
            st.warning("⚠️ GITHUB_REPO_NAME not set")
    
    with col2:
        st.subheader("Imports Test")
        
        # Test imports
        imports_status = {}
        
        try:
            from config import Config
            imports_status["Config"] = "✅ Success"
        except Exception as e:
            imports_status["Config"] = f"❌ Error: {str(e)}"
        
        try:
            from document_processor import DocumentProcessor
            imports_status["DocumentProcessor"] = "✅ Success"
        except Exception as e:
            imports_status["DocumentProcessor"] = f"❌ Error: {str(e)}"
        
        try:
            from qa_system import QASystem
            imports_status["QASystem"] = "✅ Success"
        except Exception as e:
            imports_status["QASystem"] = f"❌ Error: {str(e)}"
        
        try:
            from ticket_system import TicketSystem
            imports_status["TicketSystem"] = "✅ Success"
        except Exception as e:
            imports_status["TicketSystem"] = f"❌ Error: {str(e)}"
        
        try:
            from openai import OpenAI
            imports_status["OpenAI"] = "✅ Success"
        except Exception as e:
            imports_status["OpenAI"] = f"❌ Error: {str(e)}"
        
        try:
            import requests
            imports_status["Requests"] = "✅ Success"
        except Exception as e:
            imports_status["Requests"] = f"❌ Error: {str(e)}"
        
        for module, status in imports_status.items():
            if "Success" in status:
                st.success(f"{module}: {status}")
            else:
                st.error(f"{module}: {status}")
    
    st.divider()
    
    # Basic functionality test
    st.header("Basic Functionality Test")
    
    # Initialize session state
    if "debug_messages" not in st.session_state:
        st.session_state.debug_messages = []
    
    # Simple chat interface
    user_input = st.text_input("Test message:", key="debug_input")
    
    if user_input:
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.debug_messages.append({
            "time": timestamp,
            "message": user_input,
            "response": f"Debug response: I received '{user_input}' at {timestamp}"
        })
    
    # Display messages
    if st.session_state.debug_messages:
        st.subheader("Message History")
        for msg in reversed(st.session_state.debug_messages[-10:]):  # Show last 10
            st.text(f"[{msg['time']}] You: {msg['message']}")
            st.text(f"[{msg['time']}] Bot: {msg['response']}")
            st.divider()
    
    # GitHub Test Section
    st.header("GitHub Integration Test")
    
    if github_token and github_owner and github_repo:
        if st.button("🧪 Test GitHub Connection"):
            try:
                import requests
                
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                # Test API access
                response = requests.get(
                    f"https://api.github.com/repos/{github_owner}/{github_repo}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    repo_data = response.json()
                    st.success(f"✅ GitHub connection successful!")
                    st.json({
                        "repo_name": repo_data["name"],
                        "full_name": repo_data["full_name"],
                        "private": repo_data["private"],
                        "open_issues": repo_data["open_issues_count"]
                    })
                else:
                    st.error(f"❌ GitHub connection failed: {response.status_code}")
                    st.code(response.text)
                    
            except Exception as e:
                st.error(f"❌ GitHub test error: {str(e)}")
        
        # Manual issue creation test
        st.subheader("Create Test GitHub Issue")
        test_title = st.text_input("Issue Title:", value="Test Issue from Support Bot")
        test_body = st.text_area("Issue Body:", value="This is a test issue created from the support bot debug interface.")
        
        if st.button("Create Test Issue"):
            try:
                import requests
                
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json"
                }
                
                issue_data = {
                    "title": test_title,
                    "body": test_body,
                    "labels": ["test", "support-bot"]
                }
                
                response = requests.post(
                    f"https://api.github.com/repos/{github_owner}/{github_repo}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issue = response.json()
                    st.success(f"✅ Test issue created: #{issue['number']}")
                    st.markdown(f"[View Issue]({issue['html_url']})")
                else:
                    st.error(f"❌ Failed to create issue: {response.status_code}")
                    st.code(response.text)
                    
            except Exception as e:
                st.error(f"❌ Error creating test issue: {str(e)}")
    else:
        st.warning("GitHub credentials not configured. Cannot test GitHub integration.")
    
    # Setup Instructions
    st.header("Setup Instructions")
    
    st.markdown("""
    ### Required Environment Variables
    
    Create a `.env` file with:
    ```env
    # OpenAI Configuration
    OPENAI_API_KEY=your_openai_api_key_here
    
    # GitHub Configuration (optional)
    GITHUB_TOKEN=your_github_token_here
    GITHUB_REPO_OWNER=your_github_username
    GITHUB_REPO_NAME=your_repository_name
    ```
    
    ### Getting API Keys
    
    **OpenAI API Key:**
    1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
    2. Create new secret key
    3. Copy the key
    
    **GitHub Token:**
    1. Go to GitHub Settings → Developer settings → Personal access tokens
    2. Generate new token (classic)
    3. Select `repo` scope
    4. Copy the token
    
    ### Required Python Packages
    ```bash
    pip install streamlit openai python-dotenv requests
    ```
    """)

if __name__ == "__main__":
    main()