# Deployment Guide

This guide provides instructions for deploying the Customer Support Application in various environments.

## Local Development

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Access at http://localhost:8501
```

### Environment Variables
```bash
# Optional: Set OpenAI API credentials
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_API_BASE="your-openai-api-base"
```

## Production Deployment

### Option 1: Streamlit Cloud

1. **Prepare Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select the main branch and `app.py`
   - Add secrets in the Streamlit Cloud dashboard:
     ```toml
     [secrets]
     OPENAI_API_KEY = "your-openai-api-key"
     OPENAI_API_BASE = "your-openai-api-base"
     ```

### Option 2: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   EXPOSE 8501

   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

   ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and Run**
   ```bash
   # Build image
   docker build -t customer-support-app .

   # Run container
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY="your-key" \
     -e OPENAI_API_BASE="your-base" \
     customer-support-app
   ```

### Option 3: Cloud Platforms

#### Heroku
1. **Create Procfile**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Deploy**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY="your-key"
   git push heroku main
   ```

#### AWS EC2
1. **Launch EC2 Instance**
   - Choose Ubuntu 22.04 LTS
   - Configure security group for port 8501

2. **Setup Application**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python and pip
   sudo apt install python3 python3-pip -y

   # Clone application
   git clone <your-repo>
   cd customer_support_app

   # Install dependencies
   pip3 install -r requirements.txt

   # Run with nohup for persistence
   nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &
   ```

#### Google Cloud Platform
1. **Create app.yaml**
   ```yaml
   runtime: python311

   env_variables:
     OPENAI_API_KEY: "your-key"
     OPENAI_API_BASE: "your-base"

   handlers:
   - url: /.*
     script: auto
   ```

2. **Deploy**
   ```bash
   gcloud app deploy
   ```

## Configuration for Production

### Security Considerations

1. **Environment Variables**
   - Never commit API keys to version control
   - Use platform-specific secret management
   - Rotate keys regularly

2. **File Upload Security**
   - Implement file size limits
   - Validate file types strictly
   - Scan for malicious content

3. **Access Control**
   - Consider adding authentication
   - Implement rate limiting
   - Monitor usage patterns

### Performance Optimization

1. **Document Processing**
   - Pre-process documents during deployment
   - Implement caching for search results
   - Use background processing for large files

2. **Memory Management**
   - Monitor memory usage with large documents
   - Implement document cleanup routines
   - Consider external storage for documents

3. **Scaling**
   - Use load balancers for multiple instances
   - Implement session persistence
   - Consider database for conversation history

### Monitoring and Logging

1. **Application Monitoring**
   ```python
   # Add to app.py for production logging
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s'
   )
   ```

2. **Health Checks**
   - Implement `/health` endpoint
   - Monitor document processing status
   - Check GitHub API connectivity

3. **Error Tracking**
   - Integrate with Sentry or similar
   - Log API failures and document errors
   - Monitor user interaction patterns

## Backup and Recovery

### Data Backup
1. **Document Index**
   - Backup `documents/document_index.json`
   - Store processed documents securely
   - Implement versioning for document changes

2. **Configuration**
   - Backup GitHub repository settings
   - Document API key rotation procedures
   - Maintain deployment configuration files

### Disaster Recovery
1. **Application Recovery**
   - Maintain deployment scripts
   - Document restoration procedures
   - Test recovery processes regularly

2. **Data Recovery**
   - Implement document re-processing
   - Maintain conversation history backups
   - Plan for GitHub API outages

## Maintenance

### Regular Tasks
1. **Updates**
   - Update Python dependencies monthly
   - Monitor security advisories
   - Test application after updates

2. **Cleanup**
   - Remove old conversation sessions
   - Archive processed documents
   - Clean up temporary files

3. **Monitoring**
   - Check application performance
   - Monitor API usage and costs
   - Review error logs regularly

### Troubleshooting Production Issues

1. **Application Won't Start**
   - Check Python version compatibility
   - Verify all dependencies installed
   - Review environment variable configuration

2. **Document Processing Fails**
   - Check file permissions
   - Verify disk space availability
   - Review document format compatibility

3. **GitHub Integration Issues**
   - Verify API token validity
   - Check repository permissions
   - Monitor API rate limits

4. **Performance Issues**
   - Monitor memory usage
   - Check document index size
   - Review search query complexity

## Cost Optimization

### OpenAI API Costs
- Monitor token usage
- Implement response caching
- Use appropriate model tiers

### Infrastructure Costs
- Right-size compute resources
- Implement auto-scaling
- Use spot instances where appropriate

### Storage Costs
- Compress document storage
- Implement data lifecycle policies
- Archive old conversations

## Support and Maintenance

For production deployments:
1. Establish monitoring and alerting
2. Create runbooks for common issues
3. Plan for regular maintenance windows
4. Document escalation procedures

