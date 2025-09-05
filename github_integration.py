import os
from typing import Dict, Any, Optional
from github import Github
from datetime import datetime
import streamlit as st

class GitHubIssuesManager:
    """Manages GitHub Issues integration for support tickets"""
    
    def __init__(self):
        self.github_token = None
        self.repo_name = None
        self.github_client = None
        self.repo = None
        
    def configure(self, github_token: str, repo_name: str) -> bool:
        """Configure GitHub integration with token and repository"""
        try:
            self.github_token = github_token
            self.repo_name = repo_name
            self.github_client = Github(github_token)
            self.repo = self.github_client.get_repo(repo_name)
            
            # Test the connection
            _ = self.repo.name
            return True
        except Exception as e:
            print(f"Error configuring GitHub integration: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured"""
        return (self.github_client is not None and 
                self.repo is not None and 
                self.github_token is not None and 
                self.repo_name is not None)
    
    def create_support_ticket(self, user_name: str, user_email: str, 
                            summary: str, description: str, 
                            conversation_history: list = None) -> Dict[str, Any]:
        """Create a support ticket as a GitHub Issue"""
        if not self.is_configured():
            return {
                'success': False,
                'error': 'GitHub integration not configured',
                'issue_url': None,
                'issue_number': None
            }
        
        try:
            # Prepare issue body
            issue_body = self._format_issue_body(
                user_name, user_email, description, conversation_history
            )
            
            # Create labels for the issue
            labels = ['support-ticket', 'customer-support']
            
            # Create the issue
            issue = self.repo.create_issue(
                title=f"[Support] {summary}",
                body=issue_body,
                labels=labels
            )
            
            return {
                'success': True,
                'error': None,
                'issue_url': issue.html_url,
                'issue_number': issue.number,
                'issue_title': issue.title
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'issue_url': None,
                'issue_number': None
            }
    
    def _format_issue_body(self, user_name: str, user_email: str, 
                          description: str, conversation_history: list = None) -> str:
        """Format the issue body with user information and conversation history"""
        
        body_parts = []
        
        # User information section
        body_parts.append("## Customer Information")
        body_parts.append(f"**Name:** {user_name}")
        body_parts.append(f"**Email:** {user_email}")
        body_parts.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        body_parts.append("")
        
        # Issue description
        body_parts.append("## Issue Description")
        body_parts.append(description)
        body_parts.append("")
        
        # Conversation history if available
        if conversation_history and len(conversation_history) > 0:
            body_parts.append("## Conversation History")
            body_parts.append("Recent conversation with the support assistant:")
            body_parts.append("")
            
            for i, message in enumerate(conversation_history[-10:], 1):  # Last 10 messages
                role = "**Customer**" if message['role'] == 'user' else "**Assistant**"
                timestamp = message.get('timestamp', 'Unknown time')
                content = message['content']
                
                body_parts.append(f"### {i}. {role} ({timestamp})")
                body_parts.append(content)
                
                # Add sources if available
                if message.get('metadata') and message['metadata'].get('sources'):
                    body_parts.append("**Sources:**")
                    for source in message['metadata']['sources']:
                        body_parts.append(f"- {source}")
                
                body_parts.append("")
        
        # Footer
        body_parts.append("---")
        body_parts.append("*This ticket was automatically created by the Customer Support Assistant.*")
        
        return "\n".join(body_parts)
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the configured repository"""
        if not self.is_configured():
            return {'configured': False}
        
        try:
            return {
                'configured': True,
                'repo_name': self.repo.full_name,
                'repo_url': self.repo.html_url,
                'open_issues': self.repo.open_issues_count,
                'private': self.repo.private
            }
        except Exception as e:
            return {
                'configured': False,
                'error': str(e)
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the GitHub connection and permissions"""
        if not self.github_token or not self.repo_name:
            return {
                'success': False,
                'error': 'GitHub token or repository name not provided'
            }
        
        try:
            # Test GitHub client
            client = Github(self.github_token)
            user = client.get_user()
            
            # Test repository access
            repo = client.get_repo(self.repo_name)
            
            # Test permissions (try to get issues)
            issues = list(repo.get_issues(state='open'))
            
            return {
                'success': True,
                'user': user.login,
                'repo': repo.full_name,
                'permissions': 'Read/Write access confirmed',
                'open_issues': len(issues)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class SupportTicketManager:
    """Enhanced support ticket manager with GitHub integration"""
    
    def __init__(self):
        self.github_manager = GitHubIssuesManager()
        
        # Initialize session state for GitHub configuration
        if 'github_configured' not in st.session_state:
            st.session_state.github_configured = False
        if 'github_token' not in st.session_state:
            st.session_state.github_token = ""
        if 'github_repo' not in st.session_state:
            st.session_state.github_repo = ""
    
    def configure_github(self, token: str, repo: str) -> bool:
        """Configure GitHub integration"""
        success = self.github_manager.configure(token, repo)
        if success:
            st.session_state.github_configured = True
            st.session_state.github_token = token
            st.session_state.github_repo = repo
        return success
    
    def is_github_configured(self) -> bool:
        """Check if GitHub is configured"""
        return st.session_state.get('github_configured', False)
    
    def create_ticket(self, user_name: str, user_email: str, summary: str, 
                     description: str, conversation_history: list = None) -> Dict[str, Any]:
        """Create a support ticket"""
        if not self.is_github_configured():
            return {
                'success': False,
                'error': 'GitHub integration not configured. Please configure GitHub settings first.',
                'issue_url': None
            }
        
        # Ensure GitHub manager is configured with current session values
        if not self.github_manager.is_configured():
            self.github_manager.configure(
                st.session_state.github_token,
                st.session_state.github_repo
            )
        
        return self.github_manager.create_support_ticket(
            user_name, user_email, summary, description, conversation_history
        )
    
    def get_github_info(self) -> Dict[str, Any]:
        """Get GitHub repository information"""
        if not self.is_github_configured():
            return {'configured': False}
        
        if not self.github_manager.is_configured():
            self.github_manager.configure(
                st.session_state.github_token,
                st.session_state.github_repo
            )
        
        return self.github_manager.get_repository_info()
    
    def test_github_connection(self, token: str, repo: str) -> Dict[str, Any]:
        """Test GitHub connection"""
        temp_manager = GitHubIssuesManager()
        temp_manager.github_token = token
        temp_manager.repo_name = repo
        return temp_manager.test_connection()

