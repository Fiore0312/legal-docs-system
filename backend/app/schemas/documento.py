from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.documento import DocumentType, DocumentStatus

class DocumentoBase(BaseModel):
    filename: str = Field(..., description="Nome del file")
    tipo_documento: DocumentType = Field(..., description="Tipo di documento")

class DocumentoCreate(DocumentoBase):
    pass

class DocumentoUpdate(BaseModel):
    tipo_documento: Optional[DocumentType] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentoSearch(BaseModel):
    query: str = Field(..., min_length=3, description="Testo da cercare")
    tipo_documento: Optional[DocumentType] = None
    data_inizio: Optional[datetime] = None
    data_fine: Optional[datetime] = None
    limit: int = Field(default=10, ge=1, le=100)
    include_content: bool = Field(default=False, description="Includere il contenuto nei risultati")

class DocumentoResponse(DocumentoBase):
    id: int
    stato_elaborazione: DocumentStatus
    metadata: Optional[Dict[str, Any]]
    mime_type: Optional[str]
    dimensione: Optional[int]
    data_caricamento: datetime
    data_elaborazione: Optional[datetime]
    data_modifica: datetime
    errore: Optional[str]

    class Config:
        from_attributes = True

class DocumentoDetail(DocumentoResponse):
    contenuto: Optional[str]
    percorso_file: str
    hash_file: Optional[str]

class DocumentoSearchResult(BaseModel):
    documento: DocumentoResponse
    score: float = Field(..., description="Score di rilevanza")
    highlights: List[str] = Field(default_list=[], description="Frammenti di testo rilevanti")

class DocumentoSearchResponse(BaseModel):
    results: List[DocumentoSearchResult]
    total: int
    page: int
    page_size: int
    
class DocumentoExportFormat(str):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"

class DocumentoExportRequest(BaseModel):
    format: DocumentoExportFormat = Field(default=DocumentoExportFormat.PDF)
    include_metadata: bool = Field(default=True)
    include_content: bool = Field(default=True) 