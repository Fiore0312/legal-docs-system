from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import re
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseModel):
    host: str = Field(..., description="Host del database")
    port: int = Field(..., description="Porta del database")
    database: str = Field(..., description="Nome del database")
    user: str = Field(..., description="Username del database")
    password: str = Field(..., description="Password del database")
    ssl_mode: Optional[str] = Field("prefer", description="Modalità SSL")

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("La porta deve essere tra 1 e 65535")
        return v

class EmailConfig(BaseModel):
    smtp_server: str = Field(..., description="Server SMTP")
    smtp_port: int = Field(..., description="Porta SMTP")
    smtp_user: str = Field(..., description="Username SMTP")
    smtp_password: str = Field(..., description="Password SMTP")
    from_email: str = Field(..., description="Email mittente")
    use_tls: bool = Field(True, description="Usa TLS")

    @validator("smtp_port")
    def validate_smtp_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("La porta SMTP deve essere tra 1 e 65535")
        return v

    @validator("from_email")
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Formato email non valido")
        return v

class AIConfig(BaseModel):
    openai_api_key: str = Field(..., description="OpenAI API Key")
    embedding_model: str = Field("text-embedding-ada-002", description="Modello per embeddings")
    llm_model: str = Field("gpt-3.5-turbo", description="Modello LLM")
    max_tokens: int = Field(2000, description="Massimo numero di token")
    temperature: float = Field(0.0, description="Temperatura per generazione")

    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("La temperatura deve essere tra 0 e 1")
        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        if not 1 <= v <= 4096:
            raise ValueError("max_tokens deve essere tra 1 e 4096")
        return v

class VectorStoreConfig(BaseModel):
    collection_name: str = Field(..., description="Nome della collezione")
    dimension: int = Field(1536, description="Dimensione dei vettori")
    similarity_metric: str = Field("cosine", description="Metrica di similarità")
    index_type: str = Field("ivfflat", description="Tipo di indice")

    @validator("similarity_metric")
    def validate_similarity_metric(cls, v):
        valid_metrics = ["cosine", "l2", "ip"]
        if v not in valid_metrics:
            raise ValueError(f"Metrica di similarità deve essere una tra: {', '.join(valid_metrics)}")
        return v

    @validator("index_type")
    def validate_index_type(cls, v):
        valid_types = ["ivfflat", "ivfsq", "hnsw"]
        if v not in valid_types:
            raise ValueError(f"Tipo di indice deve essere uno tra: {', '.join(valid_types)}")
        return v

class APIConfig(BaseModel):
    host: str = Field("0.0.0.0", description="Host API")
    port: int = Field(8000, description="Porta API")
    debug: bool = Field(False, description="Modalità debug")
    workers: int = Field(4, description="Numero di workers")
    cors_origins: List[str] = Field(["http://localhost:3000"], description="CORS origins")
    api_prefix: str = Field("/api/v1", description="Prefisso API")

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("La porta deve essere tra 1 e 65535")
        return v

    @validator("workers")
    def validate_workers(cls, v):
        if not 1 <= v <= 32:
            raise ValueError("Il numero di workers deve essere tra 1 e 32")
        return v

class SecurityConfig(BaseModel):
    secret_key: str = Field(..., description="Chiave segreta per JWT")
    algorithm: str = Field("HS256", description="Algoritmo JWT")
    access_token_expire_minutes: int = Field(30, description="Durata token di accesso")
    refresh_token_expire_days: int = Field(7, description="Durata token di refresh")
    password_min_length: int = Field(8, description="Lunghezza minima password")
    password_require_special: bool = Field(True, description="Richiedi caratteri speciali")
    max_login_attempts: int = Field(5, description="Tentativi di login massimi")
    lockout_minutes: int = Field(15, description="Durata blocco account")

    @validator("access_token_expire_minutes")
    def validate_access_token_expire(cls, v):
        if not 5 <= v <= 60:
            raise ValueError("La durata del token di accesso deve essere tra 5 e 60 minuti")
        return v

    @validator("refresh_token_expire_days")
    def validate_refresh_token_expire(cls, v):
        if not 1 <= v <= 30:
            raise ValueError("La durata del token di refresh deve essere tra 1 e 30 giorni")
        return v

    @validator("password_min_length")
    def validate_password_min_length(cls, v):
        if not 8 <= v <= 128:
            raise ValueError("La lunghezza minima della password deve essere tra 8 e 128 caratteri")
        return v

class LoggingConfig(BaseModel):
    level: str = Field("INFO", description="Livello di logging")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Formato log"
    )
    file: Optional[str] = Field(None, description="File di log")
    rotate_size: Optional[str] = Field("10MB", description="Dimensione rotazione")
    backup_count: Optional[int] = Field(5, description="Numero backup")

    @validator("level")
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Livello di logging deve essere uno tra: {', '.join(valid_levels)}")
        return v.upper()

class SystemConfig(BaseModel):
    database: DatabaseConfig
    email: EmailConfig
    ai: AIConfig
    vector_store: VectorStoreConfig
    api: APIConfig
    security: SecurityConfig
    logging: LoggingConfig

def validate_config(config_data: Dict[str, Any]) -> None:
    """
    Valida la configurazione completa del sistema.
    """
    try:
        SystemConfig(**config_data)
        logger.info("Configurazione di sistema validata con successo")
    except Exception as e:
        logger.error(f"Errore nella validazione della configurazione: {str(e)}")
        raise

def validate_section(section: str, config_data: Dict[str, Any]) -> None:
    """
    Valida una sezione specifica della configurazione.
    """
    validators = {
        "database": DatabaseConfig,
        "email": EmailConfig,
        "ai": AIConfig,
        "vector_store": VectorStoreConfig,
        "api": APIConfig,
        "security": SecurityConfig,
        "logging": LoggingConfig
    }

    try:
        if section not in validators:
            raise ValueError(f"Sezione di configurazione non valida: {section}")
        
        validator_class = validators[section]
        validator_class(**config_data)
        logger.info(f"Sezione {section} validata con successo")
    
    except Exception as e:
        logger.error(f"Errore nella validazione della sezione {section}: {str(e)}")
        raise 