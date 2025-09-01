from typing import Optional
from typing import List
from datetime import datetime
import uuid
import logging
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

class Ticket:
    """Represents a support ticket."""
    
    def __init__(self, user_name: str, email: str, summary: str, description: str):
        self.id = str(uuid.uuid4())[:8]
        self.user_name = user_name
        self.email = email
        self.summary = summary
        self.description = description
        self.created_at = datetime.now()
        self.status = "Open"
    
    def to_dict(self) -> dict:
        """Convert ticket to dictionary format."""
        return {
            "id": self.id,
            "user_name": self.user_name,
            "email": self.email,
            "summary": self.summary,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }

class TicketSystem:
    """Handles creation and management of support tickets."""
    
    def __init__(self):
        self.tickets = []
    
    def create_ticket(self, user_name: str, email: str, summary: str, 
                     description: str) -> Ticket:
        """Create a new support ticket."""
        ticket = Ticket(user_name, email, summary, description)
        self.tickets.append(ticket)
        
        self._log_ticket_creation(ticket)
        self._send_to_external_system(ticket)
        
        return ticket
    
    def _log_ticket_creation(self, ticket: Ticket):
        """Log ticket creation details."""
        logger.info(f"Support ticket created: {ticket.id}")
        print("==== SUPPORT TICKET CREATED ====")
        print(f"Ticket ID: {ticket.id}")
        print(f"Name: {ticket.user_name}")
        print(f"Email: {ticket.email}")
        print(f"Summary: {ticket.summary}")
        print(f"Description: {ticket.description}")
        print(f"Created: {ticket.created_at}")
        print("=" * 35)
    
    def _send_to_external_system(self, ticket: Ticket):
        """Mock sending ticket to external system (e.g., Jira)."""
        # In a real implementation, this would integrate with Jira API
        logger.info(f"Ticket {ticket.id} would be sent to Jira (mocked)")
        print("Ticket would be sent to Jira (mocked).")
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a ticket by ID."""
        return next((t for t in self.tickets if t.id == ticket_id), None)
    
    def get_all_tickets(self) -> List[Ticket]:
        """Get all tickets."""
        return self.tickets.copy()
