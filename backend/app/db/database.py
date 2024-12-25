from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ..core.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

try:
    logger.debug("Inizializzazione connessione al database...")
    engine = create_engine(settings.DATABASE_URL)
    logger.info("Engine del database creato con successo")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.debug("Session factory creata")
    
    Base = declarative_base()
    logger.debug("Base declarative creata")
except Exception as e:
    logger.error(f"Errore durante l'inizializzazione del database: {str(e)}", exc_info=True)
    raise

def get_db():
    db = SessionLocal()
    try:
        logger.debug("Nuova sessione database creata")
        yield db
    except Exception as e:
        logger.error(f"Errore durante l'utilizzo della sessione database: {str(e)}", exc_info=True)
        raise
    finally:
        logger.debug("Chiusura sessione database")
        db.close()

def init_db():
    try:
        logger.info("Inizializzazione schema database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Schema database inizializzato con successo")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione dello schema database: {str(e)}", exc_info=True)
        raise 