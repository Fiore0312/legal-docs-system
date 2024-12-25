#!/usr/bin/env python3
"""
Script di esempio per l'upload e l'analisi di documenti.
Dimostra come:
1. Autenticarsi al sistema
2. Caricare un documento
3. Avviare l'analisi
4. Monitorare lo stato
5. Recuperare i risultati
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any
import logging

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

def upload_document(token: str, file_path: Path, tipo_documento: str) -> Dict[str, Any]:
    """
    Carica un documento nel sistema.
    
    Args:
        token: Token di autenticazione
        file_path: Path al file da caricare
        tipo_documento: Tipo di documento (DECRETO, SENTENZA, PERIZIA)
    
    Returns:
        Dict con i dettagli del documento caricato
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
        raise Exception(f"Upload fallito: {response.json()['detail']}")
    
    return response.json()

def analyze_document(token: str, doc_id: int) -> None:
    """
    Avvia l'analisi di un documento.
    
    Args:
        token: Token di autenticazione
        doc_id: ID del documento da analizzare
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_BASE_URL}/documenti/{doc_id}/analyze",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Avvio analisi fallito: {response.json()['detail']}")
    
    logger.info("Analisi avviata")

def wait_for_analysis(token: str, doc_id: int) -> Dict[str, Any]:
    """
    Attende il completamento dell'analisi.
    
    Args:
        token: Token di autenticazione
        doc_id: ID del documento
    
    Returns:
        Dict con i risultati dell'analisi
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    for _ in range(MAX_RETRIES):
        response = requests.get(
            f"{API_BASE_URL}/documenti/{doc_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Errore nel controllo stato: {response.json()['detail']}")
        
        doc_data = response.json()
        if doc_data["stato_elaborazione"] == "COMPLETED":
            return doc_data
        elif doc_data["stato_elaborazione"] == "ERROR":
            raise Exception("Errore nell'elaborazione del documento")
        
        logger.info("Elaborazione in corso...")
        time.sleep(RETRY_DELAY)
    
    raise Exception("Timeout nell'attesa dell'elaborazione")

def get_entities(token: str, doc_id: int) -> Dict[str, Any]:
    """
    Recupera le entità estratte dal documento.
    
    Args:
        token: Token di autenticazione
        doc_id: ID del documento
    
    Returns:
        Dict con le entità estratte
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_BASE_URL}/documenti/{doc_id}/entities",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Errore nel recupero entità: {response.json()['detail']}")
    
    return response.json()

def main():
    """
    Funzione principale che dimostra il flusso completo.
    """
    try:
        # 1. Login
        logger.info("Effettuo login...")
        token = get_token()
        
        # 2. Upload documento
        file_path = Path("test_files/decreto_esempio.pdf")
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")
        
        logger.info(f"Carico documento: {file_path}")
        doc_data = upload_document(token, file_path, "DECRETO")
        doc_id = doc_data["id"]
        
        # 3. Avvia analisi
        logger.info("Avvio analisi...")
        analyze_document(token, doc_id)
        
        # 4. Attendi completamento
        logger.info("Attendo completamento analisi...")
        result = wait_for_analysis(token, doc_id)
        
        # 5. Recupera entità
        logger.info("Recupero entità estratte...")
        entities = get_entities(token, doc_id)
        
        # 6. Stampa risultati
        logger.info("\nRisultati analisi:")
        logger.info(f"Documento ID: {doc_id}")
        logger.info(f"Filename: {result['filename']}")
        logger.info(f"Tipo: {result['tipo_documento']}")
        logger.info("\nEntità estratte:")
        for tipo, items in entities.items():
            logger.info(f"{tipo}: {', '.join(items)}")
        
    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 