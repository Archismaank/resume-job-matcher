import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("uploads") # this is the folder where temp files are saved 

def get_upload_dir() -> Path:
    """
    Creates a uploads folder if it doesn't exists and returns it's path.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR

async def save_upload_file(file : UploadFile) -> Path:
    """
    Validates and saves an uploaded file to the uploads folder.
    Returns the path where the file was saved.
    """

    # check if file was provided actually or not
    if not file or not file.filename:
        raise HTTPException(
            status_code = 400,
            detail = "No file was uploaded."
        )
    
    original_name = file.filename
    extension = Path(original_name).suffix.lower()

    if extension not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code = 400,
            detail = f"Unsupported file type: {extension}. Only PDF and DOCX are supported."
        )
    
    # Genrating unique file name to avoid conflicts
    unique_filename = f"{uuid.uuid4()}{extension}"

    save_path = get_upload_dir() / unique_filename
    content = await file.read()
    save_path.write_bytes(content)

    return save_path

def delete_file(file_path : Path) -> None:
    """
    Deletes a file from disk after processing.
    We always delete uploaded resumes after analysis for privacy.
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass  # if deletion fails we will ignore it it will be removed eventually.