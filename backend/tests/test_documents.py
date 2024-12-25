import pytest
from fastapi import status
from pathlib import Path
import json
from ..app.models.documento import Documento, DocumentType, DocumentStatus

def test_upload_document(client, auth_headers, test_files):
    """
    Test upload documento.
    """
    # Carica PDF
    with open(test_files["pdf"], "rb") as f:
        response = client.post(
            "/documenti/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"tipo_documento": DocumentType.DECRETO.value},
            headers=auth_headers
        )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["tipo_documento"] == DocumentType.DECRETO.value
    assert data["stato_elaborazione"] == DocumentStatus.PENDING.value

def test_upload_invalid_file_type(client, auth_headers):
    """
    Test upload file non supportato.
    """
    response = client.post(
        "/documenti/upload",
        files={"file": ("test.exe", b"invalid", "application/octet-stream")},
        data={"tipo_documento": DocumentType.DECRETO.value},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Estensione file non supportata" in response.json()["detail"]

def test_get_document(client, auth_headers, test_documents):
    """
    Test recupero documento.
    """
    doc = test_documents[0]
    response = client.get(f"/documenti/{doc.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == doc.id
    assert data["filename"] == doc.filename
    assert data["tipo_documento"] == doc.tipo_documento.value
    assert data["contenuto"] == doc.contenuto

def test_get_nonexistent_document(client, auth_headers):
    """
    Test recupero documento non esistente.
    """
    response = client.get("/documenti/999", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Documento non trovato" in response.json()["detail"]

def test_analyze_document(client, auth_headers, test_documents):
    """
    Test analisi documento.
    """
    doc = test_documents[0]
    response = client.post(
        f"/documenti/{doc.id}/analyze",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert "message" in data

def test_analyze_processing_document(client, auth_headers, test_documents, db):
    """
    Test analisi documento già in elaborazione.
    """
    doc = test_documents[0]
    doc.stato_elaborazione = DocumentStatus.PROCESSING
    db.commit()
    
    response = client.post(
        f"/documenti/{doc.id}/analyze",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Documento già in elaborazione" in response.json()["detail"]

def test_get_document_entities(client, auth_headers, test_documents):
    """
    Test recupero entità documento.
    """
    doc = test_documents[0]
    response = client.get(
        f"/documenti/{doc.id}/entities",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "persone" in data
    assert "organizzazioni" in data
    assert "date" in data
    assert "importi" in data

def test_get_entities_no_metadata(client, auth_headers, test_documents, db):
    """
    Test recupero entità documento senza metadati.
    """
    doc = test_documents[0]
    doc.metadata = None
    db.commit()
    
    response = client.get(
        f"/documenti/{doc.id}/entities",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Entità non ancora estratte" in response.json()["detail"]

def test_search_documents(client, auth_headers, test_documents):
    """
    Test ricerca documenti.
    """
    response = client.post(
        "/documenti/search",
        headers=auth_headers,
        json={
            "query": "responsabile",
            "include_content": True,
            "limit": 10
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert len(data["results"]) > 0
    
    # Verifica che i risultati siano ordinati per score
    scores = [r["score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)

def test_search_with_filters(client, auth_headers, test_documents):
    """
    Test ricerca con filtri.
    """
    response = client.post(
        "/documenti/search",
        headers=auth_headers,
        json={
            "query": "tribunale",
            "tipo_documento": DocumentType.SENTENZA.value,
            "data_inizio": "2023-01-01",
            "data_fine": "2023-12-31"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) > 0
    for result in data["results"]:
        assert result["documento"]["tipo_documento"] == DocumentType.SENTENZA.value

def test_export_document(client, auth_headers, test_documents):
    """
    Test esportazione documento.
    """
    doc = test_documents[0]
    
    # Test export PDF
    response = client.post(
        f"/documenti/{doc.id}/export",
        headers=auth_headers,
        json={
            "format": "pdf",
            "include_metadata": True
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    export_path = Path(data["export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".pdf"
    
    # Test export JSON
    response = client.post(
        f"/documenti/{doc.id}/export",
        headers=auth_headers,
        json={
            "format": "json",
            "include_content": True
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    export_path = Path(data["export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".json"
    
    with export_path.open() as f:
        json_data = json.load(f)
        assert json_data["id"] == doc.id
        assert json_data["content"] == doc.contenuto

def test_batch_analyze(client, auth_headers, test_documents):
    """
    Test analisi batch documenti.
    """
    doc_ids = [doc.id for doc in test_documents[:2]]
    response = client.post(
        "/documenti/batch-analyze",
        headers=auth_headers,
        json={"documento_ids": doc_ids}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert len(data["documento_ids"]) == 2
    assert all(id in doc_ids for id in data["documento_ids"])

def test_batch_analyze_invalid_ids(client, auth_headers):
    """
    Test analisi batch con ID non validi.
    """
    response = client.post(
        "/documenti/batch-analyze",
        headers=auth_headers,
        json={"documento_ids": [999, 1000]}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Nessun documento trovato" in response.json()["detail"]

def test_document_processing(client, auth_headers, test_documents, db):
    """
    Test elaborazione completa documento.
    """
    doc = test_documents[0]
    
    # Avvia elaborazione
    response = client.post(
        f"/documenti/{doc.id}/analyze",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Verifica stato iniziale
    doc = db.query(Documento).filter(Documento.id == doc.id).first()
    assert doc.stato_elaborazione == DocumentStatus.PROCESSING
    
    # Simula completamento elaborazione
    doc.stato_elaborazione = DocumentStatus.COMPLETED
    doc.metadata = {
        "entities": {
            "persone": ["Mario Rossi"],
            "organizzazioni": ["Comune"],
            "date": ["2023-01-01"],
            "importi": ["1.000,00"]
        },
        "summary": "Documento di test"
    }
    db.commit()
    
    # Verifica risultato
    response = client.get(f"/documenti/{doc.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["stato_elaborazione"] == DocumentStatus.COMPLETED.value
    assert "entities" in data["metadata"]
    assert "summary" in data["metadata"] 