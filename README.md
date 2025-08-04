# Documentation Support Bot 🤖

A Streamlit-based chatbot that uses LangChain and OpenAI to answer questions about your product documentation.
...


# Documentation Support Bot 🤖

A Streamlit-based chatbot that uses LangChain and OpenAI to answer questions about your product documentation.

## Features

- PDF-based document Q&A with citations (file name and page)
- Chat history support
- Streamlit UI
- Uses OpenAI + LangChain under the hood

## Getting Started

1. Clone the repo and install requirements:

```bash
pip install -r requirements.txt
```

2. Set OpenAI API key in a `.env` file:

```env
OPENAI_API_KEY=your_openai_key_here
```

3. Place PDF docs in the `data/` folder.

4. Run the app:

```bash
streamlit run app.py
```

## Folder Structure

- `data/`: place your PDF documentation here
- `/`: main code files
- `requirements.txt`: dependencies
- `README.md`: this file