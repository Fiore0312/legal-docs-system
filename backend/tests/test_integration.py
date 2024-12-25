import pytest
from fastapi import status
import asyncio
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from ..app.models.documento import Documento, DocumentType, DocumentStatus
from ..app.core.config import get_settings

settings = get_settings()

def test_complete_workflow(client, auth_headers, test_files):
    """
    Test del flusso completo: upload, elaborazione, ricerca ed export.
    """
    # 1. Upload documento
    with open(test_files["pdf"], "rb") as f:
        response = client.post(
            "/documenti/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"tipo_documento": DocumentType.DECRETO.value},
            headers=auth_headers
        )
    
    assert response.status_code == status.HTTP_201_CREATED
    doc_data = response.json()
    doc_id = doc_data["id"]
    
    # 2. Avvia elaborazione
    response = client.post(
        f"/documenti/{doc_id}/analyze",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # 3. Attendi completamento elaborazione
    max_retries = 10
    retry_delay = 1
    for _ in range(max_retries):
        response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        if response.json()["stato_elaborazione"] == DocumentStatus.COMPLETED.value:
            break
        time.sleep(retry_delay)
    
    # 4. Verifica metadati estratti
    response = client.get(f"/documenti/{doc_id}/entities", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    entities = response.json()
    assert all(key in entities for key in ["persone", "organizzazioni", "date", "importi"])
    
    # 5. Esegui ricerca semantica
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "Trova documenti simili",
            "include_content": True
        }
    )
    assert response.status_code == status.HTTP_200_OK
    search_results = response.json()
    assert doc_id in [r["documento"]["id"] for r in search_results["results"]]
    
    # 6. Genera report
    response = client.post(
        "/query/export-results",
        headers=auth_headers,
        json={
            "query_id": "test_workflow",
            "format": "pdf",
            "include_stats": True
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert Path(response.json()["export_path"]).exists()

def test_concurrent_processing(client, auth_headers, test_files):
    """
    Test elaborazione concorrente di più documenti.
    """
    # Upload multipli documenti
    doc_ids = []
    for i in range(3):
        with open(test_files["pdf"], "rb") as f:
            response = client.post(
                "/documenti/upload",
                files={"file": (f"test_{i}.pdf", f, "application/pdf")},
                data={"tipo_documento": DocumentType.DECRETO.value},
                headers=auth_headers
            )
        assert response.status_code == status.HTTP_201_CREATED
        doc_ids.append(response.json()["id"])
    
    # Avvia elaborazione batch
    response = client.post(
        "/documenti/batch-analyze",
        headers=auth_headers,
        json={"documento_ids": doc_ids}
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Monitora completamento
    max_retries = 20
    retry_delay = 1
    completed = set()
    
    for _ in range(max_retries):
        for doc_id in doc_ids:
            if doc_id in completed:
                continue
                
            response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            
            if response.json()["stato_elaborazione"] == DocumentStatus.COMPLETED.value:
                completed.add(doc_id)
                
        if len(completed) == len(doc_ids):
            break
            
        time.sleep(retry_delay)
    
    assert len(completed) == len(doc_ids), "Non tutti i documenti sono stati elaborati"

def test_error_handling(client, auth_headers, test_files, db):
    """
    Test gestione errori durante l'elaborazione.
    """
    # 1. Upload documento corrotto
    with open(test_files["pdf"], "rb") as f:
        corrupted_content = b"Invalid PDF content"
        response = client.post(
            "/documenti/upload",
            files={"file": ("corrupted.pdf", corrupted_content, "application/pdf")},
            data={"tipo_documento": DocumentType.DECRETO.value},
            headers=auth_headers
        )
    
    assert response.status_code == status.HTTP_201_CREATED
    doc_id = response.json()["id"]
    
    # 2. Avvia elaborazione
    response = client.post(
        f"/documenti/{doc_id}/analyze",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # 3. Verifica gestione errore
    max_retries = 5
    retry_delay = 1
    for _ in range(max_retries):
        response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()
        
        if status_data["stato_elaborazione"] == DocumentStatus.ERROR.value:
            assert "error" in status_data["metadata"]
            break
            
        time.sleep(retry_delay)
    
    assert status_data["stato_elaborazione"] == DocumentStatus.ERROR.value

def test_system_performance(client, auth_headers, test_files):
    """
    Test performance del sistema.
    """
    # 1. Misura tempo upload
    start_time = time.time()
    with open(test_files["pdf"], "rb") as f:
        response = client.post(
            "/documenti/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"tipo_documento": DocumentType.DECRETO.value},
            headers=auth_headers
        )
    upload_time = time.time() - start_time
    assert upload_time < 2.0  # Upload deve essere < 2 secondi
    
    doc_id = response.json()["id"]
    
    # 2. Misura tempo elaborazione
    start_time = time.time()
    response = client.post(
        f"/documenti/{doc_id}/analyze",
        headers=auth_headers
    )
    
    max_retries = 10
    retry_delay = 1
    for _ in range(max_retries):
        response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
        if response.json()["stato_elaborazione"] == DocumentStatus.COMPLETED.value:
            break
        time.sleep(retry_delay)
    
    processing_time = time.time() - start_time
    assert processing_time < 30.0  # Elaborazione deve essere < 30 secondi
    
    # 3. Misura tempo ricerca
    start_time = time.time()
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={"query": "Test query"}
    )
    search_time = time.time() - start_time
    assert search_time < 1.0  # Ricerca deve essere < 1 secondo
    
    # 4. Misura tempo export
    start_time = time.time()
    response = client.post(
        "/query/export-results",
        headers=auth_headers,
        json={
            "query_id": "test_performance",
            "format": "pdf"
        }
    )
    export_time = time.time() - start_time
    assert export_time < 5.0  # Export deve essere < 5 secondi

def test_edge_cases(client, auth_headers, test_files, db):
    """
    Test casi limite del sistema.
    """
    # 1. File molto grande
    large_content = b"x" * (10 * 1024 * 1024)  # 10MB
    response = client.post(
        "/documenti/upload",
        files={"file": ("large.pdf", large_content, "application/pdf")},
        data={"tipo_documento": DocumentType.DECRETO.value},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    # 2. Query molto lunga
    long_query = "test " * 1000
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={"query": long_query}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # 3. Molti risultati
    # Crea molti documenti di test
    for i in range(100):
        doc = Documento(
            filename=f"test_{i}.pdf",
            tipo_documento=DocumentType.DECRETO,
            contenuto="Test content",
            stato_elaborazione=DocumentStatus.COMPLETED,
            data_caricamento=datetime.now()
        )
        db.add(doc)
    db.commit()
    
    # Verifica paginazione con molti risultati
    response = client.post(
        "/query/semantic-search",
        headers=auth_headers,
        json={
            "query": "test",
            "limit": 10,
            "offset": 0
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 10
    assert data["total"] > 10
    
    # 4. Richieste concorrenti
    async def make_requests():
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                client.get(f"/documenti/{i+1}", headers=auth_headers)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)
    
    asyncio.run(make_requests())

def test_data_consistency(client, auth_headers, test_files, db):
    """
    Test consistenza dati nel sistema.
    """
    # 1. Upload e verifica documento
    with open(test_files["pdf"], "rb") as f:
        response = client.post(
            "/documenti/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"tipo_documento": DocumentType.DECRETO.value},
            headers=auth_headers
        )
    
    doc_id = response.json()["id"]
    
    # 2. Modifica diretta nel database
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    original_content = doc.contenuto
    doc.contenuto = "Modified content"
    db.commit()
    
    # 3. Verifica che le modifiche siano persistenti
    response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["contenuto"] == "Modified content"
    
    # 4. Verifica che l'elaborazione mantenga le modifiche
    response = client.post(
        f"/documenti/{doc_id}/analyze",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    max_retries = 5
    retry_delay = 1
    for _ in range(max_retries):
        response = client.get(f"/documenti/{doc_id}", headers=auth_headers)
        if response.json()["stato_elaborazione"] == DocumentStatus.COMPLETED.value:
            break
        time.sleep(retry_delay)
    
    assert response.json()["contenuto"] != original_content
    
    # 5. Verifica integrità metadati
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    assert doc.metadata is not None
    assert "entities" in doc.metadata
    assert "summary" in doc.metadata 