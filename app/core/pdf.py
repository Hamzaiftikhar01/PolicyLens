import re
import fitz  # PyMuPDF
from typing import List, Dict, Any
from pathlib import Path
import config

# Regular expressions for legal section matching
RE_ARTICLE = re.compile(r'^\s*(?:Article|ARTICLE)\s+(\d+[A-Z]?)\b\.?\s*(.*)', re.IGNORECASE)
RE_SECTION = re.compile(r'^\s*(?:Section|SECTION)\s+(\d+[A-Z]?)\b\.?\s*(.*)', re.IGNORECASE)
RE_GENERAL_HEADING = re.compile(r'^\s*(\d+)\.\s+([A-Z\s\-\,]{3,50})(?:\.-|\.)', re.ASCII)

def clean_text(text: str) -> str:
    """Basic text cleanup."""
    if not text:
        return ""
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing spaces
    return text.strip()

def split_text_sliding_window(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Helper to split text using a sliding window by characters."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        if start >= len(text) - overlap:
            break
            
    return chunks

def extract_pdf_chunks(
    pdf_path: Path, 
    document_id: str, 
    document_title: str, 
    doc_metadata: Dict[str, Any] = None,
    chunk_size: int = None,
    overlap: int = None
) -> List[Dict[str, Any]]:
    """
    Parses a PDF file page by page, identifies legal structural elements (Articles/Sections),
    and creates chunks with rich metadata.
    """
    if chunk_size is None:
        chunk_size = config.DEFAULT_CHUNK_SIZE
    if overlap is None:
        overlap = config.DEFAULT_CHUNK_OVERLAP
        
    doc_metadata = doc_metadata or {}
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF at {pdf_path}: {e}")
        
    chunks = []
    current_section = "General"
    current_section_text = []
    current_section_pages = []
    
    section_index = 0
    chunk_index = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")
        lines = page_text.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Check for section or article match
            art_match = RE_ARTICLE.match(line_clean)
            sec_match = RE_SECTION.match(line_clean)
            head_match = RE_GENERAL_HEADING.match(line_clean)
            
            new_section_found = False
            matched_section_name = ""
            
            if art_match:
                new_section_found = True
                matched_section_name = f"Article {art_match.group(1)}"
            elif sec_match:
                new_section_found = True
                matched_section_name = f"Section {sec_match.group(1)}"
            elif head_match:
                new_section_found = True
                matched_section_name = f"Section {head_match.group(1)}"
                
            if new_section_found:
                # Save previous section if not empty
                if current_section_text:
                    full_text = " ".join(current_section_text)
                    full_text = clean_text(full_text)
                    
                    if full_text:
                        sub_chunks = split_text_sliding_window(full_text, chunk_size, overlap)
                        for sc in sub_chunks:
                            chunks.append({
                                "chunk_id": f"{document_id}_ch_{chunk_index:04d}",
                                "document_id": document_id,
                                "document_title": document_title,
                                "text": sc,
                                "page": current_section_pages[0] if current_section_pages else page_num + 1,
                                "section": current_section,
                                "metadata": {
                                    **doc_metadata,
                                    "page_end": current_section_pages[-1] if current_section_pages else page_num + 1
                                }
                            })
                            chunk_index += 1
                            
                # Reset for new section
                current_section = matched_section_name
                current_section_text = [line_clean]
                current_section_pages = [page_num + 1]
                section_index += 1
            else:
                current_section_text.append(line_clean)
                if not current_section_pages or current_section_pages[-1] != page_num + 1:
                    current_section_pages.append(page_num + 1)
                    
    # Flush remaining text of final section
    if current_section_text:
        full_text = " ".join(current_section_text)
        full_text = clean_text(full_text)
        if full_text:
            sub_chunks = split_text_sliding_window(full_text, chunk_size, overlap)
            for sc in sub_chunks:
                chunks.append({
                    "chunk_id": f"{document_id}_ch_{chunk_index:04d}",
                    "document_id": document_id,
                    "document_title": document_title,
                    "text": sc,
                    "page": current_section_pages[0] if current_section_pages else len(doc),
                    "section": current_section,
                    "metadata": {
                        **doc_metadata,
                        "page_end": current_section_pages[-1] if current_section_pages else len(doc)
                    }
                })
                chunk_index += 1
                
    doc.close()
    
    # If no structural elements were found (e.g. non-legal standard document), chunks will all be in "General".
    # That is perfectly fine, we still have page-level and sliding window division.
    return chunks
