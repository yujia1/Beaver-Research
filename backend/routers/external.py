from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import pdfplumber
from bs4 import BeautifulSoup

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file (PDF, HTML) and extract text.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        text_content = ""
        
        if file.filename.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"
        elif file.filename.endswith(".html"):
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                text_content = soup.get_text()
        else:
            # Fallback for text files
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
                
        return {
            "filename": file.filename,
            "content_preview": text_content[:500], # Return first 500 chars as preview
            "full_content_length": len(text_content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
