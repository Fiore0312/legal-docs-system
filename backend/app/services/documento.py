from typing import List, Dict, Any, Optional
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session
from ..models.documento import Documento, DocumentStatus, DocumentType
from ..core.config import get_settings
from .ai.document_processor import DocumentProcessor
import logging
import shutil
import json

settings = get_settings()
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.processor = DocumentProcessor()
        
    async def extract_text(self, file_path: str) -> str:
        """
        Estrae il testo da un documento usando OCR se necessario.
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                # Converti PDF in immagini e applica OCR
                images = convert_from_path(file_path)
                text = ""
                for image in images:
                    text += pytesseract.image_to_string(image, lang='ita')
                return text
                
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff']:
                # Applica OCR direttamente all'immagine
                return pytesseract.image_to_string(file_path, lang='ita')
                
            elif file_ext in ['.txt', '.doc', '.docx']:
                # TODO: Implementa estrazione testo per altri formati
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
            else:
                raise ValueError(f"Formato file non supportato: {file_ext}")
                
        except Exception as e:
            logger.error(f"Errore nell'estrazione del testo da {file_path}: {str(e)}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera l'embedding per il testo del documento.
        """
        try:
            return await self.processor._create_embedding(text)
        except Exception as e:
            logger.error(f"Errore nella generazione dell'embedding: {str(e)}")
            raise

    async def classify_document(self, text: str) -> DocumentType:
        """
        Classifica automaticamente il tipo di documento.
        """
        try:
            result = await self.processor._classify_document(text)
            return DocumentType(result.lower())
        except Exception as e:
            logger.error(f"Errore nella classificazione del documento: {str(e)}")
            raise

    async def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Estrae metadati dal testo del documento.
        """
        try:
            return await self.processor._extract_entities(text)
        except Exception as e:
            logger.error(f"Errore nell'estrazione dei metadati: {str(e)}")
            raise

    async def search_documents(
        self,
        query: str,
        tipo_documento: Optional[DocumentType] = None,
        data_inizio: Optional[datetime] = None,
        data_fine: Optional[datetime] = None,
        limit: int = 10,
        include_content: bool = False
    ) -> Dict[str, Any]:
        """
        Esegue una ricerca semantica nei documenti.
        """
        try:
            # Genera embedding della query
            query_embedding = await self.generate_embedding(query)
            
            # Costruisci query di base
            base_query = self.db.query(Documento)
            
            # Applica filtri
            if tipo_documento:
                base_query = base_query.filter(Documento.tipo_documento == tipo_documento)
            if data_inizio:
                base_query = base_query.filter(Documento.data_caricamento >= data_inizio)
            if data_fine:
                base_query = base_query.filter(Documento.data_caricamento <= data_fine)
                
            # Recupera documenti
            documenti = base_query.all()
            
            # Calcola similarità
            results = []
            for doc in documenti:
                if doc.embedding:
                    similarity = np.dot(query_embedding, doc.embedding)
                    if similarity > settings.SIMILARITY_THRESHOLD:
                        result = {
                            "documento": doc,
                            "score": float(similarity),
                            "highlights": []  # TODO: Implementa evidenziazione del testo
                        }
                        if include_content and doc.contenuto:
                            result["highlights"] = self._get_highlights(doc.contenuto, query)
                        results.append(result)
            
            # Ordina per score e limita risultati
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:limit]
            
            return {
                "results": results,
                "total": len(results),
                "page": 1,
                "page_size": limit
            }
            
        except Exception as e:
            logger.error(f"Errore nella ricerca dei documenti: {str(e)}")
            raise

    def _get_highlights(self, text: str, query: str, context_chars: int = 100) -> List[str]:
        """
        Estrae frammenti di testo rilevanti intorno alle occorrenze della query.
        """
        highlights = []
        try:
            # Implementazione semplificata - da migliorare con NLP
            text_lower = text.lower()
            query_lower = query.lower()
            
            start = 0
            while True:
                pos = text_lower.find(query_lower, start)
                if pos == -1:
                    break
                    
                # Estrai contesto
                highlight_start = max(0, pos - context_chars)
                highlight_end = min(len(text), pos + len(query) + context_chars)
                highlight = text[highlight_start:highlight_end]
                
                # Aggiungi ellipsis se necessario
                if highlight_start > 0:
                    highlight = "..." + highlight
                if highlight_end < len(text):
                    highlight = highlight + "..."
                    
                highlights.append(highlight)
                start = pos + len(query)
                
            return highlights[:3]  # Limita a 3 highlights
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione degli highlights: {str(e)}")
            return []

async def process_document_background(documento_id: int, db: Session):
    """
    Elabora un documento in background.
    """
    try:
        # Recupera il documento
        documento = db.query(Documento).filter(Documento.id == documento_id).first()
        if not documento:
            logger.error(f"Documento {documento_id} non trovato")
            return
            
        # Aggiorna stato
        documento.stato_elaborazione = DocumentStatus.PROCESSING
        db.commit()
        
        # Inizializza servizio
        service = DocumentService(db)
        
        try:
            # Estrai testo
            documento.contenuto = await service.extract_text(documento.percorso_file)
            
            # Genera embedding
            documento.embedding = await service.generate_embedding(documento.contenuto)
            
            # Classifica documento se non specificato
            if documento.tipo_documento == DocumentType.ALTRO:
                documento.tipo_documento = await service.classify_document(documento.contenuto)
            
            # Estrai metadati
            documento.metadata = await service.extract_metadata(documento.contenuto)
            
            # Aggiorna stato
            documento.stato_elaborazione = DocumentStatus.COMPLETED
            documento.data_elaborazione = datetime.utcnow()
            
        except Exception as e:
            documento.stato_elaborazione = DocumentStatus.ERROR
            documento.errore = str(e)
            raise
            
        finally:
            db.commit()
            
    except Exception as e:
        logger.error(f"Errore nell'elaborazione del documento {documento_id}: {str(e)}")
        try:
            documento.stato_elaborazione = DocumentStatus.ERROR
            documento.errore = str(e)
            db.commit()
        except:
            pass

async def export_document(
    documento: Documento,
    format: str,
    include_metadata: bool = True,
    include_content: bool = True
) -> Path:
    """
    Esporta un documento nel formato richiesto.
    """
    try:
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{documento.id}_{timestamp}.{format}"
        export_path = export_dir / export_filename
        
        if format == "pdf":
            # Copia il PDF originale se il documento è un PDF
            if documento.percorso_file.endswith(".pdf"):
                shutil.copy2(documento.percorso_file, export_path)
            else:
                # TODO: Implementa conversione in PDF
                raise NotImplementedError("Conversione in PDF non ancora implementata")
                
        elif format == "txt":
            # Esporta solo il testo
            with export_path.open("w", encoding="utf-8") as f:
                if include_metadata:
                    f.write("=== Metadati ===\n")
                    f.write(json.dumps(documento.metadata, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                if include_content and documento.contenuto:
                    f.write("=== Contenuto ===\n")
                    f.write(documento.contenuto)
                    
        elif format == "json":
            # Esporta tutto in JSON
            data = {
                "id": documento.id,
                "filename": documento.filename,
                "tipo_documento": documento.tipo_documento.value,
                "data_caricamento": documento.data_caricamento.isoformat(),
                "data_elaborazione": documento.data_elaborazione.isoformat() if documento.data_elaborazione else None,
            }
            if include_metadata:
                data["metadata"] = documento.metadata
            if include_content:
                data["contenuto"] = documento.contenuto
                
            with export_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        else:
            raise ValueError(f"Formato di esportazione non supportato: {format}")
            
        return export_path
        
    except Exception as e:
        logger.error(f"Errore nell'esportazione del documento {documento.id}: {str(e)}")
        raise 