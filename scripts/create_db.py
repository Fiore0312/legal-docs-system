import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connessione al database di default postgres
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Verifica se il database esiste già
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'liquidazione_db'")
        exists = cur.fetchone()
        
        if not exists:
            # Crea il database
            cur.execute('CREATE DATABASE liquidazione_db')
            print("Database 'liquidazione_db' creato con successo!")
        else:
            print("Il database 'liquidazione_db' esiste già.")
            
        cur.close()
        conn.close()
        
        # Connessione al nuovo database per creare le estensioni
        conn = psycopg2.connect(
            dbname="liquidazione_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Installa l'estensione pgvector se non esiste già
        cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        """)
        print("Estensione 'vector' installata/verificata con successo!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")

if __name__ == "__main__":
    create_database() 