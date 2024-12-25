from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.database import get_db
from ...models.documento import Documento, DocumentType, DocumentStatus
from ...schemas.documento import (
    DocumentoResponse, DocumentoDetail, DocumentoSearch,
    DocumentoSearchResponse, DocumentoExportRequest
)
from ...services.documento import DocumentService
from ...services.ai.document_processor import DocumentProcessor
from ...services.ai.ai_service import AIService
from ...services.export_service import ExportService
from ..deps import get_current_user
import logging
from pathlib import Path
import shutil
import hashlib
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=DocumentoResponse)
async def upload_documento(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    tipo_documento: DocumentType,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Carica un nuovo documento e avvia l'elaborazione in background.
    """
    try:
        # Verifica estensione file
        file_extension = Path(file.filename).suffix.lower()
        allowed_extensions = [".pdf", ".doc", ".docx", ".txt", ".jpg", ".png", ".tiff"]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Estensione file non supportata. Estensioni permesse: {', '.join(allowed_extensions)}"
            )
        
        # Crea directory per i file se non esiste
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Genera nome file univoco
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(file.filename).stem.replace(" ", "_")
        new_filename = f"{safe_filename}_{timestamp}{file_extension}"
        file_path = upload_dir / new_filename
        
        # Salva il file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calcola hash del file
        sha256_hash = hashlib.sha256()
        with file_path.open("rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Crea il documento nel database
        db_documento = Documento(
            filename=file.filename,
            tipo_documento=tipo_documento,
            mime_type=file.content_type,
            dimensione=file.size,
            hash_file=sha256_hash.hexdigest(),
            percorso_file=str(file_path),
            stato_elaborazione=DocumentStatus.PENDING
        )
        
        db.add(db_documento)
        db.commit()
        db.refresh(db_documento)
        
        # Avvia elaborazione in background
        background_tasks.add_task(
            process_document_background,
            documento_id=db_documento.id,
            db=db
        )
        
        return db_documento
        
    except Exception as e:
        logger.error(f"Errore nel caricamento del documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{documento_id}", response_model=DocumentoDetail)
async def get_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Recupera i dettagli di un documento specifico.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return documento

@router.get("/search", response_model=DocumentoSearchResponse)
async def search_documenti(
    search_params: DocumentoSearch,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Ricerca semantica nei documenti.
    """
    try:
        doc_service = DocumentService(db)
        results = await doc_service.search_documents(
            query=search_params.query,
            tipo_documento=search_params.tipo_documento,
            data_inizio=search_params.data_inizio,
            data_fine=search_params.data_fine,
            limit=search_params.limit,
            include_content=search_params.include_content
        )
        return results
    except Exception as e:
        logger.error(f"Errore nella ricerca documenti: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{documento_id}/export")
async def export_documento(
    documento_id: int,
    export_request: DocumentoExportRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Esporta un documento in un formato specifico.
    """
    try:
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            raise HTTPException(status_code=404, detail="Documento non trovato")
            
        export_path = await export_document(
            documento=documento,
            format=export_request.format,
            include_metadata=export_request.include_metadata,
            include_content=export_request.include_content
        )
        
        return {"export_path": str(export_path)}
        
    except Exception as e:
        logger.error(f"Errore nell'esportazione del documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{documento_id}/analyze")
async def analyze_document(
    documento_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Avvia l'analisi approfondita di un documento.
    """
    try:
        # Recupera documento
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            raise HTTPException(status_code=404, detail="Documento non trovato")
            
        # Verifica stato
        if documento.stato_elaborazione == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=400,
                detail="Documento già in elaborazione"
            )
            
        # Inizializza servizi
        doc_processor = DocumentProcessor()
        ai_service = AIService()
        
        # Aggiorna stato
        documento.stato_elaborazione = DocumentStatus.PROCESSING
        db.commit()
        
        try:
            # Analizza documento
            analysis = await doc_processor.analyze_document(documento.percorso_file)
            
            # Aggiorna documento con risultati
            documento.contenuto = analysis["text"]
            documento.embedding = analysis["embedding"]
            if documento.tipo_documento == DocumentType.ALTRO:
                documento.tipo_documento = DocumentType(analysis["document_type"])
            
            # Estrai entità e genera riassunto in background
            background_tasks.add_task(
                _process_document_background,
                documento_id=documento.id,
                text=analysis["text"],
                db=db
            )
            
            # Aggiorna stato
            documento.stato_elaborazione = DocumentStatus.COMPLETED
            documento.data_elaborazione = datetime.utcnow()
            db.commit()
            
            return {"status": "success", "message": "Analisi completata"}
            
        except Exception as e:
            documento.stato_elaborazione = DocumentStatus.ERROR
            documento.errore = str(e)
            db.commit()
            raise
            
    except Exception as e:
        logger.error(f"Errore nell'analisi del documento {documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{documento_id}/entities")
async def get_document_entities(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Recupera le entità estratte da un documento.
    """
    try:
        # Recupera documento
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            raise HTTPException(status_code=404, detail="Documento non trovato")
            
        # Verifica presenza metadati
        if not documento.metadata or "entities" not in documento.metadata:
            raise HTTPException(
                status_code=400,
                detail="Entità non ancora estratte. Esegui prima l'analisi del documento."
            )
            
        return documento.metadata["entities"]
        
    except Exception as e:
        logger.error(f"Errore nel recupero delle entità del documento {documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
async def generate_documents_report(
    tipo_documento: Optional[DocumentType] = None,
    data_inizio: Optional[datetime] = None,
    data_fine: Optional[datetime] = None,
    format: str = Query("pdf", regex="^(pdf|excel|json)$"),
    include_content: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Genera un report dei documenti in vari formati.
    """
    try:
        # Costruisci query
        query = db.query(Documento)
        if tipo_documento:
            query = query.filter(Documento.tipo_documento == tipo_documento)
        if data_inizio:
            query = query.filter(Documento.data_caricamento >= data_inizio)
        if data_fine:
            query = query.filter(Documento.data_caricamento <= data_fine)
            
        # Recupera documenti
        documenti = query.all()
        
        # Inizializza servizio export
        export_service = ExportService()
        
        # Genera report nel formato richiesto
        if format == "pdf":
            export_path = await export_service.generate_report(
                documenti=documenti,
                include_stats=True
            )
        elif format == "excel":
            export_path = await export_service.export_to_excel(
                documenti=documenti,
                include_content=include_content
            )
        elif format == "json":
            export_path = await export_service.export_structured_data(
                documenti=documenti,
                format="json"
            )
            
        return {"export_path": str(export_path)}
        
    except Exception as e:
        logger.error(f"Errore nella generazione del report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze")
async def batch_analyze_documents(
    documento_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Avvia l'analisi di un gruppo di documenti.
    """
    try:
        # Recupera documenti
        documenti = db.query(Documento).filter(Documento.id.in_(documento_ids)).all()
        if not documenti:
            raise HTTPException(status_code=404, detail="Nessun documento trovato")
            
        # Verifica stati
        for doc in documenti:
            if doc.stato_elaborazione == DocumentStatus.PROCESSING:
                raise HTTPException(
                    status_code=400,
                    detail=f"Documento {doc.id} già in elaborazione"
                )
                
        # Avvia analisi in background per ogni documento
        for doc in documenti:
            doc.stato_elaborazione = DocumentStatus.PROCESSING
            background_tasks.add_task(
                _analyze_document_background,
                documento_id=doc.id,
                db=db
            )
            
        db.commit()
        
        return {
            "status": "success",
            "message": f"Avviata analisi di {len(documenti)} documenti",
            "documento_ids": [d.id for d in documenti]
        }
        
    except Exception as e:
        logger.error(f"Errore nell'analisi batch dei documenti: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_document_background(
    documento_id: int,
    text: str,
    db: Session
):
    """
    Elabora un documento in background estraendo entità e generando riassunto.
    """
    try:
        # Recupera documento
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            logger.error(f"Documento {documento_id} non trovato")
            return
            
        # Inizializza servizio AI
        ai_service = AIService()
        
        try:
            # Estrai entità
            entities = await ai_service.extract_entities(text)
            
            # Genera riassunto
            summary = await ai_service.generate_summary(text)
            
            # Aggiorna metadati
            documento.metadata = documento.metadata or {}
            documento.metadata.update({
                "entities": entities,
                "summary": summary
            })
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione del documento {documento_id}: {str(e)}")
            documento.stato_elaborazione = DocumentStatus.ERROR
            documento.errore = str(e)
            db.commit()
            
    except Exception as e:
        logger.error(f"Errore nel processo background per documento {documento_id}: {str(e)}")

async def _analyze_document_background(documento_id: int, db: Session):
    """
    Analizza un documento in background.
    """
    try:
        # Recupera documento
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            logger.error(f"Documento {documento_id} non trovato")
            return
            
        # Inizializza servizi
        doc_processor = DocumentProcessor()
        
        try:
            # Analizza documento
            analysis = await doc_processor.analyze_document(documento.percorso_file)
            
            # Aggiorna documento con risultati
            documento.contenuto = analysis["text"]
            documento.embedding = analysis["embedding"]
            if documento.tipo_documento == DocumentType.ALTRO:
                documento.tipo_documento = DocumentType(analysis["document_type"])
                
            # Aggiorna stato
            documento.stato_elaborazione = DocumentStatus.COMPLETED
            documento.data_elaborazione = datetime.utcnow()
            db.commit()
            
            # Avvia elaborazione entità e riassunto
            await _process_document_background(
                documento_id=documento.id,
                text=analysis["text"],
                db=db
            )
            
        except Exception as e:
            documento.stato_elaborazione = DocumentStatus.ERROR
            documento.errore = str(e)
            db.commit()
            raise
            
    except Exception as e:
        logger.error(f"Errore nell'analisi background del documento {documento_id}: {str(e)}") 