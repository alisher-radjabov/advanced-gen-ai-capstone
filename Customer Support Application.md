# Customer Support Application

A comprehensive customer support application built with Streamlit that provides web chat functionality, document-based Q&A with citations, conversation history, and GitHub Issues integration for support ticket creation.

## Features

### 🎧 Core Functionality
- **Web Chat Interface**: Interactive chat interface for customer support
- **Conversation History**: Maintains chat context and conversation flow
- **Document-Based Q&A**: Search and answer questions from uploaded documents
- **Source Citations**: Provides file names and page references for answers
- **Support Ticket Creation**: Create GitHub Issues for unresolved queries

### 📄 Document Processing
- **Multi-format Support**: PDF, TXT, and Markdown files
- **Automatic Processing**: Extract text and create searchable index
- **Page-level Citations**: Track source documents and page numbers
- **Real-time Updates**: Process new documents on upload

### 🔧 GitHub Integration
- **Issues Creation**: Automatically create GitHub Issues as support tickets
- **Conversation Context**: Include chat history in tickets
- **User Information**: Capture customer details (name, email)
- **Repository Management**: Configure target repository for tickets

### ⚙️ Configuration
- **GitHub Settings**: Configure Personal Access Token and repository
- **Document Management**: Upload and process support documents
- **Connection Testing**: Verify GitHub API connectivity

## Installation

### Prerequisites
- Python 3.11+
- GitHub Personal Access Token (with repo permissions)
- OpenAI API Key (optional, for AI responses)

### Setup

1. **Clone or download the application files**
   ```bash
   git clone <repository-url>
   cd customer_support_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (optional)**
   ```bash
   export OPENAI_API_KEY="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"
   export OPENAI_API_BASE="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"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## Configuration

### GitHub Integration

1. **Create a GitHub Personal Access Token**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with `repo` permissions
   - Copy the token for configuration

2. **Configure in the Application**
   - Open the GitHub Settings section in the sidebar
   - Enter your Personal Access Token
   - Enter the repository in format: `owner/repository-name`
   - Click "Test Connection" to verify
   - Click "Save Configuration" to apply settings

### Document Upload

1. **Supported Formats**
   - PDF files (.pdf)
   - Text files (.txt)
   - Markdown files (.md)

2. **Upload Process**
   - Use the file uploader in the Documents section
   - Files are automatically processed and indexed
   - View document statistics and details
   - Use "Reprocess All Documents" to refresh the index

## Usage

### Chat Interface

1. **Ask Questions**
   - Type your question in the chat input
   - The system searches uploaded documents first
   - If found, provides answer with source citations
   - If not found, suggests creating a support ticket

2. **View Sources**
   - Click on "Sources" expander to see document references
   - Sources include file name and page number
   - Example: "toyota-hilux-manual.md (Page 2)"

### Support Ticket Creation

1. **Fill Ticket Details**
   - Enter your name and email
   - Provide issue summary and detailed description
   - Choose whether to include conversation history

2. **Create Ticket**
   - Click "Create Ticket" button
   - System creates GitHub Issue with all details
   - Receive ticket number and direct link

### Conversation Management

- **View History**: All messages are displayed in the chat interface
- **Clear History**: Use "Clear Chat History" button to reset
- **Message Count**: View total messages in the sidebar

## File Structure

```
customer_support_app/
├── app.py                    # Main Streamlit application
├── document_processor.py     # Document processing and search
├── github_integration.py     # GitHub Issues integration
├── requirements.txt          # Python dependencies
├── documents/               # Document storage directory
│   ├── document_index.json # Document search index
│   └── *.pdf, *.txt, *.md  # Uploaded documents
└── README.md               # This documentation
```

## API Integration

### OpenAI API (Optional)
- Used for generating AI responses when documents don't contain answers
- Requires `OPENAI_API_KEY` environment variable
- Falls back to document search if API is unavailable

### GitHub API
- Used for creating support tickets as GitHub Issues
- Requires Personal Access Token with repo permissions
- Supports private and public repositories

## Troubleshooting

### Common Issues

1. **GitHub Connection Failed**
   - Verify Personal Access Token is correct
   - Check repository name format (owner/repo)
   - Ensure token has repo permissions
   - Verify repository exists and is accessible

2. **Document Processing Failed**
   - Check file format is supported (PDF, TXT, MD)
   - Ensure file is not corrupted
   - Try reprocessing with "Reprocess All Documents"

3. **OpenAI API Errors**
   - Verify API key is set correctly
   - Check API quota and billing
   - System will fall back to document search only

4. **No Search Results**
   - Ensure documents are uploaded and processed
   - Check document content matches query keywords
   - Try different search terms or phrases

### Performance Tips

1. **Document Optimization**
   - Keep documents focused and well-structured
   - Use clear headings and sections
   - Limit file sizes for faster processing

2. **Search Effectiveness**
   - Use specific keywords in queries
   - Include relevant terms from documents
   - Try variations of technical terms

## Development

### Architecture

- **Frontend**: Streamlit web interface
- **Document Processing**: PyPDF for PDF parsing, text extraction
- **Search**: Keyword-based matching with relevance scoring
- **GitHub Integration**: PyGithub library for API calls
- **Session Management**: Streamlit session state for conversation history

### Extending the Application

1. **Enhanced Search**
   - Implement vector embeddings for semantic search
   - Add fuzzy matching for better keyword matching
   - Include machine learning-based relevance scoring

2. **Additional Integrations**
   - Add Slack/Teams notifications
   - Integrate with CRM systems
   - Support for more document formats

3. **UI Improvements**
   - Add dark mode support
   - Implement responsive design
   - Add file preview capabilities

## Security Considerations

- **API Keys**: Store securely as environment variables
- **File Uploads**: Validate file types and sizes
- **GitHub Access**: Use minimal required permissions
- **Data Privacy**: Consider document content sensitivity

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review GitHub Issues in the repository
3. Create a support ticket using the application itself

