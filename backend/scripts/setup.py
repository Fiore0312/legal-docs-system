import click
import os
import yaml
import secrets
import string
from pathlib import Path
from typing import Dict, Any
import logging
from ..core.config_validator import (
    DatabaseConfig,
    EmailConfig,
    AIConfig,
    VectorStoreConfig,
    APIConfig,
    SecurityConfig,
    LoggingConfig
)

logger = logging.getLogger(__name__)

def generate_secret_key(length: int = 32) -> str:
    """
    Genera una chiave segreta sicura.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_config(config: Dict[str, Any], config_name: str) -> None:
    """
    Salva una configurazione in un file YAML.
    """
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / f"{config_name}.yaml"
    with config_path.open("w") as f:
        yaml.dump(config, f, default_flow_style=False)

def update_env(key: str, value: str) -> None:
    """
    Aggiorna una variabile d'ambiente nel file .env.
    """
    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()
    
    with env_path.open("a") as f:
        f.write(f"{key}={value}\n")

@click.group()
def cli():
    """Liquidazione IA Setup Wizard"""
    pass

@cli.command()
def setup():
    """Setup guidato del sistema"""
    click.echo("Benvenuto nel wizard di setup di Liquidazione IA!")
    
    # Setup Database
    click.echo("\n=== Configurazione Database ===")
    db_config = {
        "host": click.prompt("Host del database", default="localhost"),
        "port": click.prompt("Porta del database", default=5432),
        "database": click.prompt("Nome del database", default="liquidazione_db"),
        "user": click.prompt("Username del database"),
        "password": click.prompt("Password del database", hide_input=True),
        "ssl_mode": click.prompt("Modalità SSL", default="prefer")
    }
    
    try:
        DatabaseConfig(**db_config)
        save_config({"database": db_config}, "database")
        click.echo("✓ Configurazione database salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione database: {str(e)}")
        return
    
    # Setup Email
    click.echo("\n=== Configurazione Email ===")
    email_config = {
        "smtp_server": click.prompt("Server SMTP"),
        "smtp_port": click.prompt("Porta SMTP", default=587),
        "smtp_user": click.prompt("Username SMTP"),
        "smtp_password": click.prompt("Password SMTP", hide_input=True),
        "from_email": click.prompt("Email mittente"),
        "use_tls": click.confirm("Usa TLS?", default=True)
    }
    
    try:
        EmailConfig(**email_config)
        save_config({"email": email_config}, "email")
        click.echo("✓ Configurazione email salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione email: {str(e)}")
        return
    
    # Setup AI
    click.echo("\n=== Configurazione AI ===")
    ai_config = {
        "openai_api_key": click.prompt("OpenAI API Key", hide_input=True),
        "embedding_model": click.prompt("Modello embeddings", default="text-embedding-ada-002"),
        "llm_model": click.prompt("Modello LLM", default="gpt-3.5-turbo"),
        "max_tokens": click.prompt("Massimo numero di token", default=2000),
        "temperature": click.prompt("Temperatura", default=0.0)
    }
    
    try:
        AIConfig(**ai_config)
        save_config({"ai": ai_config}, "ai")
        update_env("OPENAI_API_KEY", ai_config["openai_api_key"])
        click.echo("✓ Configurazione AI salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione AI: {str(e)}")
        return
    
    # Setup Vector Store
    click.echo("\n=== Configurazione Vector Store ===")
    vector_config = {
        "collection_name": click.prompt("Nome collezione", default="documenti"),
        "dimension": click.prompt("Dimensione vettori", default=1536),
        "similarity_metric": click.prompt(
            "Metrica similarità",
            type=click.Choice(["cosine", "l2", "ip"]),
            default="cosine"
        ),
        "index_type": click.prompt(
            "Tipo indice",
            type=click.Choice(["ivfflat", "ivfsq", "hnsw"]),
            default="ivfflat"
        )
    }
    
    try:
        VectorStoreConfig(**vector_config)
        save_config({"vector_store": vector_config}, "vector_store")
        click.echo("✓ Configurazione vector store salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione vector store: {str(e)}")
        return
    
    # Setup API
    click.echo("\n=== Configurazione API ===")
    api_config = {
        "host": click.prompt("Host API", default="0.0.0.0"),
        "port": click.prompt("Porta API", default=8000),
        "debug": click.confirm("Modalità debug?", default=False),
        "workers": click.prompt("Numero workers", default=4),
        "cors_origins": click.prompt("CORS origins (separati da virgola)", default="http://localhost:3000").split(","),
        "api_prefix": click.prompt("Prefisso API", default="/api/v1")
    }
    
    try:
        APIConfig(**api_config)
        save_config({"api": api_config}, "api")
        click.echo("✓ Configurazione API salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione API: {str(e)}")
        return
    
    # Setup Security
    click.echo("\n=== Configurazione Sicurezza ===")
    security_config = {
        "secret_key": generate_secret_key(),
        "algorithm": click.prompt("Algoritmo JWT", default="HS256"),
        "access_token_expire_minutes": click.prompt("Durata token accesso (minuti)", default=30),
        "refresh_token_expire_days": click.prompt("Durata token refresh (giorni)", default=7),
        "password_min_length": click.prompt("Lunghezza minima password", default=8),
        "password_require_special": click.confirm("Richiedi caratteri speciali?", default=True),
        "max_login_attempts": click.prompt("Tentativi login massimi", default=5),
        "lockout_minutes": click.prompt("Durata blocco account (minuti)", default=15)
    }
    
    try:
        SecurityConfig(**security_config)
        save_config({"security": security_config}, "security")
        update_env("SECRET_KEY", security_config["secret_key"])
        click.echo("✓ Configurazione sicurezza salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione sicurezza: {str(e)}")
        return
    
    # Setup Logging
    click.echo("\n=== Configurazione Logging ===")
    logging_config = {
        "level": click.prompt(
            "Livello logging",
            type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            default="INFO"
        ),
        "format": click.prompt(
            "Formato log",
            default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        "file": click.prompt("File log", default="logs/app.log"),
        "rotate_size": click.prompt("Dimensione rotazione", default="10MB"),
        "backup_count": click.prompt("Numero backup", default=5)
    }
    
    try:
        LoggingConfig(**logging_config)
        save_config({"logging": logging_config}, "logging")
        
        # Crea directory logs
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        click.echo("✓ Configurazione logging salvata")
    except Exception as e:
        click.echo(f"✗ Errore nella configurazione logging: {str(e)}")
        return
    
    click.echo("\n✓ Setup completato con successo!")
    click.echo("\nPer avviare il sistema:")
    click.echo("1. Verifica le configurazioni nei file YAML")
    click.echo("2. Avvia il database PostgreSQL")
    click.echo("3. Esegui le migrazioni con 'alembic upgrade head'")
    click.echo("4. Avvia il server con 'uvicorn main:app'")

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
def config(section: str):
    """Gestione configurazioni"""
    config_path = Path("config") / f"{section}.yaml"
    
    if not config_path.exists():
        click.echo(f"Configurazione {section} non trovata")
        return
    
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
        click.echo(yaml.dump(config, default_flow_style=False))

if __name__ == "__main__":
    cli() 