from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ...db.database import get_db
from ...models.documento import Documento
from ...services.ai.document_processor import DocumentProcessor
from ...services.ai.cache_manager import CacheManager
from ..deps import get_current_user, check_admin_permission
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{documento_id}/analyze")
async def analyze_document(
    documento_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Avvia l'analisi AI di un documento.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    try:
        processor = DocumentProcessor()
        cache_manager = CacheManager(db)

        # Verifica se esiste una cache valida
        cached_result = await cache_manager.get_cached_result(documento, "analyze")
        if cached_result:
            return {
                "status": "completed",
                "result": cached_result,
                "from_cache": True
            }

        # Avvia l'elaborazione in background
        background_tasks.add_task(
            process_document_background,
            documento_id=documento_id,
            db=db
        )

        return {
            "status": "processing",
            "message": "Elaborazione documento avviata"
        }

    except Exception as e:
        logger.error(f"Errore nell'analisi del documento {documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore nell'elaborazione del documento")

@router.get("/{documento_id}/status")
async def get_analysis_status(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Verifica lo stato dell'analisi di un documento.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    return {
        "status": documento.stato_elaborazione,
        "metadata": documento.metadata
    }

@router.get("/search")
async def semantic_search(
    query: str,
    limit: int = Query(default=5, ge=1, le=20),
    threshold: float = Query(default=0.7, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Esegue una ricerca semantica nei documenti.
    """
    try:
        processor = DocumentProcessor()
        results = await processor.search_similar_documents(
            query=query,
            limit=limit,
            threshold=threshold
        )
        
        return {
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"Errore nella ricerca semantica: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore nella ricerca")

@router.post("/{documento_id}/extract-entities")
async def extract_entities(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Estrae le entità da un documento.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    try:
        processor = DocumentProcessor()
        cache_manager = CacheManager(db)

        # Verifica cache
        cached_result = await cache_manager.get_cached_result(documento, "entities")
        if cached_result:
            return {
                "entities": cached_result,
                "from_cache": True
            }

        # Estrai entità
        if not documento.contenuto:
            raise HTTPException(status_code=400, detail="Contenuto documento non disponibile")

        entities = await processor._extract_entities(documento.contenuto)
        
        # Salva in cache
        await cache_manager.set_cached_result(documento, "entities", entities)

        return {
            "entities": entities,
            "from_cache": False
        }

    except Exception as e:
        logger.error(f"Errore nell'estrazione delle entità dal documento {documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore nell'estrazione delle entità")

@router.post("/{documento_id}/summarize")
async def summarize_document(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Genera un riassunto del documento.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    try:
        processor = DocumentProcessor()
        cache_manager = CacheManager(db)

        # Verifica cache
        cached_result = await cache_manager.get_cached_result(documento, "summary")
        if cached_result:
            return {
                "summary": cached_result,
                "from_cache": True
            }

        # Genera riassunto
        if not documento.contenuto:
            raise HTTPException(status_code=400, detail="Contenuto documento non disponibile")

        chunks = processor._create_chunks(documento.contenuto)
        summary = await processor._generate_summary(chunks)
        
        # Salva in cache
        await cache_manager.set_cached_result(documento, "summary", summary)

        return {
            "summary": summary,
            "from_cache": False
        }

    except Exception as e:
        logger.error(f"Errore nella generazione del riassunto per il documento {documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore nella generazione del riassunto")

@router.post("/clear-cache")
async def clear_cache(
    db: Session = Depends(get_db),
    current_user = Depends(check_admin_permission)
):
    """
    Pulisce la cache scaduta (solo admin).
    """
    try:
        cache_manager = CacheManager(db)
        cache_manager.clear_expired_cache()
        return {"message": "Cache pulita con successo"}
    except Exception as e:
        logger.error(f"Errore nella pulizia della cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore nella pulizia della cache")

async def process_document_background(documento_id: int, db: Session):
    """
    Elabora un documento in background.
    """
    try:
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            logger.error(f"Documento {documento_id} non trovato per elaborazione background")
            return

        documento.stato_elaborazione = "in_elaborazione"
        db.commit()

        processor = DocumentProcessor()
        cache_manager = CacheManager(db)

        # Elabora il documento
        result = await processor.process_document(documento)
        
        # Salva risultati in cache
        await cache_manager.set_cached_result(documento, "analyze", result)
        
        documento.stato_elaborazione = "completato"
        db.commit()

    except Exception as e:
        logger.error(f"Errore nell'elaborazione background del documento {documento_id}: {str(e)}")
        documento.stato_elaborazione = "errore"
        documento.metadata = documento.metadata or {}
        documento.metadata["error"] = str(e)
        db.commit() 