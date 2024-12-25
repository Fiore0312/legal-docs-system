# Agent Instructions

## Introduzione

Questo documento descrive le funzionalità e le istruzioni operative per l'agente AI del sistema Liquidazione IA. L'agente è progettato per assistere nella gestione e nell'analisi di documenti di liquidazione giudiziale.

## Capabilities

### 1. Elaborazione Documenti
- Lettura e OCR di documenti PDF e immagini
- Estrazione strutturata del testo
- Classificazione automatica dei documenti
- Identificazione di sezioni chiave

### 2. Analisi Semantica
- Generazione embeddings per documenti
- Ricerca semantica nel corpus documentale
- Clustering di documenti simili
- Identificazione di relazioni tra documenti

### 3. Estrazione Informazioni
- Identificazione di entità (date, importi, nomi)
- Estrazione di informazioni strutturate
- Validazione di dati estratti
- Normalizzazione di formati

### 4. Generazione Contenuti
- Creazione di riassunti
- Generazione di report
- Risposte a domande sui documenti
- Traduzione di contenuti

### 5. Gestione Configurazioni
- Lettura configurazioni YAML
- Validazione configurazioni
- Aggiornamento configurazioni
- Backup configurazioni

### 6. Gestione Documentazione
- Aggiornamento automatico docs
- Versioning della documentazione
- Parsing di Markdown
- Generazione docs da codice

## Comandi

### Elaborazione Documenti

#### analyze_document
Analizza un documento e ne estrae informazioni strutturate.

```python
result = await agent.analyze_document(
    document_id=123,
    options={
        "extract_entities": True,
        "generate_summary": True,
        "classify": True
    }
)
```

#### search_documents
Esegue una ricerca semantica nei documenti.

```python
results = await agent.search_documents(
    query="contratti di affitto 2023",
    limit=10,
    threshold=0.7
)
```

### Gestione Configurazioni

#### read_config
Legge una sezione di configurazione.

```python
config = await agent.read_config("api")
```

#### update_config
Aggiorna una configurazione.

```python
await agent.update_config(
    section="api",
    updates={
        "rate_limit.max_requests": 200
    }
)
```

### Gestione Documentazione

#### update_docs
Aggiorna la documentazione.

```python
await agent.update_docs(
    doc_type="api_reference",
    content="# API Reference\n..."
)
```

#### generate_docs
Genera documentazione da codice.

```python
await agent.generate_docs(
    source_file="main.py",
    output="api_docs.md"
)
```

## Workflow

### 1. Elaborazione Documento
1. Ricevi documento
2. Estrai testo (OCR se necessario)
3. Classifica documento
4. Estrai entità
5. Genera embedding
6. Salva risultati

### 2. Ricerca Semantica
1. Ricevi query
2. Genera embedding query
3. Cerca documenti simili
4. Filtra risultati
5. Ordina per rilevanza

### 3. Aggiornamento Configurazioni
1. Leggi configurazione attuale
2. Valida modifiche
3. Crea backup
4. Applica modifiche
5. Verifica risultato

### 4. Gestione Documentazione
1. Leggi contenuto attuale
2. Genera nuovo contenuto
3. Valida formato
4. Crea versione
5. Aggiorna file

## Best Practices

### Elaborazione
1. Verifica formato documento
2. Usa cache quando possibile
3. Gestisci errori OCR
4. Valida risultati
5. Logga operazioni importanti

### Configurazioni
1. Backup prima di modifiche
2. Valida sempre gli input
3. Usa variabili ambiente per dati sensibili
4. Mantieni versioning
5. Documenta cambiamenti

### Documentazione
1. Segui standard Markdown
2. Includi esempi
3. Versiona i documenti
4. Valida link
5. Aggiorna indici

## Errori Comuni

### Elaborazione
- File non supportato
- OCR fallito
- Timeout elaborazione
- Memoria insufficiente
- API non disponibile

### Configurazioni
- Schema non valido
- Chiave non trovata
- Tipo non corretto
- Permessi insufficienti
- File bloccato

### Documentazione
- Formato non valido
- Link spezzati
- Conflitti versione
- Spazio insufficiente
- Encoding errato

## Logging

### Livelli
- DEBUG: Dettagli debug
- INFO: Operazioni normali
- WARNING: Problemi non critici
- ERROR: Errori operativi
- CRITICAL: Errori bloccanti

### Formato
```
timestamp - level - component - message
```

### Esempi
```python
logger.info("Documento elaborato", extra={"doc_id": 123})
logger.error("OCR fallito", exc_info=True)
```

## Sicurezza

### Dati Sensibili
1. Mai loggare dati sensibili
2. Usa variabili ambiente
3. Cripta in storage
4. Limita accesso
5. Ruota credenziali

### Validazione
1. Valida input
2. Sanitizza output
3. Limita dimensioni
4. Verifica permessi
5. Traccia accessi

## Manutenzione

### Cache
1. Pulisci cache scaduta
2. Monitora dimensione
3. Verifica hit rate
4. Ottimizza TTL
5. Backup se necessario

### Performance
1. Monitora tempi risposta
2. Ottimizza query
3. Gestisci memoria
4. Scala risorse
5. Profila codice 