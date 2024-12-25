import os
import sys
from pathlib import Path

# Aggiungi il percorso della directory backend al PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from app.core.config import get_settings
from app.models.base import Base
from app.models.user import User
from app.models.documento import Documento

settings = get_settings()

def create_database():
    """Crea il database se non esiste."""
    # Estrai il nome del database dall'URL
    db_name = settings.DATABASE_URL.split('/')[-1]
    # Crea un URL per connettersi al database di sistema postgres
    system_db_url = settings.DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
    
    # Connettiti al database di sistema
    engine = create_engine(system_db_url)
    
    try:
        # Verifica se il database esiste
        with engine.connect() as conn:
            conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
            
            if not result:
                # Il database non esiste, crealo
                # Chiudi tutte le connessioni al database
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                    AND pid <> pg_backend_pid()
                """))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database {db_name} creato con successo!")
            else:
                print(f"Il database {db_name} esiste già.")
                
    except Exception as e:
        print(f"Errore durante la creazione del database: {str(e)}")
        raise

def create_tables():
    """Crea tutte le tabelle nel database."""
    try:
        # Crea un engine per il database specifico
        engine = create_engine(settings.DATABASE_URL)
        
        # Crea tutte le tabelle
        Base.metadata.create_all(bind=engine)
        print("Tabelle create con successo!")
        
    except Exception as e:
        print(f"Errore durante la creazione delle tabelle: {str(e)}")
        raise

def main():
    """Funzione principale per l'inizializzazione del database."""
    try:
        print("Inizializzazione del database...")
        create_database()
        create_tables()
        print("Inizializzazione del database completata con successo!")
    except Exception as e:
        print(f"Errore durante l'inizializzazione del database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 