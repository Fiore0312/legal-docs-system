# Liquidazione IA

Sistema intelligente per la gestione e l'analisi di documenti di liquidazione giudiziale.

## Prerequisiti

### Software Richiesto
- Python 3.9+
- PostgreSQL 15+ con estensione pgvector
- Redis (opzionale, per caching)
- Tesseract OCR
- Node.js 18+ (per frontend)

### Requisiti Hardware
- CPU: 4+ core
- RAM: 8+ GB
- Storage: 50+ GB SSD

### Dipendenze Python
```bash
# Installa dipendenze principali
pip install -r requirements.txt

# Dipendenze opzionali per sviluppo
pip install -r requirements-dev.txt
```

### Configurazione Database
```sql
-- Crea database
CREATE DATABASE liquidazione_db;

-- Abilita estensione pgvector
CREATE EXTENSION vector;

-- Crea utente (opzionale)
CREATE USER liquidazione WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE liquidazione_db TO liquidazione;
```

## Installazione

### 1. Setup Ambiente

```bash
# Clona repository
git clone https://github.com/tuouser/liquidazione-ia.git
cd liquidazione-ia

# Crea ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configurazione Ambiente

```bash
# Copia file esempio
cp .env.example .env

# Configura variabili ambiente
nano .env
```

Variabili richieste in `.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/liquidazione_db

# Sicurezza
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=your-api-key

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@example.com

# Storage
STORAGE_TYPE=local
STORAGE_PATH=./storage
```

### 3. Setup Database

```bash
# Inizializza migrazioni
alembic upgrade head

# Verifica migrazioni
alembic current
```

### 4. Configurazione Sistema

```bash
# Esegui wizard setup
python scripts/setup.py setup

# Verifica configurazioni
python scripts/config_manager.py validate_all
```

## Avvio Sistema

### Backend

```bash
# Sviluppo
uvicorn main:app --reload

# Produzione
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (opzionale)

```bash
# Sviluppo
cd frontend
npm install
npm run dev

# Produzione
npm run build
npm start
```

## Utilizzo

### 1. Gestione Documenti

#### Caricamento
```python
# Esempio API
import requests

files = {
    'file': open('documento.pdf', 'rb')
}
data = {
    'metadata': {
        'tipo': 'fattura',
        'descrizione': 'Fattura fornitore X'
    }
}
response = requests.post('http://localhost:8000/api/v1/documenti', 
                        files=files, 
                        json=data)
```

#### Ricerca
```python
# Ricerca semantica
response = requests.get(
    'http://localhost:8000/api/v1/ai/search',
    params={
        'query': 'contratti di affitto 2023',
        'limit': 10,
        'threshold': 0.7
    }
)
```

### 2. Analisi IA

#### Analisi Documento
```python
# Avvia analisi
response = requests.post(
    f'http://localhost:8000/api/v1/ai/{documento_id}/analyze',
    json={
        'options': {
            'extract_entities': True,
            'generate_summary': True,
            'classify': True
        }
    }
)
```

#### Estrazione Entità
```python
# Estrai entità
response = requests.post(
    f'http://localhost:8000/api/v1/ai/{documento_id}/extract-entities'
)
```

### 3. Gestione Configurazioni

```bash
# Mostra configurazione
python scripts/config_manager.py show api

# Imposta valore
python scripts/config_manager.py set api rate_limit.max_requests 200

# Esporta configurazioni
python scripts/config_manager.py export
```

## Verifica Sistema

### 1. Test Funzionalità

```bash
# Esegui tutti i test
pytest

# Test specifici
pytest tests/test_auth.py
pytest tests/test_ai.py
```

### 2. Verifica Servizi

```bash
# Status servizi
python scripts/status.py

# Verifica API
curl http://localhost:8000/health

# Test OCR
python scripts/test_ocr.py
```

### 3. Monitoraggio

```bash
# Logs
tail -f logs/api.log

# Metriche
python scripts/metrics.py
```

## Limitazioni Note

1. **OCR**
   - Supporto limitato per documenti manoscritti
   - Richiede DPI minimo 300 per risultati ottimali
   - Performance ridotta su immagini di bassa qualità

2. **Analisi IA**
   - Limite token per documento (4000)
   - Tempi elaborazione variabili
   - Richiede connessione internet per API OpenAI

3. **Performance**
   - Elaborazione batch limitata a 10 documenti
   - Cache Redis necessaria per alte prestazioni
   - Limite dimensione file 50MB

## Prossimi Sviluppi

1. **Funzionalità**
   - [ ] Supporto per documenti manoscritti
   - [ ] Analisi batch migliorata
   - [ ] Interfaccia mobile

2. **Performance**
   - [ ] Ottimizzazione cache
   - [ ] Elaborazione asincrona
   - [ ] Compressione documenti

3. **Sicurezza**
   - [ ] 2FA
   - [ ] Audit log
   - [ ] Crittografia end-to-end

## Supporto

### Documentazione
- [Guida Utente](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Setup Guide](docs/setup_guide.md)

### Contatti
- Issue Tracker: GitHub Issues
- Email: support@example.com
- Chat: Discord

## License

MIT License - vedi [LICENSE](LICENSE) per dettagli. 