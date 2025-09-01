import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GitHubIssuesIntegration:
    """Integration with GitHub Issues for support ticket management."""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str = None):
        """
        Initialize GitHub Issues integration.
        
        Args:
            repo_owner: GitHub username or organization name
            repo_name: Repository name
            github_token: GitHub personal access token
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def create_issue(self, title: str, body: str, labels: List[str] = None, 
                    assignees: List[str] = None, milestone: int = None) -> Dict:
        """
        Create a new GitHub issue.
        
        Args:
            title: Issue title
            body: Issue description
            labels: List of label names
            assignees: List of GitHub usernames to assign
            milestone: Milestone number
            
        Returns:
            Dict with issue creation result
        """
        try:
            issue_data = {
                "title": title,
                "body": body
            }
            
            if labels:
                issue_data["labels"] = labels
            if assignees:
                issue_data["assignees"] = assignees
            if milestone:
                issue_data["milestone"] = milestone
            
            response = requests.post(
                f"{self.base_url}/issues",
                headers=self.headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issue = response.json()
                return {
                    "success": True,
                    "issue_number": issue["number"],
                    "issue_url": issue["html_url"],
                    "issue_id": issue["id"],
                    "message": f"GitHub issue #{issue['number']} created successfully"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "message": f"Failed to create GitHub issue: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while creating GitHub issue"
            }
    
    def update_issue(self, issue_number: int, title: str = None, body: str = None, 
                    state: str = None, labels: List[str] = None) -> Dict:
        """
        Update an existing GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            title: New title (optional)
            body: New body (optional)
            state: New state - "open" or "closed" (optional)
            labels: New labels list (optional)
            
        Returns:
            Dict with update result
        """
        try:
            update_data = {}
            if title:
                update_data["title"] = title
            if body:
                update_data["body"] = body
            if state:
                update_data["state"] = state
            if labels:
                update_data["labels"] = labels
            
            response = requests.patch(
                f"{self.base_url}/issues/{issue_number}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                issue = response.json()
                return {
                    "success": True,
                    "issue_number": issue["number"],
                    "issue_url": issue["html_url"],
                    "message": f"GitHub issue #{issue['number']} updated successfully"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "message": f"Failed to update GitHub issue: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error updating GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while updating GitHub issue"
            }
    
    def add_comment(self, issue_number: int, comment: str) -> Dict:
        """
        Add a comment to a GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            comment: Comment text
            
        Returns:
            Dict with comment creation result
        """
        try:
            comment_data = {"body": comment}
            
            response = requests.post(
                f"{self.base_url}/issues/{issue_number}/comments",
                headers=self.headers,
                json=comment_data
            )
            
            if response.status_code == 201:
                comment_obj = response.json()
                return {
                    "success": True,
                    "comment_id": comment_obj["id"],
                    "comment_url": comment_obj["html_url"],
                    "message": f"Comment added to issue #{issue_number}"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "message": f"Failed to add comment: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error adding comment to GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while adding comment"
            }
    
    def get_issue(self, issue_number: int) -> Dict:
        """
        Get details of a specific GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            
        Returns:
            Dict with issue details
        """
        try:
            response = requests.get(
                f"{self.base_url}/issues/{issue_number}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                issue = response.json()
                return {
                    "success": True,
                    "issue": {
                        "number": issue["number"],
                        "title": issue["title"],
                        "body": issue["body"],
                        "state": issue["state"],
                        "labels": [label["name"] for label in issue["labels"]],
                        "assignees": [assignee["login"] for assignee in issue["assignees"]],
                        "created_at": issue["created_at"],
                        "updated_at": issue["updated_at"],
                        "html_url": issue["html_url"]
                    },
                    "message": f"Retrieved issue #{issue_number}"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "message": f"Failed to get issue: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"Error getting GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while getting issue"
            }

class EnhancedTicketSystem:
    """Enhanced ticket system with GitHub Issues integration."""
    
    def __init__(self, ticket_system, github_integration: GitHubIssuesIntegration = None):
        self.ticket_system = ticket_system
        self.github_integration = github_integration
    
    def create_ticket_with_github(self, user_name: str, email: str, summary: str, 
                                 description: str, priority: str = "medium") -> Dict:
        """
        Create a support ticket and corresponding GitHub issue.
        
        Args:
            user_name: Name of the user
            email: User's email
            summary: Brief summary of the issue
            description: Detailed description
            priority: Priority level
            
        Returns:
            Dict with creation results
        """
        try:
            # Create local ticket first
            ticket = self.ticket_system.create_ticket(
                user_name=user_name,
                email=email,
                summary=summary,
                description=description
            )
            
            result = {
                "success": True,
                "ticket": ticket,
                "ticket_id": ticket.id,
                "message": f"Support ticket {ticket.id} created"
            }
            
            # Create GitHub issue if integration is available
            if self.github_integration:
                github_result = self._create_github_issue_from_ticket(ticket, priority)
                result.update(github_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating ticket with GitHub: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support ticket"
            }
    
    def _create_github_issue_from_ticket(self, ticket, priority: str) -> Dict:
        """Create a GitHub issue from a support ticket."""
        try:
            # Format the issue title
            title = f"[Support] {ticket.summary}"
            
            # Format the issue body with ticket details
            body = f"""## Support Ticket Details
            
**Ticket ID:** {ticket.id}
**User:** {ticket.user_name} ({ticket.email})
**Priority:** {priority}
**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Description
{ticket.description}

---
*This issue was automatically created from support ticket {ticket.id}*
"""
            
            # Determine labels based on priority and type
            labels = ["support-ticket", f"priority-{priority}"]
            
            # Create the GitHub issue
            github_result = self.github_integration.create_issue(
                title=title,
                body=body,
                labels=labels
            )
            
            if github_result["success"]:
                # Store GitHub issue number with the ticket
                ticket.github_issue_number = github_result["issue_number"]
                ticket.github_issue_url = github_result["issue_url"]
                
                return {
                    "github_success": True,
                    "github_issue_number": github_result["issue_number"],
                    "github_issue_url": github_result["issue_url"],
                    "github_message": github_result["message"]
                }
            else:
                return {
                    "github_success": False,
                    "github_error": github_result["error"],
                    "github_message": github_result["message"]
                }
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue from ticket: {e}")
            return {
                "github_success": False,
                "github_error": str(e),
                "github_message": "Failed to create GitHub issue"
            }
    
    def sync_ticket_with_github(self, ticket, comment: str = None) -> Dict:
        """Sync ticket updates with GitHub issue."""
        if not self.github_integration or not hasattr(ticket, 'github_issue_number'):
            return {"success": False, "message": "No GitHub integration or issue number"}
        
        try:
            if comment:
                # Add comment to GitHub issue
                result = self.github_integration.add_comment(
                    ticket.github_issue_number,
                    f"**Ticket Update ({datetime.now().strftime('%Y-%m-%d %H:%M')})**\n\n{comment}"
                )
                return result
            
            return {"success": True, "message": "Ticket synced with GitHub"}
            
        except Exception as e:
            logger.error(f"Error syncing ticket with GitHub: {e}")
            return {"success": False, "error": str(e)}

# Updated function for the main app
def create_github_integration() -> Optional[GitHubIssuesIntegration]:
    """Create GitHub integration if credentials are available."""
    try:
        repo_owner = os.getenv("GITHUB_REPO_OWNER")
        repo_name = os.getenv("GITHUB_REPO_NAME") 
        github_token = os.getenv("GITHUB_TOKEN")
        
        if repo_owner and repo_name and github_token:
            return GitHubIssuesIntegration(repo_owner, repo_name, github_token)
        else:
            logger.warning("GitHub integration disabled: missing credentials")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create GitHub integration: {e}")
        return None

# Enhanced function registry with GitHub integration
class EnhancedFunctionRegistry:
    """Enhanced function registry with GitHub Issues support."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.github_integration = create_github_integration()
        self.enhanced_ticket_system = EnhancedTicketSystem(
            app_instance.ticket_system, 
            self.github_integration
        )
        
        self.functions = {
            "create_support_ticket": self.create_support_ticket,
            "create_github_issue": self.create_github_issue,
            "update_github_issue": self.update_github_issue,
            "search_documentation": self.search_documentation,
            "get_system_status": self.get_system_status,
            "get_ticket_status": self.get_ticket_status,
            "list_user_tickets": self.list_user_tickets,
            "escalate_ticket": self.escalate_ticket,
            "sync_ticket_to_github": self.sync_ticket_to_github
        }
    
    def get_function_definitions(self) -> List[Dict]:
        """Return function definitions including GitHub functions."""
        base_functions = [
            {
                "name": "create_support_ticket",
                "description": "Create a new support ticket (automatically creates GitHub issue if configured)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Brief summary of the issue"},
                        "description": {"type": "string", "description": "Detailed description"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Priority level",
                            "default": "medium"
                        }
                    },
                    "required": ["summary", "description"]
                }
            },
            {
                "name": "create_github_issue",
                "description": "Create a GitHub issue directly",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "description": "Issue description"},
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Issue labels"
                        },
                        "assignees": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "GitHub usernames to assign"
                        }
                    },
                    "required": ["title", "body"]
                }
            },
            {
                "name": "update_github_issue",
                "description": "Update an existing GitHub issue",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_number": {"type": "integer", "description": "GitHub issue number"},
                        "title": {"type": "string", "description": "New title"},
                        "body": {"type": "string", "description": "New body"},
                        "state": {
                            "type": "string",
                            "enum": ["open", "closed"],
                            "description": "Issue state"
                        },
                        "comment": {"type": "string", "description": "Add a comment"}
                    },
                    "required": ["issue_number"]
                }
            },
            {
                "name": "sync_ticket_to_github",
                "description": "Sync a support ticket with its GitHub issue",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string", "description": "Support ticket ID"},
                        "comment": {"type": "string", "description": "Additional comment to add"}
                    },
                    "required": ["ticket_id"]
                }
            }
        ]
        
        # Add other functions from the original registry
        # (search_documentation, get_system_status, etc.)
        
        return base_functions
    
    def create_support_ticket(self, summary: str, description: str, priority: str = "medium") -> Dict:
        """Create support ticket with automatic GitHub issue creation."""
        try:
            user_name = st.session_state.get("user_name", "Anonymous User")
            email = st.session_state.get("user_email", "user@example.com")
            
            # Use enhanced ticket system that creates GitHub issues
            result = self.enhanced_ticket_system.create_ticket_with_github(
                user_name=user_name,
                email=email,
                summary=summary,
                description=description,
                priority=priority
            )
            
            if result["success"]:
                # Add to session state
                st.session_state.tickets.append(result["ticket"])
                
                # Prepare response message
                message = f"Support ticket {result['ticket_id']} created successfully"
                
                if result.get("github_success"):
                    message += f"\n🔗 GitHub issue created: #{result['github_issue_number']}"
                    message += f"\n📋 View at: {result['github_issue_url']}"
                elif self.github_integration:
                    message += f"\n⚠️ GitHub issue creation failed: {result.get('github_message', 'Unknown error')}"
                
                return {
                    "success": True,
                    "ticket_id": result["ticket_id"],
                    "message": message,
                    "github_issue_number": result.get("github_issue_number"),
                    "github_issue_url": result.get("github_issue_url")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create support ticket"
            }
    
    def create_github_issue(self, title: str, body: str, labels: List[str] = None, 
                           assignees: List[str] = None) -> Dict:
        """Create a GitHub issue directly."""
        if not self.github_integration:
            return {
                "success": False,
                "message": "GitHub integration not configured"
            }
        
        return self.github_integration.create_issue(
            title=title,
            body=body,
            labels=labels or ["support"],
            assignees=assignees
        )
    
    def update_github_issue(self, issue_number: int, title: str = None, body: str = None,
                           state: str = None, comment: str = None) -> Dict:
        """Update a GitHub issue."""
        if not self.github_integration:
            return {
                "success": False,
                "message": "GitHub integration not configured"
            }
        
        try:
            # Add comment if provided
            if comment:
                comment_result = self.github_integration.add_comment(issue_number, comment)
                if not comment_result["success"]:
                    return comment_result
            
            # Update issue if other parameters provided
            if title or body or state:
                return self.github_integration.update_issue(
                    issue_number=issue_number,
                    title=title,
                    body=body,
                    state=state
                )
            
            return {
                "success": True,
                "message": f"GitHub issue #{issue_number} updated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update GitHub issue"
            }
    
    def sync_ticket_to_github(self, ticket_id: str, comment: str = None) -> Dict:
        """Sync a support ticket with its GitHub issue."""
        try:
            # Find the ticket
            tickets = st.session_state.get("tickets", [])
            ticket = next((t for t in tickets if t.id == ticket_id), None)
            
            if not ticket:
                return {
                    "success": False,
                    "message": f"Ticket {ticket_id} not found"
                }
            
            return self.enhanced_ticket_system.sync_ticket_with_github(ticket, comment)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync ticket with GitHub"
            }
    
    # Include other methods from original FunctionRegistry
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
        """Get current system status including GitHub integration."""
        try:
            docs = self.app.document_processor.load_documents()
            qa_ready = self.app.qa_system is not None and hasattr(self.app.qa_system, 'chain') and self.app.qa_system.chain is not None
            github_configured = self.github_integration is not None
            
            return {
                "success": True,
                "status": {
                    "qa_system": "online" if qa_ready else "offline",
                    "documents_loaded": len(docs),
                    "tickets_count": len(st.session_state.get("tickets", [])),
                    "github_integration": "enabled" if github_configured else "disabled",
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
        """Get status of a specific ticket including GitHub info."""
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
                "priority": getattr(ticket, 'priority', 'medium'),
                "created_at": ticket.created_at.isoformat(),
                "user_name": ticket.user_name
            }
            
            # Add GitHub info if available
            if hasattr(ticket, 'github_issue_number'):
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
                ticket_data = {
                    "id": ticket.id,
                    "summary": ticket.summary,
                    "status": ticket.status,
                    "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                    "priority": getattr(ticket, 'priority', 'medium')
                }
                
                # Add GitHub info if available
                if hasattr(ticket, 'github_issue_number'):
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
            logger.error(f"Error listing user tickets: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list user tickets"
            }
    
    def escalate_ticket(self, ticket_id: str, reason: str) -> Dict:
        """Escalate a ticket and update GitHub issue."""
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
            
            # Sync with GitHub if available
            github_result = None
            if self.github_integration and hasattr(ticket, 'github_issue_number'):
                escalation_comment = f"""
**🚨 TICKET ESCALATED**

**Previous Priority:** {old_priority}
**New Priority:** {ticket.priority}
**Reason:** {reason}
**Escalated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This ticket requires immediate attention from the support team.
"""
                github_result = self.enhanced_ticket_system.sync_ticket_with_github(
                    ticket, escalation_comment
                )
            
            message = f"Ticket {ticket_id} escalated from {old_priority} to {ticket.priority}"
            if github_result and github_result.get("success"):
                message += "\n🔗 GitHub issue updated with escalation notice"
            
            return {
                "success": True,
                "message": message,
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