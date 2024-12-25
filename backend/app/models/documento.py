from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLAlchemyEnum, Float, ARRAY
from sqlalchemy.sql import func
import enum
from .base import Base

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class DocumentType(str, enum.Enum):
    DECRETO = "decreto"
    INGIUNZIONE = "ingiunzione"
    SENTENZA = "sentenza"
    PERIZIA = "perizia"
    ALTRO = "altro"

class Documento(Base):
    __tablename__ = "documenti"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    tipo_documento = Column(SQLAlchemyEnum(DocumentType), nullable=False)
    contenuto = Column(Text, nullable=True)  # Contenuto estratto dal documento
    embedding = Column(ARRAY(Float), nullable=True)  # Vettore embedding per ricerca semantica
    
    # Metadati e stato
    metadata = Column(JSON, nullable=True, default={})  # Metadati estratti dal documento
    stato_elaborazione = Column(SQLAlchemyEnum(DocumentStatus), default=DocumentStatus.PENDING)
    errore = Column(Text, nullable=True)  # Dettagli errore se presente
    
    # Informazioni file
    mime_type = Column(String(100), nullable=True)
    dimensione = Column(Integer, nullable=True)  # Dimensione in bytes
    hash_file = Column(String(64), nullable=True)  # SHA-256 del file
    percorso_file = Column(String(512), nullable=False)  # Percorso relativo nel filesystem
    
    # Timestamp
    data_caricamento = Column(DateTime(timezone=True), server_default=func.now())
    data_elaborazione = Column(DateTime(timezone=True), nullable=True)
    data_modifica = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Documento(id={self.id}, filename='{self.filename}', tipo='{self.tipo_documento}')>" 