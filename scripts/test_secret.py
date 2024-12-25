import os
import sys

# Aggiungi la directory root al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import get_settings

def test_secret_key():
    try:
        settings = get_settings()
        secret_key = settings.SECRET_KEY
        print(f"✅ SECRET_KEY letta correttamente!")
        print(f"Lunghezza della chiave: {len(secret_key)} caratteri")
        print(f"La chiave è stata caricata e può essere utilizzata dall'applicazione")
    except Exception as e:
        print(f"❌ Errore nel leggere la SECRET_KEY: {str(e)}")

if __name__ == "__main__":
    test_secret_key() 