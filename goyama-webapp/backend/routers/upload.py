import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from loguru import logger

from mfrecon.parsers import default_registry
from backend.services.file_manager import file_manager
from backend.models.response_models import UploadResponse, MultiUploadResponse

router = APIRouter(prefix="/api/upload", tags=["Uploads"])

@router.post("/crm", response_model=UploadResponse)
async def upload_crm(file: UploadFile = File(...)):
    """Uploads the CRM Master Excel/CSV file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_id = str(uuid.uuid4())
    content = await file.read()
    
    file_path = file_manager.save_file(file_id, file.filename, content)
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        source_type="CRM"
    )

@router.post("/reports", response_model=MultiUploadResponse)
async def upload_reports(files: List[UploadFile] = File(...)):
    """Uploads 1 to N report files (CAMS, KFintech, BSE, NSE, CAS PDF)."""
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
            
        file_id = str(uuid.uuid4())
        content = await file.read()
        
        file_path = file_manager.save_file(file_id, file.filename, content)
        
        # Auto-detect source type using engine registry
        source_type = "UNKNOWN"
        try:
            parser = default_registry.detect_parser(file_path)
            source_type = parser.source.value
            logger.info(f"Auto-detected report source: {source_type} for file: {file.filename}")
        except Exception as e:
            logger.warning(f"Could not auto-detect parser for file {file.filename}: {e}")
            # If it's a PDF, fallback to PDF_CAS since it's the only PDF source
            if file.filename.lower().endswith(".pdf"):
                source_type = "PDF_CAS"
        
        uploaded_files.append(
            UploadResponse(
                file_id=file_id,
                filename=file.filename,
                source_type=source_type
            )
        )
        
    return MultiUploadResponse(uploaded_files=uploaded_files)

@router.post("/config", response_model=UploadResponse)
async def upload_config(file: UploadFile = File(...)):
    """Uploads an optional config YAML file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_id = str(uuid.uuid4())
    content = await file.read()
    
    file_manager.save_file(file_id, file.filename, content)
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        source_type="CONFIG"
    )
