from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import pdfplumber
from bs4 import BeautifulSoup
import re

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def beautify_text(text: str) -> str:
    """
    Beautify extracted text by:
    - Removing excessive whitespace
    - Adding proper line breaks
    - Formatting paragraphs
    - Cleaning up special characters
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    
    # Remove multiple consecutive spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove multiple consecutive newlines (keep max 2 for paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up lines - remove trailing spaces
    lines = text.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    text = '\n'.join(cleaned_lines)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file (PDF, Word, HTML, Text) and extract text with beautification.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        text_content = ""
        
        # Get file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        if file_ext == "pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"
        elif file_ext in ["docx", "doc"]:
            try:
                from docx import Document
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
            except ImportError:
                # Fallback if python-docx is not installed
                text_content = f"[Word document support requires python-docx library. File: {file.filename}]"
        elif file_ext == "html" or file_ext == "htm":
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                text_content = soup.get_text()
        elif file_ext in ["txt", "text"]:
            # Try different encodings for text files
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        text_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            if not text_content:
                raise HTTPException(status_code=400, detail="Could not decode text file")
        else:
            # Fallback: try to read as text
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Beautify the extracted text
        beautified_content = beautify_text(text_content)
        
        return {
            "filename": file.filename,
            "content": beautified_content,
            "content_preview": beautified_content[:500],  # Return first 500 chars as preview
            "full_content_length": len(beautified_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
