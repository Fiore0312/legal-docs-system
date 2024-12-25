import sys
import os
from datetime import datetime, timedelta
import random
from pathlib import Path
import logging
import bcrypt
import psycopg2
from psycopg2.extras import execute_values

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dati di esempio
TEST_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "status": "active",
        "is_active": True,
        "email_verified": True
    },
    {
        "email": "user@example.com",
        "password": "user123",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "status": "active",
        "is_active": True,
        "email_verified": True
    },
    {
        "email": "pending@example.com",
        "password": "pending123",
        "first_name": "Pending",
        "last_name": "User",
        "role": "user",
        "status": "pending",
        "is_active": False,
        "email_verified": False
    }
]

TEST_DOCUMENTS = [
    {
        "title": "Documento di Liquidazione 1",
        "content": "Contenuto del documento di liquidazione 1...",
        "document_type": "liquidazione",
        "status": "pending",
        "metadata": {"anno": 2023, "numero": 1}
    },
    {
        "title": "Documento di Liquidazione 2",
        "content": "Contenuto del documento di liquidazione 2...",
        "document_type": "liquidazione",
        "status": "approved",
        "metadata": {"anno": 2023, "numero": 2}
    },
    {
        "title": "Documento di Test",
        "content": "Contenuto del documento di test...",
        "document_type": "test",
        "status": "draft",
        "metadata": {"anno": 2023, "numero": 3}
    }
]

def hash_password(password: str) -> str:
    """
    Genera l'hash della password usando bcrypt.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def insert_test_users(conn):
    """
    Inserisce gli utenti di test nel database.
    """
    try:
        cur = conn.cursor()
        
        # Prepara i dati degli utenti
        users_data = []
        for user in TEST_USERS:
            users_data.append((
                user["email"],
                hash_password(user["password"]),
                user["first_name"],
                user["last_name"],
                user["role"],
                user["status"],
                user["is_active"],
                user["email_verified"],
                datetime.now(),
                datetime.now()
            ))
        
        # Query di inserimento
        insert_query = """
        INSERT INTO users (
            email, hashed_password, first_name, last_name, 
            role, status, is_active, email_verified,
            created_at, updated_at
        ) VALUES %s
        ON CONFLICT (email) DO NOTHING
        RETURNING id;
        """
        
        execute_values(cur, insert_query, users_data)
        conn.commit()
        logger.info(f"Inseriti {len(users_data)} utenti di test")
        
    except Exception as e:
        logger.error(f"Errore durante l'inserimento degli utenti: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()

def insert_test_documents(conn):
    """
    Inserisce i documenti di test nel database.
    """
    try:
        cur = conn.cursor()
        
        # Ottiene l'ID dell'utente admin
        cur.execute("SELECT id FROM users WHERE email = 'admin@example.com'")
        admin_id = cur.fetchone()[0]
        
        # Prepara i dati dei documenti
        docs_data = []
        for doc in TEST_DOCUMENTS:
            docs_data.append((
                doc["title"],
                doc["content"],
                doc["document_type"],
                doc["status"],
                doc["metadata"],
                admin_id,
                datetime.now(),
                datetime.now()
            ))
        
        # Query di inserimento
        insert_query = """
        INSERT INTO documents (
            title, content, document_type, status,
            metadata, created_by_id, created_at, updated_at
        ) VALUES %s
        RETURNING id;
        """
        
        execute_values(cur, insert_query, docs_data)
        conn.commit()
        logger.info(f"Inseriti {len(docs_data)} documenti di test")
        
    except Exception as e:
        logger.error(f"Errore durante l'inserimento dei documenti: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()

def main():
    """
    Funzione principale per generare i dati di test.
    """
    try:
        # Connessione al database
        conn = psycopg2.connect(
            dbname="liquidazione_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        
        # Inserisce i dati di test
        insert_test_users(conn)
        insert_test_documents(conn)
        
        logger.info("Generazione dati di test completata con successo!")
        
    except Exception as e:
        logger.error(f"Errore durante la generazione dei dati di test: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main() 