"""
Document Ingestion Module

Handles loading of txt, pdf, and docx files into normalized text.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
import pdfplumber
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIngester:
    def __init__(self):
        self.supported_formats = {'.txt', '.pdf', '.docx'}

    def load_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {self.supported_formats}")
        document_id = os.path.splitext(os.path.basename(file_path))[0]
        if file_ext == '.txt':
            content = self._load_txt(file_path)
        elif file_ext == '.pdf':
            content = self._load_pdf(file_path)
        else:
            content = self._load_docx(file_path)
        return {'content': content, 'document_id': document_id, 'file_path': file_path, 'file_type': file_ext, 'metadata': self._process_metadata(metadata, file_path)}

    def _process_metadata(self, metadata, file_path):
        metadata = metadata or {}
        return {'author': metadata.get('author', 'unknown'), 'date': metadata.get('date', datetime.now().isoformat()), 'category': metadata.get('category', 'general'), 'version': metadata.get('version', '1.0'), 'source_file': file_path}

    def _load_txt(self, file_path):
        try:
            return open(file_path, 'r', encoding='utf-8').read()
        except UnicodeDecodeError:
            return open(file_path, 'r', encoding='latin-1').read()

    def _load_pdf(self, file_path):
        parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                parts = [page.extract_text() for page in pdf.pages if page.extract_text()]
        except Exception:
            reader = PdfReader(file_path)
            parts = [page.extract_text() for page in reader.pages if page.extract_text()]
        return '\n\n'.join(parts)

    def _load_docx(self, file_path):
        document = DocxDocument(file_path)
        return '\n\n'.join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
