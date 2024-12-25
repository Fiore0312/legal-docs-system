import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Aggiungi la directory root al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import get_settings

def test_smtp_connection():
    settings = get_settings()
    
    print("🔍 Verifico le configurazioni email...")
    print(f"Server: {settings.MAIL_SERVER}")
    print(f"Porta: {settings.MAIL_PORT}")
    print(f"Username: {settings.MAIL_USERNAME}")
    print(f"TLS: {settings.MAIL_TLS}")
    print(f"SSL: {settings.MAIL_SSL}")
    
    try:
        print("\n📧 Provo a connettermi al server SMTP...")
        
        # Crea connessione SMTP
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        server.set_debuglevel(1)  # Abilita il debug
        
        # Avvia TLS se richiesto
        if settings.MAIL_TLS:
            print("🔒 Avvio connessione TLS...")
            server.starttls()
        
        # Login
        print("🔑 Provo ad effettuare il login...")
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        
        print("\n✅ Connessione SMTP stabilita con successo!")
        
        # Chiudi connessione
        server.quit()
        return True
        
    except Exception as e:
        print(f"\n❌ Errore durante la connessione SMTP: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp_connection() 