import click
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from ..core.config_validator import (
    DatabaseConfig,
    EmailConfig,
    AIConfig,
    VectorStoreConfig,
    APIConfig,
    SecurityConfig,
    LoggingConfig,
    validate_config,
    validate_section
)

logger = logging.getLogger(__name__)

def load_config(config_name: str) -> Dict[str, Any]:
    """
    Carica una configurazione da file YAML.
    """
    config_path = Path("config") / f"{config_name}.yaml"
    if not config_path.exists():
        raise click.ClickException(f"File di configurazione {config_name} non trovato")
    
    with config_path.open("r") as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any], config_name: str) -> None:
    """
    Salva una configurazione in file YAML.
    """
    config_path = Path("config") / f"{config_name}.yaml"
    with config_path.open("w") as f:
        yaml.dump(config, f, default_flow_style=False)

@click.group()
def cli():
    """Gestione configurazioni Liquidazione IA"""
    pass

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
def show(section: str):
    """Mostra una sezione di configurazione"""
    try:
        config = load_config(section)
        click.echo(yaml.dump(config, default_flow_style=False))
    except Exception as e:
        click.echo(f"Errore: {str(e)}")

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
def validate(section: str):
    """Valida una sezione di configurazione"""
    try:
        config = load_config(section)
        validate_section(section, config[section])
        click.echo(f"✓ Configurazione {section} valida")
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
@click.argument("key")
@click.argument("value")
def set(section: str, key: str, value: str):
    """Imposta un valore di configurazione"""
    try:
        # Carica configurazione esistente
        config = load_config(section)
        section_config = config[section]
        
        # Converti il valore al tipo corretto
        if isinstance(section_config.get(key), bool):
            value = value.lower() == "true"
        elif isinstance(section_config.get(key), int):
            value = int(value)
        elif isinstance(section_config.get(key), float):
            value = float(value)
        elif isinstance(section_config.get(key), list):
            value = value.split(",")
        
        # Aggiorna valore
        section_config[key] = value
        
        # Valida configurazione
        validate_section(section, section_config)
        
        # Salva configurazione
        save_config(config, section)
        click.echo(f"✓ Valore {key} aggiornato in {section}")
    
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
@click.argument("key")
def get(section: str, key: str):
    """Recupera un valore di configurazione"""
    try:
        config = load_config(section)
        value = config[section].get(key)
        if value is None:
            click.echo(f"Chiave {key} non trovata in {section}")
        else:
            click.echo(f"{key}: {value}")
    except Exception as e:
        click.echo(f"Errore: {str(e)}")

@cli.command()
def validate_all():
    """Valida tutte le configurazioni"""
    try:
        # Carica tutte le configurazioni
        config = {}
        for section in ["database", "email", "ai", "vector_store", "api", "security", "logging"]:
            try:
                section_config = load_config(section)
                config.update(section_config)
            except Exception as e:
                click.echo(f"✗ Errore nel caricamento di {section}: {str(e)}")
                return
        
        # Valida configurazione completa
        validate_config(config)
        click.echo("✓ Tutte le configurazioni sono valide")
    
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

@cli.command()
@click.argument("section", type=click.Choice([
    "database", "email", "ai", "vector_store", "api", "security", "logging"
]))
def reset(section: str):
    """Resetta una sezione di configurazione ai valori di default"""
    try:
        # Carica configurazione di default
        defaults = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "liquidazione_db",
                "user": "postgres",
                "password": "",
                "ssl_mode": "prefer"
            },
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "from_email": "",
                "use_tls": True
            },
            "ai": {
                "openai_api_key": "",
                "embedding_model": "text-embedding-ada-002",
                "llm_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.0
            },
            "vector_store": {
                "collection_name": "documenti",
                "dimension": 1536,
                "similarity_metric": "cosine",
                "index_type": "ivfflat"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "workers": 4,
                "cors_origins": ["http://localhost:3000"],
                "api_prefix": "/api/v1"
            },
            "security": {
                "secret_key": "",
                "algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
                "password_min_length": 8,
                "password_require_special": True,
                "max_login_attempts": 5,
                "lockout_minutes": 15
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log",
                "rotate_size": "10MB",
                "backup_count": 5
            }
        }
        
        if section not in defaults:
            click.echo(f"Sezione {section} non valida")
            return
        
        # Salva configurazione di default
        save_config({section: defaults[section]}, section)
        click.echo(f"✓ Configurazione {section} resettata ai valori di default")
    
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

@cli.command()
def export():
    """Esporta tutte le configurazioni"""
    try:
        # Carica tutte le configurazioni
        config = {}
        for section in ["database", "email", "ai", "vector_store", "api", "security", "logging"]:
            try:
                section_config = load_config(section)
                config.update(section_config)
            except Exception:
                continue
        
        # Salva configurazione completa
        export_path = Path("config/export.yaml")
        with export_path.open("w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        click.echo(f"✓ Configurazioni esportate in {export_path}")
    
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

@cli.command()
@click.argument("file", type=click.Path(exists=True))
def import_config(file: str):
    """Importa configurazioni da file"""
    try:
        # Carica configurazione da file
        with open(file, "r") as f:
            config = yaml.safe_load(f)
        
        # Valida configurazione
        validate_config(config)
        
        # Salva ogni sezione
        for section in ["database", "email", "ai", "vector_store", "api", "security", "logging"]:
            if section in config:
                save_config({section: config[section]}, section)
        
        click.echo("✓ Configurazioni importate con successo")
    
    except Exception as e:
        click.echo(f"✗ Errore: {str(e)}")

if __name__ == "__main__":
    cli() 