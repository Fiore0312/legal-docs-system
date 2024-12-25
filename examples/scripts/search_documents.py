#!/usr/bin/env python3
"""
Script di esempio per la ricerca semantica di documenti.
Dimostra come:
1. Eseguire ricerche semantiche
2. Applicare filtri
3. Ordinare risultati
4. Esportare risultati
"""

import os
import sys
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any
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

def semantic_search(
    token: str,
    query: str,
    filters: Dict[str, Any] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Esegue una ricerca semantica con filtri opzionali.
    
    Args:
        token: Token di autenticazione
        query: Query in linguaggio naturale
        filters: Dizionario di filtri
        limit: Numero massimo risultati
        offset: Offset per paginazione
    
    Returns:
        Dict con i risultati della ricerca
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "query": query,
        "include_content": True,
        "limit": limit,
        "offset": offset
    }
    
    if filters:
        data.update(filters)
    
    response = requests.post(
        f"{API_BASE_URL}/query/semantic-search",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Ricerca fallita: {response.json()['detail']}")
    
    return response.json()

def export_results(
    token: str,
    query_id: str,
    format: str = "pdf",
    include_stats: bool = True
) -> str:
    """
    Esporta i risultati della ricerca.
    
    Args:
        token: Token di autenticazione
        query_id: ID della query
        format: Formato export (pdf, excel, json)
        include_stats: Se includere statistiche
    
    Returns:
        Path del file esportato
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "query_id": query_id,
        "format": format,
        "include_stats": include_stats
    }
    
    response = requests.post(
        f"{API_BASE_URL}/query/export-results",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Export fallito: {response.json()['detail']}")
    
    return response.json()["export_path"]

def print_results(results: Dict[str, Any]) -> None:
    """
    Stampa i risultati della ricerca in formato leggibile.
    
    Args:
        results: Dizionario con i risultati
    """
    logger.info(f"\nTrovati {results['total']} documenti (pagina {results['page']})")
    logger.info("-" * 50)
    
    for result in results["results"]:
        doc = result["documento"]
        logger.info(f"ID: {doc['id']}")
        logger.info(f"Filename: {doc['filename']}")
        logger.info(f"Tipo: {doc['tipo_documento']}")
        logger.info(f"Score: {result['score']:.2f}")
        if doc.get("metadata"):
            logger.info("Entità principali:")
            entities = doc["metadata"].get("entities", {})
            for tipo, items in entities.items():
                if items:
                    logger.info(f"  {tipo}: {', '.join(items[:3])}...")
        logger.info("-" * 50)

def main():
    """
    Funzione principale che dimostra vari tipi di ricerca.
    """
    try:
        # 1. Login
        logger.info("Effettuo login...")
        token = get_token()
        
        # 2. Ricerca base
        logger.info("\nEseguo ricerca base...")
        results = semantic_search(
            token,
            "Trova decreti che menzionano Mario Rossi"
        )
        print_results(results)
        
        # 3. Ricerca con filtri
        logger.info("\nEseguo ricerca con filtri...")
        three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
        
        filters = {
            "tipo_documento": "DECRETO",
            "data_inizio": three_months_ago,
            "importo_minimo": 1000
        }
        
        results = semantic_search(
            token,
            "Trova documenti con importi significativi",
            filters=filters
        )
        print_results(results)
        
        # 4. Ricerca entità specifiche
        logger.info("\nEseguo ricerca per entità...")
        results = semantic_search(
            token,
            "Trova documenti che menzionano il Tribunale di Milano"
        )
        print_results(results)
        
        # 5. Export risultati
        logger.info("\nEsporto risultati...")
        export_path = export_results(
            token,
            "ricerca_esempio",
            format="pdf"
        )
        logger.info(f"Risultati esportati in: {export_path}")
        
    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        sys.exit(1)

def demo_queries():
    """
    Esempi di query utili per l'utente.
    """
    queries = [
        # Ricerche per tipo documento
        "Trova tutti i decreti del 2023",
        "Cerca le ultime sentenze del tribunale",
        "Mostra le perizie tecniche più recenti",
        
        # Ricerche per entità
        "Documenti che menzionano Mario Rossi e il Comune di Roma",
        "Atti che coinvolgono il Tribunale di Milano",
        "Decreti firmati dal giudice Bianchi",
        
        # Ricerche per importi
        "Documenti con importi superiori a 10.000€",
        "Sentenze con risarcimenti elevati",
        "Perizie con valutazioni significative",
        
        # Ricerche temporali
        "Documenti degli ultimi 3 mesi",
        "Atti del primo trimestre 2023",
        "Decreti emessi la scorsa settimana",
        
        # Ricerche combinate
        "Decreti del 2023 con importi > 5000€ relativi a appalti",
        "Sentenze recenti del tribunale di Milano su cause civili",
        "Perizie tecniche degli ultimi 6 mesi su immobili"
    ]
    
    logger.info("\nEsempi di query utili:")
    for i, query in enumerate(queries, 1):
        logger.info(f"{i}. {query}")

if __name__ == "__main__":
    main()
    demo_queries() 