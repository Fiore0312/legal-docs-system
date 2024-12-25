# Setup Guide

## Requisiti di Sistema

### Software
- Python 3.9+
- PostgreSQL 15+ con estensione pgvector
- Redis (opzionale, per caching)
- Tesseract OCR
- Node.js 18+ (per frontend)

### Hardware Raccomandato
- CPU: 4+ core
- RAM: 8+ GB
- Storage: 50+ GB SSD

## Installazione

### 1. Preparazione Ambiente

```bash
# Crea e attiva ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Crea database PostgreSQL
createdb liquidazione_db

# Abilita estensione pgvector
psql liquidazione_db
CREATE EXTENSION vector;
```

### 3. Configurazione

```bash
# Copia file di esempio
cp .env.example .env

# Esegui wizard di setup
python scripts/setup.py setup
```

Configura le seguenti variabili in `.env`:
- `DATABASE_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `SMTP_*` (per email)

### 4. Migrazioni Database

```bash
# Inizializza migrazioni
alembic upgrade head
```

### 5. Setup Frontend (opzionale)

```bash
# Installa dipendenze frontend
cd frontend
npm install

# Copia configurazione
cp .env.example .env
```

## Configurazione

### File di Configurazione

Il sistema utilizza diversi file YAML per la configurazione:

- `config/agent_config.yaml`: Configurazioni agente AI
- `config/api_config.yaml`: Configurazioni API
- `config/services_config.yaml`: Configurazioni servizi
- `config/prompts_config.yaml`: Template prompt AI

### Gestione Configurazioni

Usa il CLI per gestire le configurazioni:

```bash
# Mostra configurazione
python scripts/config_manager.py show <section>

# Valida configurazione
python scripts/config_manager.py validate <section>

# Imposta valore
python scripts/config_manager.py set <section> <key> <value>
```

## Avvio

### Backend

```bash
# Avvio server di sviluppo
uvicorn main:app --reload

# Avvio produzione
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (opzionale)

```bash
# Avvio sviluppo
npm run dev

# Build produzione
npm run build
npm start
```

## Verifica Installazione

1. Verifica API: http://localhost:8000/docs
2. Verifica Frontend: http://localhost:3000
3. Verifica Health: http://localhost:8000/health

## Troubleshooting

### Database
- Verifica connessione: `psql -U <user> -d liquidazione_db`
- Verifica estensione: `\dx` in psql

### API
- Controlla logs: `logs/api.log`
- Verifica configurazioni: `python scripts/config_manager.py validate_all`

### AI
- Verifica API key: `python scripts/config_manager.py get ai openai_api_key`
- Test OCR: `python scripts/test_ocr.py`

## Sicurezza

### Best Practices
1. Usa password complesse
2. Mantieni aggiornate le dipendenze
3. Configura CORS appropriatamente
4. Abilita HTTPS in produzione
5. Ruota regolarmente i token

### Backup
1. Database: `pg_dump liquidazione_db > backup.sql`
2. Configurazioni: `python scripts/config_manager.py export`
3. Documenti: backup directory `storage/`

## Manutenzione

### Routine
1. Verifica logs giornalmente
2. Monitora uso risorse
3. Pulisci cache periodicamente
4. Aggiorna dipendenze mensilmente
5. Backup settimanali

### Aggiornamenti
1. Backup dati
2. `git pull`
3. `pip install -r requirements.txt`
4. `alembic upgrade head`
5. Riavvia servizi

## Supporto

### Risorse
- Documentazione: `/docs`
- Issue Tracker: GitHub
- Email: support@example.com

### Comandi Utili
```bash
# Status servizi
python scripts/status.py

# Pulizia cache
python scripts/cleanup.py

# Test sistema
pytest

# Logs
tail -f logs/api.log
``` 