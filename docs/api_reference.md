# API Reference

## Introduzione

Questa è la documentazione di riferimento per le API del sistema Liquidazione IA. Le API forniscono funzionalità per la gestione di documenti di liquidazione giudiziale, inclusa l'elaborazione AI, la ricerca semantica e la gestione delle configurazioni.

## Autenticazione

Tutte le richieste API devono essere autenticate utilizzando un token JWT. Il token può essere ottenuto attraverso l'endpoint di login.

### Ottenere un Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "string",
  "password": "string"
}
```

### Utilizzare il Token

Include il token nell'header `Authorization` di ogni richiesta:

```http
Authorization: Bearer <token>
```

## Endpoints

### Autenticazione

#### POST /api/v1/auth/register
Registra un nuovo utente.

**Request Body:**
```json
{
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string"
}
```

#### POST /api/v1/auth/login
Effettua il login e ottiene un token.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

#### POST /api/v1/auth/refresh
Rinnova un token di accesso.

#### GET /api/v1/auth/me
Ottiene le informazioni dell'utente corrente.

### Documenti

#### POST /api/v1/documenti
Carica un nuovo documento.

**Request Body:**
```json
{
  "file": "binary",
  "metadata": {
    "tipo": "string",
    "descrizione": "string"
  }
}
```

#### GET /api/v1/documenti
Lista tutti i documenti.

**Query Parameters:**
- `page`: numero pagina
- `size`: dimensione pagina
- `tipo`: filtra per tipo
- `search`: ricerca testuale

#### GET /api/v1/documenti/{id}
Ottiene un documento specifico.

#### PUT /api/v1/documenti/{id}
Aggiorna un documento.

#### DELETE /api/v1/documenti/{id}
Elimina un documento.

### AI

#### POST /api/v1/ai/{documento_id}/analyze
Avvia l'analisi AI di un documento.

#### GET /api/v1/ai/{documento_id}/status
Verifica lo stato dell'analisi.

#### GET /api/v1/ai/search
Esegue una ricerca semantica.

**Query Parameters:**
- `query`: testo da cercare
- `limit`: numero massimo risultati
- `threshold`: soglia di similarità

#### POST /api/v1/ai/{documento_id}/extract-entities
Estrae le entità da un documento.

#### POST /api/v1/ai/{documento_id}/summarize
Genera un riassunto del documento.

### Configurazioni

#### GET /api/v1/config/{section}
Ottiene una sezione di configurazione.

#### PUT /api/v1/config/{section}
Aggiorna una sezione di configurazione.

#### POST /api/v1/config/validate
Valida una configurazione.

## Modelli Dati

### User
```json
{
  "id": "integer",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Documento
```json
{
  "id": "integer",
  "titolo": "string",
  "tipo_documento": "string",
  "contenuto": "string",
  "metadata": "object",
  "embedding": "array",
  "percorso_file": "string",
  "stato_elaborazione": "string",
  "risultati_analisi": "object",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Codici di Errore

- `400`: Bad Request - Richiesta non valida
- `401`: Unauthorized - Autenticazione richiesta
- `403`: Forbidden - Permessi insufficienti
- `404`: Not Found - Risorsa non trovata
- `422`: Unprocessable Entity - Dati non validi
- `429`: Too Many Requests - Troppe richieste
- `500`: Internal Server Error - Errore interno

## Rate Limiting

Le API sono soggette a rate limiting per prevenire abusi. I limiti sono:
- 100 richieste per minuto per IP
- Header di risposta includono:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Versioning

Le API sono versionate nel path: `/api/v1/`

## CORS

Le API supportano CORS per `localhost:3000` in sviluppo. 