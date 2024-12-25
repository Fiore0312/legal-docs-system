import os
import sys
from pathlib import Path

# Aggiungo il percorso della directory backend al PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.config import get_settings

def test_database():
    """Testa la connessione al database"""
    try:
        import psycopg2
        settings = get_settings()
        conn = psycopg2.connect(settings.DATABASE_URL)
        print("✅ Database connesso correttamente!")
        conn.close()
    except Exception as e:
        print(f"❌ Errore connessione database: {str(e)}")

def test_email():
    """Testa la configurazione email"""
    try:
        settings = get_settings()
        required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]
        missing = [field for field in required if not getattr(settings, field)]
        if missing:
            print(f"❌ Configurazione email incompleta. Campi mancanti: {', '.join(missing)}")
        else:
            print("✅ Configurazione email corretta!")
    except Exception as e:
        print(f"❌ Errore configurazione email: {str(e)}")

def test_openai():
    """Testa la configurazione OpenAI"""
    try:
        settings = get_settings()
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key":
            print("❌ API Key OpenAI non configurata")
        else:
            print("✅ Configurazione OpenAI corretta!")
    except Exception as e:
        print(f"❌ Errore configurazione OpenAI: {str(e)}")

def main():
    print("\n🔍 Inizio test configurazioni...\n")
    
    # Test Database
    print("Testing Database...")
    test_database()
    print()
    
    # Test Email
    print("Testing Email...")
    test_email()
    print()
    
    # Test OpenAI
    print("Testing OpenAI...")
    test_openai()
    print()

if __name__ == "__main__":
    main() 