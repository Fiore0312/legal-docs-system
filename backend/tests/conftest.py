import pytest
from typing import Generator, Dict, Any
from pathlib import Path
import shutil
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from ..app.db.database import Base, get_db
from ..app.main import app
from ..app.models.documento import Documento, DocumentType, DocumentStatus
from ..app.models.user import User
from ..app.core.security import get_password_hash
from ..app.core.config import get_settings

settings = get_settings()

# Crea database di test
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Directory per file di test
TEST_FILES_DIR = Path(__file__).parent / "test_files"
TEST_FILES_DIR.mkdir(exist_ok=True)

# Directory per upload test
TEST_UPLOAD_DIR = Path("test_uploads")
TEST_UPLOAD_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def test_db() -> Generator:
    """
    Crea database di test e lo elimina dopo i test.
    """
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(test_db) -> Generator:
    """
    Fornisce una sessione di test pulita per ogni test.
    """
    connection = test_db.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db) -> Generator:
    """
    Fornisce un client di test con database mockato.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db) -> Dict[str, Any]:
    """
    Crea un utente di test.
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "password": "password123",
        "full_name": user.full_name
    }

@pytest.fixture(scope="function")
def test_admin(db) -> Dict[str, Any]:
    """
    Crea un utente admin di test.
    """
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {
        "id": admin.id,
        "email": admin.email,
        "password": "admin123",
        "full_name": admin.full_name
    }

@pytest.fixture(scope="function")
def auth_headers(client, test_user) -> Dict[str, str]:
    """
    Fornisce headers di autenticazione per un utente di test.
    """
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_headers(client, test_admin) -> Dict[str, str]:
    """
    Fornisce headers di autenticazione per un admin di test.
    """
    response = client.post("/auth/login", data={
        "username": test_admin["email"],
        "password": test_admin["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_documents(db) -> List[Documento]:
    """
    Crea un set di documenti di test.
    """
    docs = []
    
    # Documento 1: Decreto
    doc1 = Documento(
        filename="decreto_1.pdf",
        tipo_documento=DocumentType.DECRETO,
        contenuto="Decreto di nomina del responsabile...",
        stato_elaborazione=DocumentStatus.COMPLETED,
        metadata={
            "entities": {
                "persone": ["Mario Rossi", "Giuseppe Verdi"],
                "organizzazioni": ["Comune di Roma"],
                "date": ["2023-01-15"],
                "importi": ["1.234,56"]
            },
            "summary": "Decreto di nomina del nuovo responsabile..."
        },
        data_caricamento=datetime.now() - timedelta(days=30)
    )
    
    # Documento 2: Sentenza
    doc2 = Documento(
        filename="sentenza_123.pdf",
        tipo_documento=DocumentType.SENTENZA,
        contenuto="Il tribunale di Milano...",
        stato_elaborazione=DocumentStatus.COMPLETED,
        metadata={
            "entities": {
                "persone": ["Luca Bianchi", "Anna Verdi"],
                "organizzazioni": ["Tribunale di Milano"],
                "date": ["2023-02-20"],
                "importi": ["50.000,00"]
            },
            "summary": "Sentenza su causa civile..."
        },
        data_caricamento=datetime.now() - timedelta(days=15)
    )
    
    # Documento 3: Perizia
    doc3 = Documento(
        filename="perizia_tecnica.pdf",
        tipo_documento=DocumentType.PERIZIA,
        contenuto="Perizia tecnica relativa...",
        stato_elaborazione=DocumentStatus.COMPLETED,
        metadata={
            "entities": {
                "persone": ["Ing. Paolo Neri"],
                "organizzazioni": ["Studio Tecnico ABC"],
                "date": ["2023-03-10"],
                "importi": ["2.500,00"]
            },
            "summary": "Perizia tecnica su immobile..."
        },
        data_caricamento=datetime.now() - timedelta(days=5)
    )
    
    docs.extend([doc1, doc2, doc3])
    for doc in docs:
        db.add(doc)
    db.commit()
    
    for doc in docs:
        db.refresh(doc)
    
    return docs

@pytest.fixture(scope="function")
def test_files() -> Dict[str, Path]:
    """
    Crea file di test per upload.
    """
    files = {}
    
    # PDF di test
    pdf_content = b"%PDF-1.4\n..."  # Contenuto PDF minimo
    pdf_path = TEST_FILES_DIR / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    files["pdf"] = pdf_path
    
    # Immagine di test
    img_content = b"..."  # Contenuto immagine minimo
    img_path = TEST_FILES_DIR / "test.jpg"
    img_path.write_bytes(img_content)
    files["image"] = img_path
    
    # File di testo
    text_content = "Questo è un documento di test..."
    text_path = TEST_FILES_DIR / "test.txt"
    text_path.write_text(text_content)
    files["text"] = text_path
    
    return files

@pytest.fixture(autouse=True)
def cleanup():
    """
    Pulisce i file temporanei dopo ogni test.
    """
    yield
    
    # Elimina file di upload
    if TEST_UPLOAD_DIR.exists():
        shutil.rmtree(TEST_UPLOAD_DIR)
        TEST_UPLOAD_DIR.mkdir()
    
    # Elimina file di test
    if TEST_FILES_DIR.exists():
        shutil.rmtree(TEST_FILES_DIR)
        TEST_FILES_DIR.mkdir()

def create_test_token(user_id: int) -> str:
    """
    Helper per creare token di test.
    """
    from ..app.core.security import create_access_token
    return create_access_token({"sub": str(user_id)})

def get_test_file_path(filename: str) -> Path:
    """
    Helper per ottenere il path di un file di test.
    """
    return TEST_FILES_DIR / filename

def assert_document_metadata(doc: Documento):
    """
    Helper per verificare i metadati di un documento.
    """
    assert doc.metadata is not None
    assert "entities" in doc.metadata
    assert "summary" in doc.metadata
    
    entities = doc.metadata["entities"]
    assert all(key in entities for key in ["persone", "organizzazioni", "date", "importi"])

def assert_valid_export(export_path: Path, format: str):
    """
    Helper per verificare file di export.
    """
    assert export_path.exists()
    assert export_path.suffix == f".{format}"
    
    if format == "json":
        with export_path.open() as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0
    elif format == "xlsx":
        import pandas as pd
        df = pd.read_excel(export_path)
        assert not df.empty 