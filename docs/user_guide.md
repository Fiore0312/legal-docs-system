# Guida Utente

## Introduzione

Questa guida ti aiuterà a utilizzare al meglio il Sistema di Gestione Documenti Legali. Il sistema è progettato per semplificare la gestione, l'analisi e la ricerca di documenti legali.

## Casi d'Uso Comuni

### 1. Gestione Documenti

#### Upload di un Documento
1. Accedi al sistema
2. Vai alla sezione "Upload"
3. Seleziona il file (PDF, DOCX, etc.)
4. Scegli il tipo di documento
5. Clicca su "Carica"

#### Analisi Automatica
Dopo l'upload, il sistema:
1. Estrae il testo
2. Identifica entità chiave
3. Genera un sommario
4. Categorizza il documento

#### Visualizzazione e Modifica
- Apri il documento dalla dashboard
- Visualizza metadati e entità estratte
- Modifica manualmente se necessario
- Salva le modifiche

### 2. Ricerca Avanzata

#### Ricerca Semantica
Esempi di query efficaci:
- "Trova decreti del 2023 relativi a Mario Rossi"
- "Cerca sentenze con importi superiori a 10.000€"
- "Mostra perizie tecniche degli ultimi 6 mesi"

#### Filtri e Ordinamento
- Filtra per tipo documento
- Ordina per data o rilevanza
- Filtra per entità specifiche
- Combina più filtri

### 3. Analisi e Report

#### Generazione Report
1. Seleziona documenti
2. Scegli tipo di report
3. Configura parametri
4. Esporta (PDF, Excel, etc.)

#### Dashboard Analytics
- Visualizza trend temporali
- Analizza distribuzione documenti
- Monitora metriche chiave
- Esporta statistiche

## Esempi Pratici

### Esempio 1: Gestione Decreto
```python
# Upload decreto
curl -X POST http://localhost:8000/documenti/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@decreto.pdf" \
  -F "tipo_documento=DECRETO"

# Analisi automatica
curl -X POST http://localhost:8000/documenti/1/analyze \
  -H "Authorization: Bearer $TOKEN"

# Ricerca correlati
curl -X POST http://localhost:8000/query/semantic-search \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "decreti simili", "limit": 5}'
```

### Esempio 2: Report Mensile
```python
# Aggregazione dati
curl -X POST http://localhost:8000/query/aggregate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "group_by": ["tipo_documento", "data"],
    "metrics": ["count", "importi"]
  }'

# Export report
curl -X POST http://localhost:8000/query/export-results \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "format": "pdf",
    "include_stats": true
  }'
```

## Troubleshooting

### Problemi Comuni

#### 1. Upload Fallito
- **Problema**: File non caricato
- **Soluzioni**:
  - Verifica formato file supportato
  - Controlla dimensione max (10MB)
  - Assicura connessione stabile

#### 2. Analisi Non Completata
- **Problema**: Stato bloccato su "PROCESSING"
- **Soluzioni**:
  - Attendi qualche minuto
  - Verifica qualità documento
  - Riavvia analisi

#### 3. Ricerca Non Accurata
- **Problema**: Risultati non pertinenti
- **Soluzioni**:
  - Usa query più specifiche
  - Aggiungi filtri
  - Verifica indice ricerca

#### 4. Errori Autenticazione
- **Problema**: Token non valido
- **Soluzioni**:
  - Rinnova login
  - Verifica scadenza token
  - Controlla permessi

### Messaggi di Errore Comuni

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `File not supported` | Formato non valido | Usa PDF/DOCX |
| `Token expired` | Sessione scaduta | Rieffettua login |
| `Entity not found` | ID non esistente | Verifica ID |
| `Processing timeout` | Analisi troppo lunga | Riprova più tardi |

## Best Practices

### Organizzazione Documenti
1. Usa naming consistente
2. Categorizza correttamente
3. Mantieni metadati aggiornati
4. Verifica qualità OCR

### Ricerca Efficiente
1. Usa query specifiche
2. Combina filtri appropriati
3. Verifica risultati
4. Salva ricerche comuni

### Backup e Sicurezza
1. Esporta regolarmente
2. Verifica permessi
3. Monitora accessi
4. Aggiorna password

## Supporto

### Contatti
- Email: support@legaldocs.com
- Tel: +39 02 1234567
- Chat: Disponibile in-app

### Risorse
- [FAQ](faq.md)
- [Video Tutorial](tutorials/)
- [Forum Comunità](forum/)
- [Blog Tecnico](blog/) 