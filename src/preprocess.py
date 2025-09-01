import fitz
import os
import re
from typing import List
from src.utils import logger

def extract_text_from_pdf(pdf_path: str) -> str:
    logger.info(f"Extracting text from: {pdf_path}")
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""    
    return text

def clean_text(text: str) -> str:
    #normaliz text replacing mutliple whitepace with 1 space
    text = re.sub(r'\s+', ' ', text)
    """
    remove
    http:// https:// *DOI: whitespaces arXiv*
    """
    artifacts = [
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        r'\bDOI:\s*\S+',  # DOI references
        r'arXiv:\d+\.\d+v\d+\[[^\]]+\]',  # arXiv version strings
    ]
    
    for pattern in artifacts:
        text = re.sub(pattern, '', text)
    
    return text.strip()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            #keep context between chunks (minimal of 10 or smn)
            overlap_text = " ".join(current_chunk.split()[-10:])
            current_chunk = overlap_text + " " + sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def process_paper(pdf_path: str, output_dir: str) -> List[str]:
    """Process a single paper: extract, clean, and chunk text"""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []
    cleaned_text = clean_text(text)
    chunks = chunk_text(cleaned_text)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_files = []
    
    for i, chunk in enumerate(chunks):
        output_file = os.path.join(output_dir, f"{base_name}_chunk_{i}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        output_files.append(output_file)
    
    logger.info(f"Saved {len(output_files)} chunks for {base_name}")
    return output_files

def process_all_papers(pdf_dir: str, output_dir: str) -> List[str]:
    """    Process all PDFs in a directory    """
    os.makedirs(output_dir, exist_ok=True)
    all_chunk_files = []
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            chunk_files = process_paper(pdf_path, output_dir)
            all_chunk_files.extend(chunk_files)
    
    return all_chunk_files