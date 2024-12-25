from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import numpy as np
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
import pandas as pd
import logging
from ..models.documento import Documento, DocumentType, DocumentStatus
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self, db: Session):
        self.db = db
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.llm = OpenAI(
            temperature=0,
            model_name="gpt-4",
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Template per parsing query
        self.query_parser_template = PromptTemplate(
            input_variables=["query"],
            template="""
            Analizza la seguente query in linguaggio naturale ed estrai i parametri di ricerca:

            Query: {query}

            Estrai e formatta in JSON i seguenti parametri:
            1. Testo da cercare
            2. Tipo documento (se specificato)
            3. Range date (se specificato)
            4. Entità menzionate (persone, organizzazioni, luoghi)
            5. Altri filtri o condizioni

            Esempio output:
            {
                "search_text": "...",
                "doc_type": "...",
                "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
                "entities": {"people": [], "orgs": [], "places": []},
                "filters": {}
            }
            """
        )

    async def parse_natural_query(self, query: str) -> Dict[str, Any]:
        """
        Converte una query in linguaggio naturale in parametri strutturati.
        """
        try:
            # Usa LLM per interpretare la query
            chain = LLMChain(llm=self.llm, prompt=self.query_parser_template)
            result = await chain.arun(query=query)
            
            # Parsa risultato JSON
            params = eval(result)
            
            # Normalizza parametri
            if "doc_type" in params and params["doc_type"]:
                params["doc_type"] = DocumentType(params["doc_type"].lower())
                
            if "date_range" in params:
                for key in ["start", "end"]:
                    if params["date_range"].get(key):
                        params["date_range"][key] = datetime.strptime(
                            params["date_range"][key], "%Y-%m-%d"
                        )
                        
            return params
            
        except Exception as e:
            logger.error(f"Errore nel parsing della query: {str(e)}")
            raise

    async def semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Esegue una ricerca semantica con filtri opzionali.
        """
        try:
            # Genera embedding della query
            query_embedding = self.embeddings.embed_query(query)
            
            # Costruisci query base
            base_query = self.db.query(Documento)
            
            # Applica filtri
            if filters:
                if "doc_type" in filters:
                    base_query = base_query.filter(
                        Documento.tipo_documento == filters["doc_type"]
                    )
                    
                if "date_range" in filters:
                    if filters["date_range"].get("start"):
                        base_query = base_query.filter(
                            Documento.data_caricamento >= filters["date_range"]["start"]
                        )
                    if filters["date_range"].get("end"):
                        base_query = base_query.filter(
                            Documento.data_caricamento <= filters["date_range"]["end"]
                        )
                        
                if "entities" in filters:
                    entity_conditions = []
                    for entity_type, values in filters["entities"].items():
                        if values:
                            entity_conditions.append(
                                Documento.metadata["entities"][entity_type].contains(values)
                            )
                    if entity_conditions:
                        base_query = base_query.filter(or_(*entity_conditions))
            
            # Recupera documenti
            documenti = base_query.all()
            
            # Calcola similarità
            results = []
            for doc in documenti:
                if doc.embedding:
                    similarity = np.dot(query_embedding, doc.embedding)
                    if similarity > settings.SIMILARITY_THRESHOLD:
                        results.append({
                            "documento": doc,
                            "score": float(similarity)
                        })
            
            # Ordina per score e applica paginazione
            results.sort(key=lambda x: x["score"], reverse=True)
            paginated_results = results[offset:offset + limit]
            
            return {
                "total": len(results),
                "results": paginated_results,
                "page": offset // limit + 1,
                "page_size": limit
            }
            
        except Exception as e:
            logger.error(f"Errore nella ricerca semantica: {str(e)}")
            raise

    async def aggregate_results(
        self,
        query_results: List[Dict[str, Any]],
        group_by: List[str],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Aggrega i risultati della ricerca per varie dimensioni.
        """
        try:
            # Estrai documenti dai risultati
            docs = [r["documento"] for r in query_results]
            
            aggregations = {}
            
            # Aggregazione per tipo documento
            if "tipo_documento" in group_by:
                type_counts = {}
                for doc in docs:
                    tipo = doc.tipo_documento.value
                    type_counts[tipo] = type_counts.get(tipo, 0) + 1
                aggregations["by_type"] = type_counts
            
            # Aggregazione temporale
            if "data" in group_by:
                time_series = {}
                for doc in docs:
                    date_key = doc.data_caricamento.strftime("%Y-%m")
                    time_series[date_key] = time_series.get(date_key, 0) + 1
                aggregations["by_date"] = dict(sorted(time_series.items()))
            
            # Aggregazione per entità
            if "entities" in group_by:
                entity_counts = {
                    "persone": {},
                    "organizzazioni": {},
                    "luoghi": {}
                }
                for doc in docs:
                    if doc.metadata and "entities" in doc.metadata:
                        for entity_type, entities in doc.metadata["entities"].items():
                            if entity_type in entity_counts:
                                for entity in entities:
                                    entity_counts[entity_type][entity] = \
                                        entity_counts[entity_type].get(entity, 0) + 1
                aggregations["by_entity"] = entity_counts
            
            # Calcolo metriche
            if metrics:
                stats = {}
                if "avg_score" in metrics:
                    scores = [r["score"] for r in query_results]
                    stats["avg_score"] = sum(scores) / len(scores) if scores else 0
                    
                if "importi" in metrics:
                    total_amount = 0
                    count = 0
                    for doc in docs:
                        if doc.metadata and "entities" in doc.metadata:
                            importi = doc.metadata["entities"].get("importi", [])
                            for importo in importi:
                                try:
                                    # Converte importo da stringa a float
                                    amount = float(
                                        importo.replace(".", "").replace(",", ".")
                                    )
                                    total_amount += amount
                                    count += 1
                                except:
                                    continue
                    stats["total_amount"] = total_amount
                    stats["avg_amount"] = total_amount / count if count > 0 else 0
                    
                aggregations["metrics"] = stats
            
            return aggregations
            
        except Exception as e:
            logger.error(f"Errore nell'aggregazione dei risultati: {str(e)}")
            raise

    async def generate_timeline(
        self,
        documenti: List[Documento],
        group_by: str = "month"
    ) -> List[Dict[str, Any]]:
        """
        Genera una timeline di eventi dai documenti.
        """
        try:
            timeline = []
            
            # Raggruppa documenti per periodo
            if group_by == "day":
                format_str = "%Y-%m-%d"
            elif group_by == "week":
                format_str = "%Y-W%W"
            elif group_by == "month":
                format_str = "%Y-%m"
            else:
                format_str = "%Y"
                
            # Organizza documenti per data
            date_groups = {}
            for doc in documenti:
                date_key = doc.data_caricamento.strftime(format_str)
                if date_key not in date_groups:
                    date_groups[date_key] = []
                date_groups[date_key].append(doc)
            
            # Crea timeline
            for date_key, docs in sorted(date_groups.items()):
                entry = {
                    "period": date_key,
                    "count": len(docs),
                    "documents": [{
                        "id": doc.id,
                        "tipo": doc.tipo_documento.value,
                        "filename": doc.filename,
                        "summary": doc.metadata.get("summary", "") if doc.metadata else ""
                    } for doc in docs],
                    "stats": {
                        "by_type": {},
                        "entities": {
                            "persone": set(),
                            "organizzazioni": set(),
                            "luoghi": set()
                        }
                    }
                }
                
                # Calcola statistiche per periodo
                for doc in docs:
                    # Conta per tipo
                    tipo = doc.tipo_documento.value
                    entry["stats"]["by_type"][tipo] = \
                        entry["stats"]["by_type"].get(tipo, 0) + 1
                    
                    # Raccogli entità
                    if doc.metadata and "entities" in doc.metadata:
                        for entity_type in ["persone", "organizzazioni", "luoghi"]:
                            entities = doc.metadata["entities"].get(entity_type, [])
                            entry["stats"]["entities"][entity_type].update(entities)
                
                # Converti set in liste per JSON
                for entity_type in entry["stats"]["entities"]:
                    entry["stats"]["entities"][entity_type] = \
                        sorted(list(entry["stats"]["entities"][entity_type]))
                
                timeline.append(entry)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Errore nella generazione della timeline: {str(e)}")
            raise 