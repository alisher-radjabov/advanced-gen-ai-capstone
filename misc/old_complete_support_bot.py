import streamlit as st
import logging
import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv
import uuid
import time

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Support Bot",
    page_icon="🤖",
    layout="wide"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION AND DATA MODELS
# ============================================================================

@dataclass
class Config:
    """Application configuration."""
    data_directory: str = "data"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    max_tokens: int = 500

@dataclass
class SupportTicket:
    """Support ticket data model."""
    id: str = field(default_factory=lambda: f"TICK-{str(uuid.uuid4())[:8].upper()}")
    user_name: str = ""
    email: str = ""
    summary: str = ""
    description: str = ""
    status: str = "open"
    priority: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None

# ============================================================================
# OPENAI CLIENT SETUP
# ============================================================================

def get_openai_client():
    """Initialize and return OpenAI client with proper API key handling."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Test the connection with a simple call
        client.models.list()
        return client
    except Exception as e:
        logger.error(f"OpenAI connection failed: {e}")
        return None

# ============================================================================
# DOCUMENT PROCESSING (SIMPLIFIED)
# ============================================================================

class SimpleDocumentProcessor:
    """Simplified document processor for demo purposes."""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        self.documents = []
    
    def load_documents(self) -> List[Dict]:
        """Load sample documents for demo."""
        if not self.documents:
            # Create sample documents for demo
            self.documents = [
                {
                    "content": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions in the email you receive.",
                    "metadata": {"source": "user_guide.pdf", "page": 1}
                },
                {
                    "content": "API authentication requires a valid API key. Include the key in the Authorization header as 'Bearer YOUR_API_KEY'. Rate limits apply: 1000 requests per hour for standard accounts.",
                    "metadata": {"source": "api_documentation.pdf", "page": 3}
                },
                {
                    "content": "For billing questions, contact our support team at billing@company.com. Premium accounts include priority support and extended features.",
                    "metadata": {"source": "billing_faq.pdf", "page": 2}
                },
                {
                    "content": "System maintenance is scheduled every Sunday from 2-4 AM UTC. During this time, some services may be temporarily unavailable.",
                    "metadata": {"source": "system_info.pdf", "page": 1}
                }
            ]
        return self.documents

# ============================================================================
# SIMPLE QA SYSTEM
# ============================================================================

class SimpleQASystem:
    """Simplified QA system that works without complex dependencies."""
    
    def __init__(self, config: Config, document_processor: SimpleDocumentProcessor):
        self.config = config
        self.document_processor = document_processor
        self.openai_client = get_openai_client()
        self.documents = document_processor.load_documents()
    
    def ask_question(self, question: str) -> Dict:
        """Answer a question using simple keyword matching and OpenAI."""
        try:
            # Find relevant documents using simple keyword matching
            relevant_docs = self._find_relevant_documents(question)
            
            if self.openai_client and relevant_docs:
                # Use OpenAI to generate answer
                context = "\n".join([doc["content"] for doc in relevant_docs])
                answer = self._generate_openai_answer(question, context)
            else:
                # Fallback to simple matching
                answer = self._generate_simple_answer(question, relevant_docs)
            
            return {
                "answer": answer,
                "source_documents": relevant_docs
            }
        except Exception as e:
            logger.error(f"Error in QA system: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again or contact support.",
                "source_documents": []
            }
    
    def _find_relevant_documents(self, question: str) -> List[Dict]:
        """Find relevant documents using keyword matching."""
        question_lower = question.lower()
        relevant_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Simple keyword matching
            if any(word in content_lower for word in question_lower.split() if len(word) > 3):
                relevant_docs.append(doc)
        
        return relevant_docs[:3]  # Return top 3 matches
    
    def _generate_openai_answer(self, question: str, context: str) -> str:
        """Generate answer using OpenAI."""
        try:
            prompt = f"""
            Based on the following documentation context, answer the user's question.
            If the answer is not in the context, say so clearly.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return self._generate_simple_answer(question, self._find_relevant_documents(question))
    
    def _generate_simple_answer(self, question: str, relevant_docs: List[Dict]) -> str:
        """Generate a simple answer using keyword matching."""
        if not relevant_docs:
            return "I couldn't find relevant information in the documentation. Would you like me to create a support ticket for you?"
        
        # Return the most relevant document content
        return f"Based on the documentation: {relevant_docs[0]['content']}"
    
    def is_answer_uncertain(self, answer: str) -> bool:
        """Check if the answer indicates uncertainty."""
        uncertainty_phrases = [
            "i don't know", "i'm not sure", "i couldn't find", 
            "unclear", "uncertain", "might be", "possibly"
        ]
        return any(phrase in answer.lower() for phrase in uncertainty_phrases)

# ============================================================================
# TICKET SYSTEM
# ============================================================================

class TicketSystem:
    """Simple ticket management system."""
    
    def __init__(self):
        self.tickets = []
    
    def create_ticket(self, user_name: str, email: str, summary: str, 
                     description: str, priority: str = "medium") -> SupportTicket:
        """Create a new support ticket."""
        ticket = SupportTicket(
            user_name=user_name,
            email=email,
            summary=summary,
            description=description,
            priority=priority
        )
        self.tickets.append(ticket)
        return ticket
    
    def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get a ticket by ID."""
        return next((t for t in self.tickets if t.id == ticket_id), None)
    
    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status."""
        ticket = self.get_ticket(ticket_id)
        if ticket:
            ticket.status = status
            ticket.updated_at = datetime.now()
            return True
        return False

# ============================================================================
# GITHUB INTEGRATION
# ============================================================================

class GitHubIssuesIntegration:
    """Integration with GitHub Issues for support ticket management."""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        if not self.github_token:
            raise ValueError("GitHub token is required.")
        
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict:
        """Create a new GitHub issue."""
        try:
            issue_data = {
                "title": title,
                "body": body,
                "labels": labels or ["support"]
            }
            
            response = requests.post(
                f"{self.base_url}/issues",
                headers=self.headers,
                json=issue_data,
                timeout=10
            )
            
            if response.status_code == 201:
                issue = response.json()
                return {
                    "success": True,
                    "issue_number": issue["number"],
                    "issue_url": issue["html_url"],
                    "message": f"GitHub issue #{issue['number']} created successfully"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to create GitHub issue: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while creating GitHub issue"
            }
    
    def add_comment(self, issue_number: int, comment: str) -> Dict:
        """Add a comment to a GitHub issue."""
        try:
            comment_data = {"body": comment}
            
            response = requests.post(
                f"{self.base_url}/issues/{issue_number}/comments",
                headers=self.headers,
                json=comment_data,
                timeout=10
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "message": f"Comment added to issue #{issue_number}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to add comment: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return {"success": False, "error": str(e)}

def create_github_integration() -> Optional[GitHubIssuesIntegration]:
    """Create GitHub integration if credentials are available."""
    try:
        repo_owner = os.getenv("GITHUB_REPO_OWNER")
        repo_name = os.getenv("GITHUB_REPO_NAME") 
        github_token = os.getenv("GITHUB_TOKEN")
        
        if repo_owner and repo_name and github_token:
            return GitHubIssuesIntegration(repo_owner, repo_name, github_token)
        return None
        
    except Exception as e:
        logger.error(f"Failed to create GitHub integration: {e}")
        return None

# ============================================================================
# FUNCTION REGISTRY
# ============================================================================

class FunctionRegistry:
    """Registry for available functions that the bot can call."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.github_integration = create_github_integration()
        
    def create_support_ticket(self, summary: str, description: str, priority: str = "medium") -> Dict:
        """Create a support ticket and optionally a GitHub issue."""
        try:
            user_name = st.session_state.get("user_name", "Anonymous User")
            email = st.session_state.get("user_email", "user@example.com")
            
            # Create the ticket
            ticket = self.app.ticket_system.create_ticket(
                user_name=user_name,
                email=email,
                summary=summary,
                description=description,
                priority=priority
            )
            
            # Add to session state
            st.session_state.tickets.append(ticket)
            
            message = f"Support ticket {ticket.id} created successfully"
            result = {
                "success": True,
                "ticket_id": ticket.id,
                "priority": priority
            }
            
            # Try to create GitHub issue if integration is available
            if self.github_integration:
                github_result = self._create_github_issue_from_ticket(ticket)
                if github_result["success"]:
                    ticket.github_issue_number = github_result["issue_number"]
                    ticket.github_issue_url = github_result["issue_url"]
                    message += f"\n🔗 GitHub issue #{github_result['issue_number']} created"
                    message += f"\n📋 View at: {github_result['issue_url']}"
                    result["github_issue_number"] = github_result["issue_number"]
                    result["github_issue_url"] = github_result["issue_url"]
                else:
                    message += f"\n⚠️ GitHub issue creation failed: {github_result['message']}"
            
            result["message"] = message
            return result
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support ticket"
            }
    
    def _create_github_issue_from_ticket(self, ticket: SupportTicket) -> Dict:
        """Create a GitHub issue from a support ticket."""
        title = f"[Support] {ticket.summary}"
        
        body = f"""## Support Ticket Details

**Ticket ID:** {ticket.id}
**User:** {ticket.user_name} ({ticket.email})
**Priority:** {ticket.priority}
**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Description
{ticket.description}

---
*This issue was automatically created from support ticket {ticket.id}*
"""
        
        labels = ["support-ticket", f"priority-{ticket.priority}"]
        
        return self.github_integration.create_issue(title, body, labels)
    
    def search_documentation(self, query: str, max_results: int = 5) -> Dict:
        """Search through documentation."""
        try:
            if not self.app.qa_system:
                self.app.qa_system = self.app._load_qa_system()
            
            result = self.app.qa_system.ask_question(query)
            sources = result.get("source_documents", [])[:max_results]
            
            return {
                "success": True,
                "results": sources,
                "answer": result["answer"],
                "message": f"Found {len(sources)} relevant documents"
            }
        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search documentation"
            }
    
    def get_system_status(self) -> Dict:
        """Get current system status."""
        try:
            docs = self.app.document_processor.load_documents()
            qa_ready = self.app.qa_system is not None
            github_configured = self.github_integration is not None
            openai_available = get_openai_client() is not None
            
            return {
                "success": True,
                "status": {
                    "qa_system": "online" if qa_ready else "offline",
                    "documents_loaded": len(docs),
                    "tickets_count": len(st.session_state.get("tickets", [])),
                    "github_integration": "enabled" if github_configured else "disabled",
                    "openai_connection": "connected" if openai_available else "disconnected",
                    "timestamp": datetime.now().isoformat()
                },
                "message": "System status retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get system status"
            }
    
    def get_ticket_status(self, ticket_id: str) -> Dict:
        """Get status of a specific ticket."""
        try:
            tickets = st.session_state.get("tickets", [])
            ticket = next((t for t in tickets if t.id == ticket_id), None)
            
            if not ticket:
                return {
                    "success": False,
                    "message": f"Ticket {ticket_id} not found"
                }
            
            ticket_info = {
                "id": ticket.id,
                "summary": ticket.summary,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_at": ticket.created_at.isoformat(),
                "user_name": ticket.user_name
            }
            
            if ticket.github_issue_number:
                ticket_info["github_issue"] = {
                    "number": ticket.github_issue_number,
                    "url": ticket.github_issue_url
                }
            
            return {
                "success": True,
                "ticket": ticket_info,
                "message": f"Ticket {ticket_id} status retrieved"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_user_tickets(self, status_filter: str = "all") -> Dict:
        """List all tickets for the current user."""
        try:
            user_email = st.session_state.get("user_email", "user@example.com")
            tickets = st.session_state.get("tickets", [])
            
            user_tickets = [t for t in tickets if t.email == user_email]
            
            if status_filter != "all":
                user_tickets = [t for t in user_tickets if t.status == status_filter]
            
            ticket_list = []
            for ticket in user_tickets:
                ticket_data = {
                    "id": ticket.id,
                    "summary": ticket.summary,
                    "status": ticket.status,
                    "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                    "priority": ticket.priority
                }
                
                if ticket.github_issue_number:
                    ticket_data["github_issue"] = {
                        "number": ticket.github_issue_number,
                        "url": ticket.github_issue_url
                    }
                
                ticket_list.append(ticket_data)
            
            return {
                "success": True,
                "tickets": ticket_list,
                "count": len(ticket_list),
                "message": f"Found {len(ticket_list)} tickets for user"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def escalate_ticket(self, ticket_id: str, reason: str) -> Dict:
        """Escalate a ticket to higher priority."""
        try:
            tickets = st.session_state.get("tickets", [])
            ticket = next((t for t in tickets if t.id == ticket_id), None)
            
            if not ticket:
                return {"success": False, "message": f"Ticket {ticket_id} not found"}
            
            old_priority = ticket.priority
            priority_map = {"low": "medium", "medium": "high", "high": "urgent"}
            ticket.priority = priority_map.get(old_priority, "urgent")
            ticket.status = "escalated"
            ticket.updated_at = datetime.now()
            
            message = f"Ticket {ticket_id} escalated from {old_priority} to {ticket.priority}"
            
            # Add comment to GitHub issue if available
            if self.github_integration and ticket.github_issue_number:
                escalation_comment = f"""
🚨 **TICKET ESCALATED**

- **Previous Priority:** {old_priority}
- **New Priority:** {ticket.priority}
- **Reason:** {reason}
- **Escalated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This ticket requires immediate attention.
"""
                github_result = self.github_integration.add_comment(
                    ticket.github_issue_number, escalation_comment
                )
                if github_result["success"]:
                    message += "\n🔗 GitHub issue updated with escalation notice"
            
            return {
                "success": True,
                "message": message,
                "new_priority": ticket.priority,
                "reason": reason
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_function(self, function_name: str, parameters: Dict) -> Dict:
        """Execute a function call."""
        functions = {
            "create_support_ticket": self.create_support_ticket,
            "search_documentation": self.search_documentation,
            "get_system_status": self.get_system_status,
            "get_ticket_status": self.get_ticket_status,
            "list_user_tickets": self.list_user_tickets,
            "escalate_ticket": self.escalate_ticket
        }
        
        if function_name not in functions:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}",
                "message": "Function not available"
            }
        
        try:
            return functions[function_name](**parameters)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing {function_name}"
            }

# ============================================================================
# ENHANCED QA SYSTEM WITH FUNCTION CALLING
# ============================================================================

class EnhancedQASystem(SimpleQASystem):
    """Enhanced QA System with function calling capabilities."""
    
    def __init__(self, config: Config, document_processor: SimpleDocumentProcessor, function_registry: FunctionRegistry):
        super().__init__(config, document_processor)
        self.function_registry = function_registry
    
    def ask_question_with_functions(self, question: str) -> Dict:
        """Process question and determine if function calling is needed."""
        try:
            # Get regular answer first
            regular_result = self.ask_question(question)
            
            # Analyze if function calling is needed
            function_call = self._analyze_for_function_call(question, regular_result["answer"])
            
            if function_call:
                # Execute the function
                function_result = self.function_registry.execute_function(
                    function_call["name"], 
                    function_call["parameters"]
                )
                
                # Combine results
                enhanced_answer = self._combine_answer_with_function_result(
                    regular_result["answer"],
                    function_call,
                    function_result
                )
                
                return {
                    "answer": enhanced_answer,
                    "source_documents": regular_result.get("source_documents", []),
                    "function_called": function_call["name"],
                    "function_result": function_result
                }
            
            return regular_result
            
        except Exception as e:
            logger.error(f"Error in ask_question_with_functions: {e}")
            return {
                "answer": f"I encountered an error: {str(e)}. Please try again.",
                "source_documents": [],
                "function_called": None,
                "function_result": None
            }
    
    def _analyze_for_function_call(self, question: str, answer: str) -> Optional[Dict]:
        """Analyze question to determine if a function should be called."""
        question_lower = question.lower()
        
        # Ticket creation triggers
        if any(phrase in question_lower for phrase in [
            "create ticket", "open ticket", "file ticket", "submit ticket",
            "need help", "escalate", "contact support"
        ]) or self.is_answer_uncertain(answer):
            return {
                "name": "create_support_ticket",
                "parameters": {
                    "summary": question[:100],
                    "description": f"User question: {question}\nBot response: {answer}",
                    "priority": "medium"
                }
            }
        
        # Documentation search triggers
        if any(phrase in question_lower for phrase in [
            "search for", "find information", "look up", "documentation about"
        ]):
            return {
                "name": "search_documentation",
                "parameters": {"query": question, "max_results": 5}
            }
        
        # System status triggers
        if any(phrase in question_lower for phrase in [
            "system status", "is system working", "health check", "status check"
        ]):
            return {"name": "get_system_status", "parameters": {}}
        
        # Ticket status triggers
        if any(phrase in question_lower for phrase in [
            "ticket status", "check ticket", "my tickets", "ticket update"
        ]):
            # Try to extract ticket ID
            words = question.split()
            for word in words:
                if word.startswith("TICK-"):
                    return {
                        "name": "get_ticket_status",
                        "parameters": {"ticket_id": word}
                    }
            
            # List all tickets if no specific ID
            return {"name": "list_user_tickets", "parameters": {"status_filter": "all"}}
        
        return None
    
    def _combine_answer_with_function_result(self, answer: str, function_call: Dict, function_result: Dict) -> str:
        """Combine the regular answer with function execution results."""
        if not function_result.get("success"):
            return f"{answer}\n\n⚠️ {function_result.get('message', 'Function execution failed')}"
        
        function_name = function_call["name"]
        
        if function_name == "create_support_ticket":
            ticket_id = function_result.get("ticket_id")
            base_msg = f"\n\n🎫 I've created support ticket {ticket_id} for you."
            
            if function_result.get("github_issue_number"):
                github_url = function_result.get("github_issue_url")
                base_msg += f"\n🔗 GitHub issue #{function_result['github_issue_number']} also created."
                if github_url:
                    base_msg += f"\n📋 [View on GitHub]({github_url})"
            
            return f"{answer}{base_msg}"
        
        elif function_name == "search_documentation":
            results = function_result.get("results", [])
            if results:
                sources_text = "\n".join([f"• {r.get('metadata', {}).get('source', 'Unknown')}" for r in results])
                return f"{function_result.get('answer', answer)}\n\n📚 Sources:\n{sources_text}"
        
        elif function_name == "get_system_status":
            status = function_result.get("status", {})
            status_text = f"""
🔍 **System Status:**
• QA System: {status.get('qa_system', 'unknown')}
• OpenAI: {status.get('openai_connection', 'unknown')}
• Documents: {status.get('documents_loaded', 0)} loaded
• GitHub: {status.get('github_integration', 'disabled')}
• Active Tickets: {status.get('tickets_count', 0)}
"""
            return status_text
        
        elif function_name == "get_ticket_status":
            ticket = function_result.get("ticket", {})
            ticket_text = f"""
🎫 **Ticket {ticket.get('id', 'Unknown')}:**
• Status: {ticket.get('status', 'Unknown')}
• Priority: {ticket.get('priority', 'Unknown')}
• Created: {ticket.get('created_at', 'Unknown')}
"""
            if ticket.get("github_issue"):
                github_info = ticket["github_issue"]
                ticket_text += f"• GitHub Issue: #{github_info['number']}\n"
            
            return ticket_text
        
        elif function_name == "list_user_tickets":
            tickets = function_result.get("tickets", [])
            if tickets:
                ticket_list = "\n".join([
                    f"• **{t['id']}**: {t['summary']} ({t['status']}) - Priority: {t['priority']}"
                    for t in tickets
                ])
                return f"🎫 **Your Support Tickets ({len(tickets)} total):**\n{ticket_list}"
            else:
                return "You don't have any support tickets yet."
        
        elif function_name == "escalate_ticket":
            return f"⬆️ {function_result.get('message', 'Ticket escalated')}"
        
        return f"{answer}\n\n✅ {function_result.get('message', 'Function executed successfully')}"

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class SupportBotApp:
    """Main Streamlit application for the Support Bot with function calling."""
    
    def __init__(self):
        self.config = Config()
        self.document_processor = SimpleDocumentProcessor(self.config.data_directory)
        self.ticket_system = TicketSystem()
        self.function_registry = FunctionRegistry(self)
        self.qa_system = None
        
        self._setup_streamlit()
        self._initialize_session_state()
    
    def _setup_streamlit(self):
        """Configure Streamlit page content (page_config already set globally)."""
        # Page content is now set in the main() function to avoid duplication
        pass
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "history" not in st.session_state:
            st.session_state.history = []
        if "tickets" not in st.session_state:
            st.session_state.tickets = []
        if "function_calls_log" not in st.session_state:
            st.session_state.function_calls_log = []
        if "user_name" not in st.session_state:
            st.session_state.user_name = "Alex Smith"
        if "user_email" not in st.session_state:
            st.session_state.user_email = "alex@example.com"
    
    def _load_qa_system(self):
        """Load and initialize the QA system."""
        try:
            return EnhancedQASystem(self.config, self.document_processor, self.function_registry)
        except Exception as e:
            logger.error(f"Error loading QA system: {e}")
            return SimpleQASystem(self.config, self.document_processor)
    
    @st.cache_resource
    def load_qa_system(_self):
        """Load and cache the QA system."""
        return _self._load_qa_system()
    
    def handle_user_input(self, user_input: str) -> Tuple[str, List, Optional[str]]:
        """Process user input with function calling capabilities."""
        try:
            if not self.qa_system:
                self.qa_system = self.load_qa_system()
            
            # Use enhanced QA system with function calling if available
            if hasattr(self.qa_system, 'ask_question_with_functions'):
                result = self.qa_system.ask_question_with_functions(user_input)
            else:
                # Fallback to basic QA
                result = self.qa_system.ask_question(user_input)
                result.update({"function_called": None, "function_result": None})
            
            answer = result["answer"]
            sources = result.get("source_documents", [])
            function_called = result.get("function_called")
            function_result = result.get("function_result")
            
            # Log function call if one was made
            if function_called:
                st.session_state.function_calls_log.append({
                    "timestamp": datetime.now(),
                    "function": function_called,
                    "question": user_input,
                    "result": function_result
                })
            
            # Add to history
            st.session_state.history.append({
                "question": user_input,
                "answer": answer,
                "sources": sources,
                "function_called": function_called,
                "timestamp": datetime.now()
            })
            
            return answer, sources, function_called
            
        except Exception as e:
            logger.error(f"Error handling user input: {e}")
            error_answer = f"I encountered an error: {str(e)}. Please try again or contact support."
            
            st.session_state.history.append({
                "question": user_input,
                "answer": error_answer,
                "sources": [],
                "function_called": None,
                "timestamp": datetime.now()
            })
            
            return error_answer, [], None
    
    def display_chat_history(self):
        """Display the chat history with function call indicators."""
        if not st.session_state.history:
            st.info("💬 Start a conversation by asking a question above!")
            return
        
        for i, entry in enumerate(reversed(st.session_state.history)):
            question = entry["question"]
            answer = entry["answer"]
            sources = entry["sources"]
            function_called = entry.get("function_called")
            timestamp = entry.get("timestamp", datetime.now())
            
            # Create a container for each message
            with st.container():
                # Display timestamp
                st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')}")
                
                # User message
                st.markdown(f"**👤 You:** {question}")
                
                # Function call indicator
                if function_called:
                    st.info(f"🔧 Action taken: `{function_called}`")
                
                # Bot response
                st.markdown(f"**🤖 Bot:** {answer}")
                
                # Display sources if available
                if sources:
                    with st.expander("📄 Sources"):
                        for doc in sources:
                            if isinstance(doc, dict):
                                source = doc.get('metadata', {}).get('source', 'Unknown')
                                page = doc.get('metadata', {}).get('page', '?')
                            else:
                                source = getattr(doc, 'metadata', {}).get('source', 'Unknown')
                                page = getattr(doc, 'metadata', {}).get('page', '?')
                            st.markdown(f"• {source} (page {page})")
                
                st.divider()
    
    def display_sidebar(self):
        """Display sidebar with user info, tickets, and quick actions."""
        with st.sidebar:
            st.header("👤 User Information")
            st.session_state.user_name = st.text_input("Name", value=st.session_state.user_name)
            st.session_state.user_email = st.text_input("Email", value=st.session_state.user_email)
            
            st.header("⚡ Quick Actions")
            
            # Quick action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 System Status"):
                    result = self.function_registry.get_system_status()
                    if result["success"]:
                        status = result["status"]
                        st.success("System Status Retrieved!")
                        for key, value in status.items():
                            if key != "timestamp":
                                st.caption(f"{key}: {value}")
            
            with col2:
                if st.button("🎫 My Tickets"):
                    result = self.function_registry.list_user_tickets()
                    if result["success"]:
                        count = result["count"]
                        st.success(f"Found {count} tickets")
            
            # Manual ticket creation
            st.header("🎫 Create Ticket")
            with st.expander("Manual Ticket Creation"):
                ticket_summary = st.text_input("Issue Summary", key="manual_summary")
                ticket_description = st.text_area("Description", key="manual_description")
                ticket_priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"], index=1)
                
                if st.button("Create Ticket"):
                    if ticket_summary and ticket_description:
                        result = self.function_registry.create_support_ticket(
                            ticket_summary, ticket_description, ticket_priority
                        )
                        if result["success"]:
                            st.success(f"Ticket {result['ticket_id']} created!")
                        else:
                            st.error(result["message"])
                    else:
                        st.warning("Please fill in both summary and description")
            
            st.header("🎫 Support Tickets")
            if st.session_state.tickets:
                for ticket in st.session_state.tickets[-5:]:  # Show last 5 tickets
                    with st.expander(f"Ticket {ticket.id}"):
                        st.write(f"**Summary:** {ticket.summary}")
                        st.write(f"**Status:** {ticket.status}")
                        st.write(f"**Priority:** {ticket.priority}")
                        st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        if ticket.github_issue_url:
                            st.markdown(f"🔗 [View on GitHub]({ticket.github_issue_url})")
                        
                        # Escalation button
                        if st.button(f"⬆️ Escalate", key=f"escalate_{ticket.id}"):
                            result = self.function_registry.escalate_ticket(
                                ticket.id, 
                                "User-requested escalation"
                            )
                            if result["success"]:
                                st.success(result["message"])
                                st.rerun()
                            else:
                                st.error(result["message"])
            else:
                st.info("No tickets created yet.")
            
            # Function calls log
            if st.session_state.function_calls_log:
                st.header("📞 Recent Actions")
                with st.expander(f"Activity Log ({len(st.session_state.function_calls_log)})"):
                    for call in reversed(st.session_state.function_calls_log[-10:]):  # Show last 10
                        st.caption(f"{call['timestamp'].strftime('%H:%M:%S')} - {call['function']}")
    
    def display_function_help(self):
        """Display available functions and examples."""
        with st.expander("🔧 Available Actions & Examples"):
            st.markdown("""
            **Support Tickets:**
            - "Create a ticket for login issues"
            - "I need help with billing"
            - "Check ticket TICK-12345678"
            - "Show me my tickets"
            - "Escalate ticket TICK-12345678"
            
            **Documentation:**
            - "How do I reset my password?"
            - "Search documentation for API setup"
            - "Find information about billing"
            
            **System:**
            - "What's the system status?"
            - "Is everything working?"
            
            **GitHub Integration:**
            - Tickets automatically create GitHub issues (if configured)
            - Track issues directly from tickets
            """)
    
    def display_configuration_status(self):
        """Display current configuration status."""
        st.subheader("🔧 Configuration Status")
        
        # API Keys status
        openai_key = os.getenv("OPENAI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        github_owner = os.getenv("GITHUB_REPO_OWNER")
        github_repo = os.getenv("GITHUB_REPO_NAME")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.caption("**OpenAI Configuration:**")
            if openai_key:
                st.success("✅ API Key configured")
                # Test connection
                client = get_openai_client()
                if client:
                    st.success("✅ Connection verified")
                else:
                    st.error("❌ Connection failed")
            else:
                st.error("❌ API Key missing")
        
        with col2:
            st.caption("**GitHub Integration:**")
            if github_token and github_owner and github_repo:
                st.success("✅ Fully configured")
                st.caption(f"Repo: {github_owner}/{github_repo}")
            elif github_token:
                st.warning("⚠️ Partial configuration")
            else:
                st.info("ℹ️ Not configured")
    
    def run(self):
        """Run the Streamlit application."""
        try:
            # Check for missing configurations and show warnings
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.warning("⚠️ OpenAI API key not configured. Using basic functionality.")
                with st.expander("🔧 Setup OpenAI"):
                    st.code("""
# Add to your .env file:
OPENAI_API_KEY=your_openai_api_key_here

# Or set environment variable:
export OPENAI_API_KEY=your_openai_api_key_here
""")
            
            # Display sidebar
            self.display_sidebar()
            
            # Main content area
            main_col, status_col = st.columns([3, 1])
            
            with main_col:
                # Display function help
                self.display_function_help()
                
                # Main input
                user_input = st.text_input(
                    "💬 Ask a question or request an action:",
                    key="user_input",
                    placeholder="Try: 'How do I reset my password?' or 'Create a ticket for login issues'"
                )
                
                if user_input:
                    with st.spinner("🤔 Processing your request..."):
                        try:
                            answer, sources, function_called = self.handle_user_input(user_input)
                            
                            if function_called:
                                st.success(f"✅ Action completed: {function_called}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            logger.error(f"Error in user input handling: {e}")
                
                # Display chat history
                st.subheader("💬 Conversation History")
                self.display_chat_history()
            
            with status_col:
                self.display_configuration_status()
                
                st.divider()
                
                # System metrics
                st.subheader("📊 Metrics")
                docs = self.document_processor.load_documents()
                tickets = st.session_state.get("tickets", [])
                function_calls = st.session_state.get("function_calls_log", [])
                
                st.metric("Documents", len(docs))
                st.metric("Total Tickets", len(tickets))
                st.metric("Function Calls", len(function_calls))
                
                # Recent activity
                if function_calls:
                    st.caption("**Recent Activity:**")
                    for call in reversed(function_calls[-3:]):
                        st.caption(f"• {call['function']} ({call['timestamp'].strftime('%H:%M')})")
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"❌ Application error: {str(e)}")
            
            # Fallback basic interface
            st.markdown("## 🔧 Basic Mode")
            st.info("Running in basic mode due to configuration issues.")
            
            basic_input = st.text_input("Ask a basic question:", key="basic_input")
            if basic_input:
                st.write(f"**👤 You:** {basic_input}")
                st.write("**🤖 Bot:** I'm running in basic mode. Please check the configuration above.")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_environment_guide():
    """Display environment setup guide."""
    st.header("🛠️ Environment Setup Guide")
    
    st.markdown("""
    ### Step 1: Install Dependencies
    ```bash
    pip install streamlit openai python-dotenv requests
    ```
    
    ### Step 2: Create .env File
    Create a `.env` file in your project directory:
    """)
    
    st.code("""
# Required for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Optional - for GitHub Issues integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=your_repository_name
""")
    
    st.markdown("""
    ### Step 3: Get API Keys
    
    **OpenAI API Key:**
    1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
    2. Click "Create new secret key"
    3. Copy the key and add to .env file
    
    **GitHub Token (Optional):**
    1. Go to GitHub Settings → Developer settings → Personal access tokens
    2. Generate new token (classic)
    3. Select `repo` scope for private repos or `public_repo` for public repos
    4. Copy token and add to .env file
    
    ### Step 4: Run the Application
    ```bash
    streamlit run app.py
    ```
    """)

def test_configuration():
    """Test and display configuration status."""
    st.header("🧪 Configuration Test")
    
    tests = []
    
    # Test environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_REPO_OWNER")
    github_repo = os.getenv("GITHUB_REPO_NAME")
    
    tests.append(("OpenAI API Key", "✅ Found" if openai_key else "❌ Missing", openai_key is not None))
    tests.append(("GitHub Token", "✅ Found" if github_token else "ℹ️ Optional", True))
    tests.append(("GitHub Owner", "✅ Set" if github_owner else "ℹ️ Optional", True))
    tests.append(("GitHub Repo", "✅ Set" if github_repo else "ℹ️ Optional", True))
    
    # Test OpenAI connection
    if openai_key:
        client = get_openai_client()
        tests.append(("OpenAI Connection", "✅ Connected" if client else "❌ Failed", client is not None))
    
    # Test GitHub connection
    if github_token and github_owner and github_repo:
        try:
            headers = {"Authorization": f"token {github_token}"}
            response = requests.get(f"https://api.github.com/repos/{github_owner}/{github_repo}", headers=headers, timeout=5)
            github_ok = response.status_code == 200
            tests.append(("GitHub Connection", "✅ Connected" if github_ok else "❌ Failed", github_ok))
        except:
            tests.append(("GitHub Connection", "❌ Failed", False))
    
    # Display test results
    for test_name, status, passed in tests:
        if "✅" in status:
            st.success(f"{test_name}: {status}")
        elif "❌" in status:
            st.error(f"{test_name}: {status}")
        else:
            st.info(f"{test_name}: {status}")
    
    return all(test[2] for test in tests if "❌" in test[1])

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

def main():
    """Main application entry point."""
    
    # Page title and description (page_config already set at top)
    st.title("🤖 Product Support Chatbot")
    st.markdown("Ask questions about your product documentation or get help with support!")
    
    # Add a configuration check option in sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        if st.button("📖 Show Setup Guide"):
            setup_environment_guide()
            return
        
        if st.button("🧪 Test Configuration"):
            if test_configuration():
                st.success("🎉 All tests passed!")
            else:
                st.warning("⚠️ Some tests failed.")
            return
    
    # Run the main application
    try:
        app = SupportBotApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        st.error(f"❌ Failed to start application: {str(e)}")
        
        # Show setup guide as fallback
        st.markdown("---")
        st.subheader("🛠️ Troubleshooting")
        setup_environment_guide()

if __name__ == "__main__":
    main()