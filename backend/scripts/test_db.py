import os
import sys
from pathlib import Path

# Aggiungi la directory root del progetto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.config import get_settings
from sqlalchemy import create_engine, text

def test_database_connection():
    settings = get_settings()
    try:
        # Crea la connessione
        engine = create_engine(settings.DATABASE_URL)
        
        # Testa la connessione
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Connessione al database riuscita!")
            
            # Verifica le tabelle esistenti
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print("\nTabelle esistenti:")
            for table in tables:
                print(f"- {table}")
            
    except Exception as e:
        print("❌ Errore di connessione al database:")
        print(str(e))

if __name__ == "__main__":
    test_database_connection() 