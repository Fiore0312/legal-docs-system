import pytest
from fastapi import status
from pathlib import Path
import json
from datetime import datetime, timedelta
from ..app.models.documento import DocumentType

def test_semantic_search(client, auth_headers, test_documents):
    """
    Test ricerca semantica base.
    """
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova tutti i decreti che menzionano Mario Rossi",
            "include_content": True,
            "limit": 10
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert len(data["results"]) > 0
    
    # Verifica che i risultati contengano decreti con Mario Rossi
    for result in data["results"]:
        doc = result["documento"]
        if doc["tipo_documento"] == DocumentType.DECRETO.value:
            assert "Mario Rossi" in doc["metadata"]["entities"]["persone"]

def test_semantic_search_with_date_filter(client, auth_headers, test_documents):
    """
    Test ricerca semantica con filtro date.
    """
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova documenti degli ultimi 30 giorni",
            "include_content": False,
            "limit": 10
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verifica che i documenti siano degli ultimi 30 giorni
    thirty_days_ago = datetime.now() - timedelta(days=30)
    for result in data["results"]:
        doc_date = datetime.fromisoformat(result["documento"]["data_caricamento"])
        assert doc_date >= thirty_days_ago

def test_semantic_search_with_type_filter(client, auth_headers, test_documents):
    """
    Test ricerca semantica con filtro tipo documento.
    """
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova tutte le sentenze",
            "include_content": False,
            "limit": 10
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verifica che i risultati siano solo sentenze
    for result in data["results"]:
        assert result["documento"]["tipo_documento"] == DocumentType.SENTENZA.value

def test_semantic_search_with_entity_filter(client, auth_headers, test_documents):
    """
    Test ricerca semantica con filtro entità.
    """
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova documenti che menzionano il Tribunale di Milano",
            "include_content": False,
            "limit": 10
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verifica che i risultati contengano l'entità cercata
    for result in data["results"]:
        entities = result["documento"]["metadata"]["entities"]
        assert "Tribunale di Milano" in entities["organizzazioni"]

def test_aggregate_results(client, auth_headers, test_documents):
    """
    Test aggregazione risultati.
    """
    response = client.post(
        "/query/aggregate",
        headers=auth_headers,
        json={
            "group_by": ["tipo_documento", "data", "entities"],
            "metrics": ["avg_score", "importi"]
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verifica struttura aggregazioni
    assert "by_type" in data
    assert "by_date" in data
    assert "by_entity" in data
    assert "metrics" in data
    
    # Verifica metriche
    metrics = data["metrics"]
    assert "avg_score" in metrics
    assert "total_amount" in metrics
    assert "avg_amount" in metrics

def test_timeline_generation(client, auth_headers, test_documents):
    """
    Test generazione timeline.
    """
    # Imposta date per il test
    start_date = datetime.now() - timedelta(days=60)
    end_date = datetime.now()
    
    response = client.get(
        "/query/timeline",
        headers=auth_headers,
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": "month"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    # Verifica struttura timeline
    for entry in data:
        assert "period" in entry
        assert "count" in entry
        assert "documents" in entry
        assert "stats" in entry
        
        # Verifica statistiche periodo
        stats = entry["stats"]
        assert "by_type" in stats
        assert "entities" in stats

def test_export_results_pdf(client, auth_headers, test_documents):
    """
    Test esportazione risultati in PDF.
    """
    response = client.post(
        "/query/export-results",
        headers=auth_headers,
        json={
            "query_id": "test_query",
            "format": "pdf",
            "include_stats": True,
            "include_content": False
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    export_path = Path(data["export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".pdf"

def test_export_results_excel(client, auth_headers, test_documents):
    """
    Test esportazione risultati in Excel.
    """
    response = client.post(
        "/query/export-results",
        headers=auth_headers,
        json={
            "query_id": "test_query",
            "format": "excel",
            "include_content": True
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    export_path = Path(data["export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".xlsx"

def test_export_results_json(client, auth_headers, test_documents):
    """
    Test esportazione risultati in JSON.
    """
    response = client.post(
        "/query/export-results",
        headers=auth_headers,
        json={
            "query_id": "test_query",
            "format": "json"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    export_path = Path(data["export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".json"
    
    # Verifica struttura JSON
    with export_path.open() as f:
        json_data = json.load(f)
        assert isinstance(json_data, list)
        for item in json_data:
            assert "id" in item
            assert "filename" in item
            assert "tipo" in item
            assert "score" in item
            assert "metadata" in item

def test_natural_language_query_parsing(client, auth_headers):
    """
    Test parsing query in linguaggio naturale.
    """
    test_queries = [
        # Query con tipo documento
        "Trova tutti i decreti del 2023",
        
        # Query con range date
        "Cerca documenti degli ultimi 6 mesi",
        
        # Query con entità
        "Trova documenti che menzionano Mario Rossi e il Comune di Roma",
        
        # Query con importi
        "Cerca documenti con importi superiori a 10.000€",
        
        # Query complessa
        "Trova le sentenze del tribunale di Milano del 2023 con importi maggiori di 5.000€"
    ]
    
    for query in test_queries:
        response = client.post(
            "/query/semantic-search",
            headers=auth_headers,
            json={"query": query}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "total" in data

def test_query_pagination(client, auth_headers, test_documents):
    """
    Test paginazione risultati ricerca.
    """
    # Prima pagina
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova tutti i documenti",
            "limit": 2,
            "offset": 0
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 2
    assert data["page"] == 1
    first_page_ids = [r["documento"]["id"] for r in data["results"]]
    
    # Seconda pagina
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova tutti i documenti",
            "limit": 2,
            "offset": 2
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["page"] == 2
    second_page_ids = [r["documento"]["id"] for r in data["results"]]
    
    # Verifica che non ci siano duplicati
    assert not set(first_page_ids).intersection(set(second_page_ids)) 