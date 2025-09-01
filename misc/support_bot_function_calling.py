import streamlit as st
import logging
import json
from config import Config
from document_processor import DocumentProcessor
from qa_system import QASystem
from ticket_system import TicketSystem
from dotenv import load_dotenv
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_openai_client():
    """Initialize and return OpenAI client with proper API key handling."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("❌ OpenAI API key not found! Please set the OPENAI_API_KEY environment variable.")
        st.info("""
        To fix this:
        1. Create a `.env` file in your project directory
        2. Add: `OPENAI_API_KEY=your_api_key_here`
        3. Or set it as an environment variable: `export OPENAI_API_KEY=your_api_key_here`
        """)
        st.stop()
    
    try:
        client = OpenAI(api_key=api_key)
        # Test the connection
        client.models.list()
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
        st.info("Please check your API key and internet connection.")
        st.stop()

class FunctionRegistry:
    """Registry for available functions that the bot can call."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.functions = {
            "create_support_ticket": self.create_support_ticket,
            "search_documentation": self.search_documentation,
            "get_system_status": self.get_system_status,
            "get_ticket_status": self.get_ticket_status,
            "list_user_tickets": self.list_user_tickets,
            "escalate_ticket": self.escalate_ticket
        }
    
    def get_function_definitions(self) -> List[Dict]:
        """Return OpenAI function definitions for the available functions."""
        return [
            {
                "name": "create_support_ticket",
                "description": "Create a new support ticket for issues that cannot be resolved through documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of the issue"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Priority level of the ticket"
                        }
                    },
                    "required": ["summary", "description"]
                }
            },
            {
                "name": "search_documentation",
                "description": "Search through product documentation for specific information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for documentation"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_system_status",
                "description": "Get current system status and health information",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_ticket_status",
                "description": "Get the status of a specific support ticket",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "ID of the ticket to check"
                        }
                    },
                    "required": ["ticket_id"]
                }
            },
            {
                "name": "list_user_tickets",
                "description": "List all tickets for the current user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status_filter": {
                            "type": "string",
                            "enum": ["all", "open", "closed", "pending"],
                            "description": "Filter tickets by status",
                            "default": "all"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "escalate_ticket",
                "description": "Escalate a ticket to higher priority or specialized team",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "ID of the ticket to escalate"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for escalation"
                        }
                    },
                    "required": ["ticket_id", "reason"]
                }
            }
        ]
    
    def create_support_ticket(self, summary: str, description: str, priority: str = "medium") -> Dict:
        """Create a new support ticket."""
        try:
            user_name = st.session_state.get("user_name", "Anonymous User")
            email = st.session_state.get("user_email", "user@example.com")
            
            ticket = self.app.ticket_system.create_ticket(
                user_name=user_name,
                email=email,
                summary=summary,
                description=description,
                priority=priority
            )
            
            st.session_state.tickets.append(ticket)
            
            return {
                "success": True,
                "ticket_id": ticket.id,
                "message": f"Support ticket {ticket.id} created successfully",
                "priority": priority
            }
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support ticket"
            }
    
    def search_documentation(self, query: str, max_results: int = 5) -> Dict:
        """Search through documentation."""
        try:
            if not self.app.qa_system:
                self.app.qa_system = self.app.load_qa_system()
            
            result = self.app.qa_system.ask_question(query)
            sources = result.get("source_documents", [])[:max_results]
            
            search_results = []
            for doc in sources:
                search_results.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get('source', 'Unknown'),
                    "page": doc.metadata.get('page', '?')
                })
            
            return {
                "success": True,
                "results": search_results,
                "answer": result["answer"],
                "message": f"Found {len(search_results)} relevant documents"
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
            qa_ready = self.app.qa_system is not None and hasattr(self.app.qa_system, 'chain') and self.app.qa_system.chain is not None
            
            return {
                "success": True,
                "status": {
                    "qa_system": "online" if qa_ready else "offline",
                    "documents_loaded": len(docs),
                    "tickets_count": len(st.session_state.get("tickets", [])),
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
            
            return {
                "success": True,
                "ticket": {
                    "id": ticket.id,
                    "summary": ticket.summary,
                    "status": ticket.status,
                    "priority": getattr(ticket, 'priority', 'medium'),
                    "created_at": ticket.created_at.isoformat(),
                    "user_name": ticket.user_name
                },
                "message": f"Ticket {ticket_id} status retrieved"
            }
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get ticket status"
            }
    
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
                ticket_list.append({
                    "id": ticket.id,
                    "summary": ticket.summary,
                    "status": ticket.status,
                    "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                    "priority": getattr(ticket, 'priority', 'medium')
                })
            
            return {
                "success": True,
                "tickets": ticket_list,
                "count": len(ticket_list),
                "message": f"Found {len(ticket_list)} tickets for user"
            }
        except Exception as e:
            logger.error(f"Error listing user tickets: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list user tickets"
            }
    
    def escalate_ticket(self, ticket_id: str, reason: str) -> Dict:
        """Escalate a ticket to higher priority."""
        try:
            tickets = st.session_state.get("tickets", [])
            ticket = next((t for t in tickets if t.id == ticket_id), None)
            
            if not ticket:
                return {
                    "success": False,
                    "message": f"Ticket {ticket_id} not found"
                }
            
            # Update ticket priority and status
            old_priority = getattr(ticket, 'priority', 'medium')
            if old_priority == "low":
                ticket.priority = "medium"
            elif old_priority == "medium":
                ticket.priority = "high"
            elif old_priority == "high":
                ticket.priority = "urgent"
            
            ticket.status = "escalated"
            
            return {
                "success": True,
                "message": f"Ticket {ticket_id} escalated from {old_priority} to {ticket.priority}",
                "new_priority": ticket.priority,
                "reason": reason
            }
        except Exception as e:
            logger.error(f"Error escalating ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to escalate ticket"
            }
    
    def execute_function(self, function_name: str, parameters: Dict) -> Dict:
        """Execute a function call."""
        if function_name not in self.functions:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}",
                "message": "Function not available"
            }
        
        try:
            return self.functions[function_name](**parameters)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing {function_name}"
            }

class EnhancedQASystem(QASystem):
    """Enhanced QA System with function calling capabilities."""
    
    def __init__(self, config, document_processor, function_registry):
        super().__init__(config, document_processor)
        self.function_registry = function_registry
        self.openai_client = get_openai_client()
    
    def ask_question_with_functions(self, question: str) -> Dict:
        """Process question and determine if function calling is needed."""
        try:
            # First, try to get a regular answer
            regular_result = self.ask_question(question)
            
            # Use OpenAI to analyze if function calling is needed
            function_call = self._analyze_for_function_call_with_openai(question, regular_result["answer"])
            
            if function_call:
                # Execute the function
                function_result = self.function_registry.execute_function(
                    function_call["name"], 
                    function_call["parameters"]
                )
                
                # Combine regular answer with function result
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
            # Fallback to regular QA if function calling fails
            return self.ask_question(question)
    
    def _analyze_for_function_call_with_openai(self, question: str, answer: str) -> Optional[Dict]:
        """Use OpenAI to analyze if a function should be called."""
        try:
            system_prompt = """
            You are a function call analyzer. Determine if the user's question requires calling a specific function.
            
            Available functions:
            - create_support_ticket: For issues needing human support or when bot answer is uncertain
            - search_documentation: For finding specific information in docs
            - get_system_status: For system health checks
            - get_ticket_status: For checking specific ticket status
            - list_user_tickets: For listing user's tickets
            - escalate_ticket: For escalating existing tickets
            
            Respond with either:
            1. JSON object with function call: {"name": "function_name", "parameters": {...}}
            2. "NO_FUNCTION" if no function is needed
            
            Consider the user's question and the bot's answer uncertainty.
            """
            
            user_prompt = f"""
            User Question: {question}
            Bot Answer: {answer}
            
            Should a function be called?
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "NO_FUNCTION":
                return None
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback to rule-based detection
                return self._analyze_for_function_call_fallback(question, answer)
                
        except Exception as e:
            logger.warning(f"OpenAI function analysis failed: {e}, using fallback")
            return self._analyze_for_function_call_fallback(question, answer)
    
    def _analyze_for_function_call_fallback(self, question: str, answer: str) -> Optional[Dict]:
        """Fallback rule-based analysis for function calling."""
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
                "parameters": {
                    "query": question,
                    "max_results": 5
                }
            }
        
        # System status triggers
        if any(phrase in question_lower for phrase in [
            "system status", "is system working", "health check", "status check"
        ]):
            return {
                "name": "get_system_status",
                "parameters": {}
            }
        
        # Ticket status triggers
        if any(phrase in question_lower for phrase in [
            "ticket status", "check ticket", "my tickets", "ticket update"
        ]):
            # Try to extract ticket ID
            words = question.split()
            for word in words:
                if word.startswith("TICK-") or word.isdigit():
                    return {
                        "name": "get_ticket_status",
                        "parameters": {"ticket_id": word}
                    }
            
            # If no specific ticket ID, list all user tickets
            return {
                "name": "list_user_tickets",
                "parameters": {"status_filter": "all"}
            }
        
        return None
    
    def _combine_answer_with_function_result(self, answer: str, function_call: Dict, function_result: Dict) -> str:
        """Combine the regular answer with function execution results."""
        if not function_result.get("success"):
            return f"{answer}\n\n⚠️ {function_result.get('message', 'Function execution failed')}"
        
        function_name = function_call["name"]
        
        if function_name == "create_support_ticket":
            ticket_id = function_result.get("ticket_id")
            return f"{answer}\n\n🎫 I've created a support ticket for you (ID: {ticket_id}). Our support team will review your issue and get back to you soon."
        
        elif function_name == "search_documentation":
            results = function_result.get("results", [])
            if results:
                sources_text = "\n".join([f"• {r['source']} (page {r['page']})" for r in results])
                return f"{function_result.get('answer', answer)}\n\n📚 Additional sources found:\n{sources_text}"
        
        elif function_name == "get_system_status":
            status = function_result.get("status", {})
            return f"🔍 System Status:\n• QA System: {status.get('qa_system', 'unknown')}\n• Documents: {status.get('documents_loaded', 0)} loaded\n• Active Tickets: {status.get('tickets_count', 0)}"
        
        elif function_name == "get_ticket_status":
            ticket = function_result.get("ticket", {})
            return f"🎫 Ticket {ticket.get('id', 'Unknown')}:\n• Status: {ticket.get('status', 'Unknown')}\n• Priority: {ticket.get('priority', 'Unknown')}\n• Created: {ticket.get('created_at', 'Unknown')}"
        
        elif function_name == "list_user_tickets":
            tickets = function_result.get("tickets", [])
            if tickets:
                ticket_list = "\n".join([f"• {t['id']}: {t['summary']} ({t['status']})" for t in tickets])
                return f"🎫 Your Support Tickets ({len(tickets)} total):\n{ticket_list}"
            else:
                return "You don't have any support tickets yet."
        
        elif function_name == "escalate_ticket":
            return f"{answer}\n\n⬆️ {function_result.get('message', 'Ticket escalated')}"
        
        return f"{answer}\n\n✅ {function_result.get('message', 'Function executed successfully')}"

class SupportBotApp:
    """Main Streamlit application for the Support Bot with function calling."""
    
    def __init__(self):
        # Check API key first
        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ OpenAI API key not found!")
            st.info("""
            To fix this issue:
            
            **Option 1: Environment Variable**
            ```bash
            export OPENAI_API_KEY=your_api_key_here
            ```
            
            **Option 2: .env File**
            Create a `.env` file in your project directory:
            ```
            OPENAI_API_KEY=your_api_key_here
            ```
            
            **Option 3: Streamlit Secrets**
            Create `.streamlit/secrets.toml`:
            ```toml
            OPENAI_API_KEY = "your_api_key_here"
            ```
            """)
            st.stop()
        
        self.config = Config()
        self.document_processor = DocumentProcessor(self.config.data_directory)
        self.ticket_system = TicketSystem()
        self.function_registry = FunctionRegistry(self)
        self.qa_system = None
        
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
        st.markdown("Ask questions about your product documentation or get help with support!")
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "history" not in st.session_state:
            st.session_state.history = []
        if "tickets" not in st.session_state:
            st.session_state.tickets = []
        if "function_calls_log" not in st.session_state:
            st.session_state.function_calls_log = []
    
    @st.cache_resource
    def load_qa_system(_self):
        """Load and cache the enhanced QA system."""
        return EnhancedQASystem(_self.config, _self.document_processor, _self.function_registry)
    
    def handle_user_input(self, user_input: str):
        """Process user input with function calling capabilities."""
        if not self.qa_system:
            self.qa_system = self.load_qa_system()
        
        # Use enhanced QA system with function calling
        result = self.qa_system.ask_question_with_functions(user_input)
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
    
    def display_chat_history(self):
        """Display the chat history with function call indicators."""
        for i, entry in enumerate(reversed(st.session_state.history)):
            question = entry["question"]
            answer = entry["answer"]
            sources = entry["sources"]
            function_called = entry.get("function_called")
            timestamp = entry.get("timestamp", datetime.now())
            
            # Display timestamp
            st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')}")
            
            st.markdown(f"**You:** {question}")
            
            # Show function call indicator
            if function_called:
                st.info(f"🔧 Function called: `{function_called}`")
            
            st.markdown(f"**Bot:** {answer}")
            
            # Display sources
            if sources:
                with st.expander("📄 Sources"):
                    for doc in sources:
                        source = doc.metadata.get('source', 'Unknown')
                        page = doc.metadata.get('page', '?')
                        st.markdown(f"• {source} (page {page})")
            
            st.divider()
    
    def display_sidebar(self):
        """Display sidebar with user info, tickets, and function logs."""
        with st.sidebar:
            st.header("User Information")
            st.session_state.user_name = st.text_input("Name", value="Alex Smith")
            st.session_state.user_email = st.text_input("Email", value="alex@example.com")
            
            st.header("Quick Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 System Status"):
                    result = self.function_registry.get_system_status()
                    if result["success"]:
                        status = result["status"]
                        st.success(f"QA System: {status['qa_system']}")
                        st.info(f"Documents: {status['documents_loaded']}")
                        st.info(f"Tickets: {status['tickets_count']}")
            
            with col2:
                if st.button("🎫 My Tickets"):
                    result = self.function_registry.list_user_tickets()
                    if result["success"]:
                        st.info(f"You have {result['count']} tickets")
            
            st.header("Support Tickets")
            if st.session_state.tickets:
                for ticket in st.session_state.tickets[-5:]:  # Show last 5 tickets
                    with st.expander(f"Ticket {ticket.id}"):
                        st.write(f"**Summary:** {ticket.summary}")
                        st.write(f"**Status:** {ticket.status}")
                        st.write(f"**Priority:** {getattr(ticket, 'priority', 'medium')}")
                        st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Escalation button
                        if st.button(f"Escalate", key=f"escalate_{ticket.id}"):
                            result = self.function_registry.escalate_ticket(
                                ticket.id, 
                                "User-requested escalation"
                            )
                            if result["success"]:
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
            else:
                st.write("No tickets created yet.")
            
            # Function calls log
            if st.session_state.function_calls_log:
                st.header("Function Calls Log")
                with st.expander(f"Recent Activity ({len(st.session_state.function_calls_log)})"):
                    for call in st.session_state.function_calls_log[-10:]:  # Show last 10
                        st.caption(f"{call['timestamp'].strftime('%H:%M:%S')} - {call['function']}")
    
    def display_function_help(self):
        """Display available functions and their descriptions."""
        with st.expander("🔧 Available Functions"):
            st.markdown("""
            The bot can perform the following actions:
            
            **Support Tickets:**
            - Create support tickets for complex issues
            - Check ticket status by ID
            - List your tickets
            - Escalate tickets
            
            **Documentation:**
            - Search through product documentation
            - Find specific information
            
            **System:**
            - Check system status and health
            
            **Examples of what you can ask:**
            - "Create a ticket for login issues"
            - "Search documentation for API setup"
            - "What's the system status?"
            - "Check ticket TICK-001"
            - "Show me my tickets"
            """)
    
    def run(self):
        """Run the Streamlit application."""
        try:
            # Display sidebar
            self.display_sidebar()
            
            # Main chat interface
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Display function help
                self.display_function_help()
                
                user_input = st.text_input(
                    "Ask a question or request an action:",
                    key="user_input",
                    placeholder="e.g., 'Create a ticket for login issues' or 'Search docs for API setup'"
                )
                
                if user_input:
                    with st.spinner("Processing..."):
                        answer, sources, function_called = self.handle_user_input(user_input)
                        
                        if function_called:
                            st.success(f"✅ Action completed: {function_called}")
                
                # Display chat history
                self.display_chat_history()
            
            with col2:
                st.subheader("System Status")
                if self.qa_system and hasattr(self.qa_system, 'chain') and self.qa_system.chain:
                    st.success("✅ QA System Ready")
                else:
                    st.error("❌ QA System Error")
                
                # Display document count
                docs = self.document_processor.load_documents()
                st.info(f"📚 {len(docs)} documents loaded")
                
                # Function registry status
                available_functions = len(self.function_registry.functions)
                st.info(f"🔧 {available_functions} functions available")
                
                # Recent function calls
                recent_calls = len(st.session_state.function_calls_log)
                st.info(f"📞 {recent_calls} function calls made")
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app = SupportBotApp()
    app.run()