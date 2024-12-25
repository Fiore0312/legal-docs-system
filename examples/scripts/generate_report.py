#!/usr/bin/env python3
"""
Script di esempio per la generazione di report e statistiche.
Dimostra come:
1. Aggregare dati
2. Generare statistiche
3. Creare visualizzazioni
4. Esportare report
"""

import os
import sys
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any
import logging
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

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
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

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

def get_aggregations(token: str) -> Dict[str, Any]:
    """
    Recupera aggregazioni sui documenti.
    
    Args:
        token: Token di autenticazione
    
    Returns:
        Dict con dati aggregati
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "group_by": ["tipo_documento", "data"],
        "metrics": ["count", "importi"]
    }
    
    response = requests.post(
        f"{API_BASE_URL}/query/aggregate",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Aggregazione fallita: {response.json()['detail']}")
    
    return response.json()

def get_timeline(
    token: str,
    start_date: str = None,
    end_date: str = None
) -> List[Dict[str, Any]]:
    """
    Recupera timeline documenti.
    
    Args:
        token: Token di autenticazione
        start_date: Data inizio (ISO format)
        end_date: Data fine (ISO format)
    
    Returns:
        Lista di dati timeline
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "group_by": "month"
    }
    
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    response = requests.get(
        f"{API_BASE_URL}/query/timeline",
        headers=headers,
        params=params
    )
    
    if response.status_code != 200:
        raise Exception(f"Timeline fallita: {response.json()['detail']}")
    
    return response.json()

def export_report(
    token: str,
    query_id: str,
    format: str = "pdf"
) -> str:
    """
    Esporta report in vari formati.
    
    Args:
        token: Token di autenticazione
        query_id: ID query
        format: Formato export
    
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
        "include_stats": True
    }
    
    response = requests.post(
        f"{API_BASE_URL}/query/export-results",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Export fallito: {response.json()['detail']}")
    
    return response.json()["export_path"]

def create_visualizations(
    aggregations: Dict[str, Any],
    timeline: List[Dict[str, Any]]
) -> None:
    """
    Crea visualizzazioni dei dati.
    
    Args:
        aggregations: Dati aggregati
        timeline: Dati timeline
    """
    # 1. Distribuzione per tipo documento
    plt.figure(figsize=(10, 6))
    types = aggregations["by_type"]
    plt.bar(types.keys(), types.values())
    plt.title("Distribuzione Documenti per Tipo")
    plt.xlabel("Tipo Documento")
    plt.ylabel("Numero Documenti")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "distribuzione_tipi.png")
    plt.close()
    
    # 2. Timeline documenti
    plt.figure(figsize=(12, 6))
    dates = [entry["period"] for entry in timeline]
    counts = [entry["count"] for entry in timeline]
    plt.plot(dates, counts, marker='o')
    plt.title("Timeline Documenti")
    plt.xlabel("Periodo")
    plt.ylabel("Numero Documenti")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "timeline.png")
    plt.close()
    
    # 3. Importi medi per tipo
    plt.figure(figsize=(10, 6))
    metrics = aggregations["metrics"]
    avg_amounts = {
        tipo: sum(importi)/len(importi) if importi else 0
        for tipo, importi in metrics["importi_by_type"].items()
    }
    plt.bar(avg_amounts.keys(), avg_amounts.values())
    plt.title("Importo Medio per Tipo Documento")
    plt.xlabel("Tipo Documento")
    plt.ylabel("Importo Medio (€)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "importi_medi.png")
    plt.close()

def generate_excel_report(
    aggregations: Dict[str, Any],
    timeline: List[Dict[str, Any]]
) -> None:
    """
    Genera report Excel dettagliato.
    
    Args:
        aggregations: Dati aggregati
        timeline: Dati timeline
    """
    # Crea Excel writer
    writer = pd.ExcelWriter(
        REPORT_DIR / "report_dettagliato.xlsx",
        engine='xlsxwriter'
    )
    
    # 1. Foglio distribuzione tipi
    df_types = pd.DataFrame.from_dict(
        aggregations["by_type"],
        orient='index',
        columns=['count']
    )
    df_types.to_excel(writer, sheet_name='Distribuzione Tipi')
    
    # 2. Foglio timeline
    df_timeline = pd.DataFrame(timeline)
    df_timeline.to_excel(writer, sheet_name='Timeline')
    
    # 3. Foglio metriche
    metrics = aggregations["metrics"]
    df_metrics = pd.DataFrame({
        'Metrica': [
            'Score Medio',
            'Importo Totale',
            'Importo Medio'
        ],
        'Valore': [
            metrics['avg_score'],
            metrics['total_amount'],
            metrics['avg_amount']
        ]
    })
    df_metrics.to_excel(writer, sheet_name='Metriche')
    
    # 4. Foglio entità più frequenti
    entities = {}
    for doc in timeline:
        for entity_type, items in doc["stats"]["entities"].items():
            if entity_type not in entities:
                entities[entity_type] = {}
            for item in items:
                entities[entity_type][item] = entities[entity_type].get(item, 0) + 1
    
    for entity_type, counts in entities.items():
        df_entities = pd.DataFrame.from_dict(
            counts,
            orient='index',
            columns=['count']
        ).sort_values('count', ascending=False).head(10)
        df_entities.to_excel(writer, sheet_name=f'Top {entity_type}')
    
    writer.close()

def generate_summary(
    aggregations: Dict[str, Any],
    timeline: List[Dict[str, Any]]
) -> str:
    """
    Genera sommario testuale dei dati.
    
    Args:
        aggregations: Dati aggregati
        timeline: Dati timeline
    
    Returns:
        Stringa con sommario
    """
    metrics = aggregations["metrics"]
    types = aggregations["by_type"]
    
    summary = [
        "# Report Analisi Documenti",
        "",
        "## Statistiche Generali",
        f"- Totale documenti: {sum(types.values())}",
        f"- Score medio: {metrics['avg_score']:.2f}",
        f"- Importo totale: €{metrics['total_amount']:,.2f}",
        f"- Importo medio: €{metrics['avg_amount']:,.2f}",
        "",
        "## Distribuzione per Tipo",
    ]
    
    for tipo, count in types.items():
        summary.append(f"- {tipo}: {count} documenti")
    
    summary.extend([
        "",
        "## Trend Temporale",
        f"- Periodo analizzato: {timeline[0]['period']} - {timeline[-1]['period']}",
        f"- Picco documenti: {max(entry['count'] for entry in timeline)} "
        f"({max(timeline, key=lambda x: x['count'])['period']})",
        "",
        "## Entità più Frequenti"
    ])
    
    # Aggrega entità da timeline
    entities = {}
    for entry in timeline:
        for entity_type, items in entry["stats"]["entities"].items():
            if entity_type not in entities:
                entities[entity_type] = {}
            for item in items:
                entities[entity_type][item] = entities[entity_type].get(item, 0) + 1
    
    for entity_type, counts in entities.items():
        top_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        summary.append(f"\n### {entity_type.title()}")
        for item, count in top_items:
            summary.append(f"- {item}: {count} occorrenze")
    
    return "\n".join(summary)

def main():
    """
    Funzione principale che genera report completo.
    """
    try:
        # 1. Login
        logger.info("Effettuo login...")
        token = get_token()
        
        # 2. Recupera dati
        logger.info("Recupero aggregazioni...")
        aggregations = get_aggregations(token)
        
        logger.info("Recupero timeline...")
        three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
        timeline = get_timeline(token, start_date=three_months_ago)
        
        # 3. Genera visualizzazioni
        logger.info("Genero visualizzazioni...")
        create_visualizations(aggregations, timeline)
        
        # 4. Genera report Excel
        logger.info("Genero report Excel...")
        generate_excel_report(aggregations, timeline)
        
        # 5. Genera sommario
        logger.info("Genero sommario...")
        summary = generate_summary(aggregations, timeline)
        
        # 6. Salva sommario
        summary_path = REPORT_DIR / "report_summary.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        # 7. Esporta report PDF
        logger.info("Esporto report PDF...")
        pdf_path = export_report(token, "report_completo", "pdf")
        
        logger.info("\nReport generati:")
        logger.info(f"- Visualizzazioni: {REPORT_DIR}")
        logger.info(f"- Report Excel: {REPORT_DIR/'report_dettagliato.xlsx'}")
        logger.info(f"- Sommario: {summary_path}")
        logger.info(f"- Report PDF: {pdf_path}")
        
    except Exception as e:
        logger.error(f"Errore: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 