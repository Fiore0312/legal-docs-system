# Sistema di Gestione Documenti Legali

## Panoramica del Sistema

Questo sistema è una piattaforma avanzata per la gestione, l'analisi e la ricerca di documenti legali. Offre funzionalità di:

- Upload e gestione documenti
- Analisi automatica del contenuto
- Estrazione di entità (persone, organizzazioni, date, importi)
- Ricerca semantica avanzata
- Generazione di report e statistiche
- API RESTful completa

## Requisiti di Installazione

### Requisiti di Sistema
- Python 3.8+
- PostgreSQL 12+
- Redis (per caching e code)
- Almeno 4GB di RAM
- 10GB di spazio su disco

### Dipendenze Python
```bash
pip install -r requirements.txt
```

Principali dipendenze:
- FastAPI
- SQLAlchemy
- Pydantic
- spaCy (per NLP)
- PyTorch (per modelli ML)

## Quick Start Guide

1. Clona il repository:
```bash
git clone https://github.com/tuouser/legal-docs-system.git
cd legal-docs-system
```

2. Crea e attiva l'ambiente virtuale:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

4. Configura le variabili d'ambiente:
```bash
cp .env.example .env
# Modifica .env con i tuoi parametri
```

5. Inizializza il database:
```bash
python scripts/init_db.py
```

6. Avvia il server:
```bash
uvicorn app.main:app --reload
```

7. Accedi all'interfaccia:
- API docs: http://localhost:8000/docs
- Admin panel: http://localhost:8000/admin

## Struttura del Progetto

```
legal-docs-system/
├── app/
│   ├── api/            # Endpoints API
│   ├── core/           # Configurazioni e utilità
│   ├── db/             # Modelli e connessione database
│   ├── models/         # Modelli Pydantic
│   └── services/       # Logica di business
├── docs/              # Documentazione
├── scripts/           # Script di utilità
├── tests/            # Test automatizzati
└── examples/         # Esempi e demo
```

### Componenti Principali

- `app/api/`: Endpoints REST API
- `app/core/`: Configurazioni, sicurezza, logging
- `app/db/`: Modelli SQLAlchemy e gestione DB
- `app/models/`: Schema dati e validazione
- `app/services/`: Logica di business e elaborazione
- `scripts/`: Utility per deployment e manutenzione
- `tests/`: Suite completa di test
- `examples/`: Esempi di utilizzo e demo

## Link Utili

- [Guida Utente](user_guide.md)
- [Documentazione API](api_documentation.md)
- [Guida al Deployment](deployment.md)
- [Esempi](../examples/README.md)

## Supporto

Per supporto e segnalazione bug:
- Apri una issue su GitHub
- Contatta il team di sviluppo
- Consulta la [guida troubleshooting](user_guide.md#troubleshooting) 