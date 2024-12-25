import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_tables():
    try:
        # Connessione al database liquidazione_db
        conn = psycopg2.connect(
            dbname="liquidazione_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Crea la tabella documents
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Tabella 'documents' creata/verificata con successo!")
        
        # Crea la tabella embeddings
        cur.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id),
            embedding FLOAT[] NOT NULL,
            text_chunk TEXT NOT NULL,
            chunk_start INTEGER,
            chunk_end INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Tabella 'embeddings' creata/verificata con successo!")
        
        # Crea la tabella users
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Tabella 'users' creata/verificata con successo!")
        
        # Crea la tabella document_access
        cur.execute("""
        CREATE TABLE IF NOT EXISTS document_access (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            document_id INTEGER REFERENCES documents(id),
            access_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, document_id)
        );
        """)
        print("Tabella 'document_access' creata/verificata con successo!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")

if __name__ == "__main__":
    create_tables() 