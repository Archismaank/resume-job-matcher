import fitz
from pathlib import Path

def extract_text_from_pdf(file_path: str) -> str:
    """
    Reads a PDF file and extracts all the text from it.
    Returns one big string with all the text.
    """
    path = Path(file_path) # convert the file path string to a path object.

    if not path.exists(): #checking if file exists or not
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    if path.suffix.lower() != ".pdf": # checking the file is pdf or not
        raise ValueError(f"file is not a PDF: {file_path}")
    
    doc = fitz.open(file_path) # opening the file 

    full_text = ""

    for page_no in range(doc.page_count):
        page = doc[page_no]  
        text = page.get_text()
        full_text += text + "\n"

    doc.close()

    full_text = full_text.strip()
    return full_text

def extract_text_from_docx(file_path: str) -> str:
    """
    Reads a DOCX file and extracts all the text from it.
    Returns one big string with all the text.
    """
    from docx import Document
    from pathlib import Path

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    
    if path.suffix.lower() != ".docx":
        raise ValueError(f"file is not a DOCX: {file_path}")
    
    doc = Document(file_path)
    full_text = ""

    for paragraph in doc.paragraphs: # A DOCX file is made of paragraphs so loop through each one
        if paragraph.text.strip():
            full_text += paragraph.text + "\n"

    full_text = full_text.strip()
    return full_text

def extract_text(file_path: str) -> str:
    """
    smart function that automatically detects if the file is a PDF or DOCX
    and calls the right parser.
    This is the main function we'll use everywhere in the project.
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {extension}. Only PDF and DOCX are supported.")
 
