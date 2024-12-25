#!/usr/bin/env python3
"""
Script di esempio per l'elaborazione batch di documenti.
Dimostra come:
1. Caricare multipli documenti
2. Avviare elaborazione batch
3. Monitorare progresso
4. Gestire errori
5. Generare report
"""

import os
import sys
import time
from pathlib import Path
import requests
from typing import Dict, List, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione
API_BASE_URL = "http://localhost:8000"
EMAIL = "user@example.com"
PASSWORD = "password123"
MAX_WORKERS = 4
MAX_RETRIES = 10
RETRY_DELAY = 2

def get_token() -> str:
    """
    Ottiene un token di accesso tramite login.
    """
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Login fallito: {response.json()['detail']}")
    
    return response.json()["access_token"]

def upload_document(
    token: str,
    file_path: Path,
    tipo_documento: str
) -> Dict[str, Any]:
    """
    Carica un singolo documento.
    
    Args:
        token: Token di autenticazione
        file_path: Path al file
        tipo_documento: Tipo di documento
    
    Returns:
        Dict con dettagli documento caricato
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, "application/pdf")
        }
        data = {
            "tipo_documento": tipo_documento
        }
        
        response = requests.post(
            f"{API_BASE_URL}/documenti/upload",
            headers=headers,
            files=files,
            data=data
        )
    
    if response.status_code != 201:
        raise Exception(f"Upload fallito per {file_path}: {response.json()['detail']}")
    
    return response.json()

def batch_analyze(token: str, doc_ids: List[int]) -> Dict[str, Any]:
    """
    Avvia analisi batch di documenti.
    
    Args:
        token: Token di autenticazione
        doc_ids: Lista di ID documenti
    
    Returns:
        Dict con stato elaborazione
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/documenti/batch-analyze",
        headers=headers,
        json={"documento_ids": doc_ids}
    )
    
    if response.status_code != 200:
        raise Exception(f"Avvio batch fallito: {response.json()['detail']}")
    
    return response.json()

def check_document_status(token: str, doc_id: int) -> Dict[str, Any]:
    """
    Verifica stato elaborazione documento.
    
    Args:
        token: Token di autenticazione
        doc_id: ID documento
    
    Returns:
        Dict con stato documento
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_BASE_URL}/documenti/{doc_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Errore verifica stato doc {doc_id}: {response.json()['detail']}")
    
    return response.json()

def wait_for_completion(token: str, doc_ids: List[int]) -> Dict[str, Any]:
    """
    Attende completamento elaborazione batch.
    
    Args:
        token: Token di autenticazione
        doc_ids: Lista di ID documenti
    
    Returns:
        Dict con risultati elaborazione
    """
    results = {
        "completed": [],
        "failed": [],
        "timeout": []
    }
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        
        for doc_id in doc_ids:
            futures[executor.submit(monitor_document, token, doc_id)] = doc_id
        
        for future in as_completed(futures):
            doc_id = futures[future]
            try:
                status = future.result()
                if status["stato_elaborazione"] == "COMPLETED":
                    results["completed"].append(doc_id)
                elif status["stato_elaborazione"] == "ERROR":
                    results["failed"].append(doc_id)
                else:
                    results["timeout"].append(doc_id)
            except Exception as e:
                logger.error(f"Errore monitoraggio doc {doc_id}: {str(e)}")
                results["failed"].append(doc_id)
    
    return results

def monitor_document(token: str, doc_id: int) -> Dict[str, Any]:
    """
    Monitora elaborazione singolo documento.
    
    Args:
        token: Token di autenticazione
        doc_id: ID documento
    
    Returns:
        Dict con stato finale
    """
    for _ in range(MAX_RETRIES):
        status = check_document_status(token, doc_id)
        if status["stato_elaborazione"] in ["COMPLETED", "ERROR"]:
            return status
        time.sleep(RETRY_DELAY)
    
    return {"stato_elaborazione": "TIMEOUT"}

def generate_report(results: Dict[str, List[int]], doc_details: Dict[int, Dict]) -> None:
    """
    Genera report elaborazione batch.
    
    Args:
        results: Risultati elaborazione
        doc_details: Dettagli documenti
    """
    logger.info("\nReport Elaborazione Batch:")
    logger.info("-" * 50)
    
    # Statistiche generali
    total = len(doc_details)
    completed = len(results["completed"])
    failed = len(results["failed"])
    timeout = len(results["timeout"])
    
    logger.info(f"Totale documenti: {total}")
    logger.info(f"Completati: {completed} ({completed/total*100:.1f}%)")
    logger.info(f"Falliti: {failed} ({failed/total*100:.1f}%)")
    logger.info(f"Timeout: {timeout} ({timeout/total*100:.1f}%)")
    
    # Dettagli documenti completati
    if results["completed"]:
        logger.info("\nDocumenti Completati:")
        for doc_id in results["completed"]:
            doc = doc_details[doc_id]
            logger.info(f"- {doc['filename']} (ID: {doc_id})")
    
    # Dettagli errori
    if results["failed"]:
        logger.info("\nDocumenti Falliti:")
        for doc_id in results["failed"]:
            doc = doc_details[doc_id]
            logger.info(f"- {doc['filename']} (ID: {doc_id})")
    
    # Documenti in timeout
    if results["timeout"]:
        logger.info("\nDocumenti Timeout:")
        for doc_id in results["timeout"]:
            doc = doc_details[doc_id]
            logger.info(f"- {doc['filename']} (ID: {doc_id})")

def main():
    """
    Funzione principale che dimostra elaborazione batch.
    """
    try:
        # 1. Login
        logger.info("Effettuo login...")
        token = get_token()
        
        # 2. Prepara documenti
        docs_dir = Path("test_files")
        if not docs_dir.exists():
            raise FileNotFoundError(f"Directory {docs_dir} non trovata")
        
        pdf_files = list(docs_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError("Nessun file PDF trovato")
        
        # 3. Upload documenti
        logger.info(f"\nCarico {len(pdf_files)} documenti...")
        doc_details = {}
        
        for file_path in pdf_files:
            try:
                # Determina tipo documento dal nome file
                tipo = "DECRETO" if "decreto" in file_path.name.lower() else \
                       "SENTENZA" if "sentenza" in file_path.name.lower() else \
                       "PERIZIA"
                
                doc_data = upload_document(token, file_path, tipo)
                doc_details[doc_data["id"]] = doc_data
                logger.info(f"Caricato: {file_path.name} (ID: {doc_data['id']})")
                
            except Exception as e:
                logger.error(f"Errore caricamento {file_path}: {str(e)}")
        
        if not doc_details:
            raise Exception("Nessun documento caricato con successo")
        
        # 4. Avvia elaborazione batch
        logger.info("\nAvvio elaborazione batch...")
        doc_ids = list(doc_details.keys())
        batch_analyze(token, doc_ids)
        
        # 5. Monitora progresso
        logger.info("Monitoro elaborazione...")
        results = wait_for_completion(token, doc_ids)
        
        # 6. Genera report
        generate_report(results, doc_details)
        
    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 