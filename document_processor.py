import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
import openai
from pypdf import PdfReader
import re
from datetime import datetime

class DocumentProcessor:
    """Handles document processing, indexing, and Q&A with citations"""
    
    def __init__(self, documents_dir: str = "documents"):
        self.documents_dir = Path(documents_dir)
        self.documents_dir.mkdir(exist_ok=True)
        self.index_file = self.documents_dir / "document_index.json"
        self.client = openai.OpenAI()
        self.document_index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load document index from file"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Save document index to file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for change detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _extract_text_from_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract text from PDF with page information"""
        pages = []
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    pages.append({
                        'page_number': page_num,
                        'text': text.strip(),
                        'word_count': len(text.split())
                    })
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
        return pages
    
    def _extract_text_from_txt(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into chunks of approximately 1000 words per "page"
            words = content.split()
            chunk_size = 1000
            pages = []
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)
                pages.append({
                    'page_number': (i // chunk_size) + 1,
                    'text': chunk_text,
                    'word_count': len(chunk_words)
                })
            
            return pages
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return []
    
    def _extract_text_from_md(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove markdown formatting for better text extraction
            # Remove headers
            content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
            # Remove bold/italic
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
            content = re.sub(r'\*(.*?)\*', r'\1', content)
            # Remove links
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            # Remove code blocks
            content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            content = re.sub(r'`([^`]+)`', r'\1', content)
            
            # Split into chunks
            words = content.split()
            chunk_size = 1000
            pages = []
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)
                pages.append({
                    'page_number': (i // chunk_size) + 1,
                    'text': chunk_text,
                    'word_count': len(chunk_words)
                })
            
            return pages
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return []
    
    def process_document(self, file_path: Path) -> bool:
        """Process a document and add it to the index"""
        try:
            file_hash = self._get_file_hash(file_path)
            file_name = file_path.name
            
            # Check if document already processed and unchanged
            if file_name in self.document_index:
                if self.document_index[file_name].get('hash') == file_hash:
                    return True  # Already processed and unchanged
            
            # Extract text based on file type
            file_extension = file_path.suffix.lower()
            pages = []
            
            if file_extension == '.pdf':
                pages = self._extract_text_from_pdf(file_path)
            elif file_extension == '.txt':
                pages = self._extract_text_from_txt(file_path)
            elif file_extension == '.md':
                pages = self._extract_text_from_md(file_path)
            else:
                print(f"Unsupported file type: {file_extension}")
                return False
            
            if not pages:
                print(f"No text extracted from {file_name}")
                return False
            
            # Store document information
            self.document_index[file_name] = {
                'hash': file_hash,
                'processed_date': datetime.now().isoformat(),
                'pages': pages,
                'total_pages': len(pages),
                'file_type': file_extension
            }
            
            self._save_index()
            print(f"Processed document: {file_name} ({len(pages)} pages)")
            return True
            
        except Exception as e:
            print(f"Error processing document {file_path}: {e}")
            return False
    
    def process_all_documents(self) -> int:
        """Process all documents in the documents directory"""
        processed_count = 0
        
        for file_path in self.documents_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.md']:
                if self.process_document(file_path):
                    processed_count += 1
        
        return processed_count
    
    def search_documents(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Search documents for relevant information"""
        if not self.document_index:
            return {
                'found': False,
                'answer': None,
                'sources': [],
                'message': 'No documents have been processed yet. Please upload some documents first.'
            }
        
        try:
            # Find relevant passages
            relevant_passages = []
            
            for doc_name, doc_info in self.document_index.items():
                for page in doc_info['pages']:
                    # Simple keyword matching (can be improved with embeddings)
                    page_text = page['text'].lower()
                    query_words = query.lower().split()
                    
                    # Calculate relevance score
                    score = 0
                    for word in query_words:
                        if len(word) > 2:  # Skip very short words
                            score += page_text.count(word)
                    
                    if score > 0:
                        relevant_passages.append({
                            'document': doc_name,
                            'page': page['page_number'],
                            'text': page['text'],
                            'score': score
                        })
            
            if not relevant_passages:
                return {
                    'found': False,
                    'answer': None,
                    'sources': [],
                    'message': 'No relevant information found in the uploaded documents.'
                }
            
            # Sort by relevance score
            relevant_passages.sort(key=lambda x: x['score'], reverse=True)
            top_passages = relevant_passages[:max_results]
            
            # Generate answer using OpenAI
            context = "\n\n".join([
                f"From {passage['document']} (Page {passage['page']}):\n{passage['text'][:500]}..."
                for passage in top_passages
            ])
            
            messages = [
                {
                    'role': 'system',
                    'content': '''You are a helpful customer support assistant. Use the provided document excerpts to answer the user's question. 
                    Be accurate and cite the sources. If the information is not sufficient, say so clearly.
                    Keep your answer concise but informative.'''
                },
                {
                    'role': 'user',
                    'content': f"Question: {query}\n\nRelevant document excerpts:\n{context}\n\nPlease provide a helpful answer based on this information."
                }
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            
            # Prepare sources
            sources = [
                f"{passage['document']} (Page {passage['page']})"
                for passage in top_passages
            ]
            
            return {
                'found': True,
                'answer': answer,
                'sources': sources,
                'passages_found': len(relevant_passages)
            }
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return {
                'found': False,
                'answer': None,
                'sources': [],
                'message': f'Error occurred while searching documents: {str(e)}'
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        if not self.document_index:
            return {
                'total_documents': 0,
                'total_pages': 0,
                'document_types': {}
            }
        
        total_pages = sum(doc['total_pages'] for doc in self.document_index.values())
        document_types = {}
        
        for doc_info in self.document_index.values():
            file_type = doc_info['file_type']
            document_types[file_type] = document_types.get(file_type, 0) + 1
        
        return {
            'total_documents': len(self.document_index),
            'total_pages': total_pages,
            'document_types': document_types,
            'documents': list(self.document_index.keys())
        }

