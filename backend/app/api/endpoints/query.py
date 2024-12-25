from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.database import get_db
from ...models.documento import DocumentType
from ...services.query_engine import QueryEngine
from ...services.report_generator import ReportGenerator
from ..deps import get_current_user
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class NaturalQuery(BaseModel):
    query: str
    include_content: bool = False
    limit: int = 10
    offset: int = 0

class AggregationRequest(BaseModel):
    query_id: Optional[str] = None
    group_by: List[str]
    metrics: List[str]
    filters: Optional[dict] = None

class ExportRequest(BaseModel):
    query_id: str
    format: str = "pdf"
    include_stats: bool = True
    include_content: bool = False

@router.post("/semantic-search")
async def semantic_search(
    query: NaturalQuery,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Esegue una ricerca semantica usando query in linguaggio naturale.
    
    Esempio query:
    - "Trova tutti i decreti del 2023 che menzionano Mario Rossi"
    - "Cerca documenti con importi superiori a 10.000€ negli ultimi 6 mesi"
    - "Mostra sentenze che citano l'articolo 1218 del codice civile"
    """
    try:
        # Inizializza query engine
        query_engine = QueryEngine(db)
        
        # Parsa query naturale
        search_params = await query_engine.parse_natural_query(query.query)
        
        # Esegui ricerca
        results = await query_engine.semantic_search(
            query=search_params["search_text"],
            filters=search_params,
            limit=query.limit,
            offset=query.offset
        )
        
        # Salva risultati in cache per aggregazioni
        # TODO: Implementa caching risultati
        
        return results
        
    except Exception as e:
        logger.error(f"Errore nella ricerca semantica: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aggregate")
async def aggregate_results(
    request: AggregationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Aggrega i risultati di una ricerca per varie dimensioni.
    
    Dimensioni disponibili:
    - tipo_documento: Conta documenti per tipo
    - data: Serie temporale documenti
    - entities: Frequenza entità estratte
    
    Metriche disponibili:
    - avg_score: Score medio di rilevanza
    - importi: Statistiche sugli importi
    """
    try:
        # Recupera risultati dalla cache
        # TODO: Implementa recupero da cache
        results = []  # Placeholder
        
        # Inizializza query engine
        query_engine = QueryEngine(db)
        
        # Calcola aggregazioni
        aggregations = await query_engine.aggregate_results(
            query_results=results,
            group_by=request.group_by,
            metrics=request.metrics
        )
        
        return aggregations
        
    except Exception as e:
        logger.error(f"Errore nell'aggregazione dei risultati: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline")
async def get_timeline(
    start_date: datetime,
    end_date: datetime,
    group_by: str = QueryParam("month", regex="^(day|week|month|year)$"),
    tipo_documento: Optional[DocumentType] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Genera una timeline di eventi dai documenti.
    
    Parametri:
    - start_date: Data inizio periodo
    - end_date: Data fine periodo
    - group_by: Raggruppamento (day|week|month|year)
    - tipo_documento: Filtra per tipo documento
    """
    try:
        # Costruisci query base
        query = db.query(Documento)
        
        # Applica filtri
        query = query.filter(Documento.data_caricamento.between(start_date, end_date))
        if tipo_documento:
            query = query.filter(Documento.tipo_documento == tipo_documento)
            
        # Recupera documenti
        documenti = query.all()
        
        # Inizializza query engine
        query_engine = QueryEngine(db)
        
        # Genera timeline
        timeline = await query_engine.generate_timeline(
            documenti=documenti,
            group_by=group_by
        )
        
        return timeline
        
    except Exception as e:
        logger.error(f"Errore nella generazione della timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-results")
async def export_results(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Esporta i risultati di una ricerca in vari formati.
    
    Formati supportati:
    - PDF: Report completo con statistiche
    - Excel: Dati strutturati in formato tabellare
    - JSON: Dati raw per elaborazioni
    """
    try:
        # Recupera risultati dalla cache
        # TODO: Implementa recupero da cache
        results = []  # Placeholder
        
        # Inizializza report generator
        report_gen = ReportGenerator()
        
        # Genera report nel formato richiesto
        if request.format == "pdf":
            export_path = await report_gen.generate_pdf_report(
                results,
                include_stats=request.include_stats,
                include_content=request.include_content
            )
        elif request.format == "excel":
            export_path = await report_gen.export_to_excel(
                results,
                include_content=request.include_content
            )
        elif request.format == "json":
            export_path = await report_gen.export_to_json(results)
        else:
            raise ValueError(f"Formato non supportato: {request.format}")
            
        return {"export_path": str(export_path)}
        
    except Exception as e:
        logger.error(f"Errore nell'esportazione dei risultati: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 