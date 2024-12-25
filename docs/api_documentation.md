# Documentazione API

## Autenticazione

Il sistema utilizza autenticazione JWT (JSON Web Token). Per accedere alle API protette:

1. Ottieni un token tramite login:
```bash
POST /auth/login
{
    "username": "user@example.com",
    "password": "password123"
}
```

2. Usa il token nelle richieste successive:
```bash
Authorization: Bearer <token>
```

## Endpoints

### Autenticazione

#### POST /auth/register
Registra un nuovo utente.

Request:
```json
{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Mario Rossi"
}
```

Response:
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "Mario Rossi",
    "is_active": true
}
```

#### POST /auth/login
Effettua il login.

Request:
```json
{
    "username": "user@example.com",
    "password": "password123"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer"
}
```

### Gestione Documenti

#### POST /documenti/upload
Carica un nuovo documento.

Request:
- Multipart form data:
  - file: File binario
  - tipo_documento: Enum (DECRETO, SENTENZA, PERIZIA)

Response:
```json
{
    "id": 1,
    "filename": "documento.pdf",
    "tipo_documento": "DECRETO",
    "stato_elaborazione": "PENDING"
}
```

#### GET /documenti/{id}
Recupera un documento specifico.

Response:
```json
{
    "id": 1,
    "filename": "documento.pdf",
    "tipo_documento": "DECRETO",
    "contenuto": "...",
    "metadata": {
        "entities": {
            "persone": ["Mario Rossi"],
            "organizzazioni": ["Tribunale Milano"],
            "date": ["2023-01-15"],
            "importi": ["1000.00"]
        },
        "summary": "..."
    }
}
```

#### POST /documenti/{id}/analyze
Avvia l'analisi di un documento.

Response:
```json
{
    "status": "success",
    "message": "Analisi avviata"
}
```

### Ricerca e Query

#### POST /query/semantic-search
Esegue una ricerca semantica.

Request:
```json
{
    "query": "Trova tutti i decreti che menzionano Mario Rossi",
    "include_content": true,
    "limit": 10,
    "offset": 0
}
```

Response:
```json
{
    "results": [
        {
            "score": 0.95,
            "documento": {
                "id": 1,
                "filename": "decreto_1.pdf",
                "tipo_documento": "DECRETO",
                "contenuto": "..."
            }
        }
    ],
    "total": 1,
    "page": 1
}
```

#### POST /query/aggregate
Esegue aggregazioni sui documenti.

Request:
```json
{
    "group_by": ["tipo_documento", "data"],
    "metrics": ["avg_score", "importi"]
}
```

Response:
```json
{
    "by_type": {
        "DECRETO": 10,
        "SENTENZA": 5
    },
    "by_date": {
        "2023-01": 8,
        "2023-02": 7
    },
    "metrics": {
        "avg_score": 0.85,
        "total_amount": 50000.00
    }
}
```

## Schema Dati

### Documento
```typescript
interface Documento {
    id: number;
    filename: string;
    tipo_documento: "DECRETO" | "SENTENZA" | "PERIZIA";
    contenuto: string;
    stato_elaborazione: "PENDING" | "PROCESSING" | "COMPLETED" | "ERROR";
    metadata: {
        entities: {
            persone: string[];
            organizzazioni: string[];
            date: string[];
            importi: string[];
        };
        summary: string;
    };
    data_caricamento: string;
}
```

### User
```typescript
interface User {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superuser: boolean;
}
```

## Gestione Errori

Le API utilizzano i seguenti codici HTTP:

- 200: Successo
- 201: Creazione completata
- 400: Richiesta non valida
- 401: Non autorizzato
- 403: Accesso negato
- 404: Risorsa non trovata
- 500: Errore interno

Esempio errore:
```json
{
    "detail": "Messaggio di errore"
}
```

## Rate Limiting

Le API hanno i seguenti limiti:

- 100 richieste/minuto per IP
- 1000 richieste/ora per utente
- Max 10MB per upload file
- Max 50 documenti per batch

## Versioning

L'API è versionata tramite header:
```
Accept: application/vnd.legal-docs.v1+json
``` 