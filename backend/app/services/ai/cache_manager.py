from typing import Dict, Any, Optional
import json
import hashlib
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from ...models.documento import Documento
from ...core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, db: Session):
        self.db = db
        self.cache_duration = timedelta(hours=24)  # Cache valida per 24 ore

    def _generate_cache_key(self, content: str, operation: str) -> str:
        """
        Genera una chiave univoca per la cache basata sul contenuto e l'operazione.
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"{operation}_{content_hash}"

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """
        Verifica se la cache è ancora valida.
        """
        return datetime.utcnow() - timestamp < self.cache_duration

    async def get_cached_result(
        self,
        documento: Documento,
        operation: str
    ) -> Optional[Dict[str, Any]]:
        """
        Recupera il risultato dalla cache se disponibile e valido.
        """
        try:
            if not documento.metadata:
                return None

            cache_key = self._generate_cache_key(documento.contenuto or "", operation)
            cached_data = documento.metadata.get("cache", {}).get(cache_key)

            if not cached_data:
                return None

            cached_timestamp = datetime.fromisoformat(cached_data.get("timestamp"))
            if not self._is_cache_valid(cached_timestamp):
                return None

            logger.info(f"Cache hit per {operation} su documento {documento.id}")
            return cached_data.get("result")

        except Exception as e:
            logger.error(f"Errore nel recupero della cache: {str(e)}")
            return None

    async def set_cached_result(
        self,
        documento: Documento,
        operation: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Salva il risultato nella cache.
        """
        try:
            if not documento.metadata:
                documento.metadata = {}

            if "cache" not in documento.metadata:
                documento.metadata["cache"] = {}

            cache_key = self._generate_cache_key(documento.contenuto or "", operation)
            documento.metadata["cache"][cache_key] = {
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"  # Per gestire versioni future della cache
            }

            self.db.add(documento)
            self.db.commit()
            logger.info(f"Risultato cachato per {operation} su documento {documento.id}")

        except Exception as e:
            logger.error(f"Errore nel salvataggio della cache: {str(e)}")
            self.db.rollback()

    async def invalidate_cache(self, documento: Documento) -> None:
        """
        Invalida la cache per un documento.
        """
        try:
            if documento.metadata and "cache" in documento.metadata:
                del documento.metadata["cache"]
                self.db.add(documento)
                self.db.commit()
                logger.info(f"Cache invalidata per documento {documento.id}")

        except Exception as e:
            logger.error(f"Errore nell'invalidazione della cache: {str(e)}")
            self.db.rollback()

    async def get_cached_embedding(self, documento: Documento) -> Optional[list]:
        """
        Recupera l'embedding dalla cache.
        """
        try:
            if not documento.embedding:
                return None

            metadata = documento.metadata or {}
            embedding_timestamp = metadata.get("embedding_timestamp")
            
            if not embedding_timestamp:
                return None

            if not self._is_cache_valid(datetime.fromisoformat(embedding_timestamp)):
                return None

            return documento.embedding

        except Exception as e:
            logger.error(f"Errore nel recupero dell'embedding dalla cache: {str(e)}")
            return None

    async def set_cached_embedding(
        self,
        documento: Documento,
        embedding: list
    ) -> None:
        """
        Salva l'embedding nella cache.
        """
        try:
            documento.embedding = embedding
            if not documento.metadata:
                documento.metadata = {}
            
            documento.metadata["embedding_timestamp"] = datetime.utcnow().isoformat()
            documento.metadata["embedding_version"] = "1.0"

            self.db.add(documento)
            self.db.commit()
            logger.info(f"Embedding cachato per documento {documento.id}")

        except Exception as e:
            logger.error(f"Errore nel salvataggio dell'embedding nella cache: {str(e)}")
            self.db.rollback()

    def clear_expired_cache(self) -> None:
        """
        Rimuove tutte le cache scadute dal database.
        """
        try:
            documenti = self.db.query(Documento).all()
            now = datetime.utcnow()
            
            for doc in documenti:
                if not doc.metadata or "cache" not in doc.metadata:
                    continue

                # Filtra le cache valide
                valid_cache = {}
                for key, cache_data in doc.metadata["cache"].items():
                    timestamp = datetime.fromisoformat(cache_data["timestamp"])
                    if self._is_cache_valid(timestamp):
                        valid_cache[key] = cache_data

                # Aggiorna solo se ci sono state modifiche
                if len(valid_cache) != len(doc.metadata["cache"]):
                    doc.metadata["cache"] = valid_cache
                    self.db.add(doc)

            self.db.commit()
            logger.info("Pulizia cache completata")

        except Exception as e:
            logger.error(f"Errore nella pulizia della cache: {str(e)}")
            self.db.rollback() 