---
title: GenAI Bot
emoji: 🚀
colorFrom: indigo
colorTo: pink
sdk: streamlit
sdk_version: 1.47.1
app_file: app.py
pinned: false
---

# Product Documentation Support Bot 🤖

A Streamlit-based chatbot that uses LangChain and OpenAI to answer questions about your product documentation.
...


# Product Documentation Support Bot 🤖

A Streamlit-based chatbot that uses LangChain and OpenAI to answer questions about your product documentation.

## Features

- PDF-based document Q&A with citations (file name and page)
- Chat history support
- Streamlit UI
- Support ticket creation mock (Jira integration)
- Uses LangChain + OpenAI under the hood

## Getting Started

1. Clone the repo and install requirements:

```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key in a `.env` file:

```env
OPENAI_API_KEY=your_openai_key_here
```

3. Put your PDF docs in the `data/` folder.

4. Run the app:

```bash
streamlit run app.py
```
