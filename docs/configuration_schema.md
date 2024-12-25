# Configuration Schema

## Introduzione

Questo documento descrive lo schema di configurazione del sistema Liquidazione IA. Le configurazioni sono organizzate in file YAML separati per modularità e manutenibilità.

## Schema Generale

### agent_config.yaml

```yaml
agent:
  # Configurazioni generali
  name: string
  version: string
  description: string

  # Capabilities
  capabilities:
    - string[]

  # Elaborazione documenti
  document_processing:
    max_file_size_mb: integer
    supported_formats:
      - string[]
    ocr_enabled: boolean
    ocr_language: string
    chunk_size: integer
    chunk_overlap: integer

  # Analisi testo
  text_analysis:
    min_confidence: float
    max_tokens_per_request: integer
    classification_threshold: float
    similarity_threshold: float
    max_results: integer

  # Memoria
  memory:
    cache_enabled: boolean
    cache_ttl_hours: integer
    max_cached_items: integer
    vector_dimension: integer

  # Logging
  logging:
    enabled: boolean
    level: string
    format: string
    file: string

  # Sicurezza
  security:
    require_authentication: boolean
    allowed_roles:
      - string[]
    rate_limit:
      enabled: boolean
      max_requests: integer
      time_window_seconds: integer

  # Documentazione
  documentation:
    auto_update: boolean
    versioning: boolean
    backup_enabled: boolean
    max_versions: integer
    docs_path: string
```

### api_config.yaml

```yaml
api:
  # Configurazioni generali
  title: string
  version: string
  description: string
  prefix: string

  # Server
  server:
    host: string
    port: integer
    workers: integer
    debug: boolean
    reload: boolean
    timeout_keep_alive: integer

  # CORS
  cors:
    enabled: boolean
    allow_origins:
      - string[]
    allow_methods:
      - string[]
    allow_headers:
      - string[]
    allow_credentials: boolean
    max_age: integer

  # Rate limiting
  rate_limit:
    enabled: boolean
    max_requests: integer
    time_window_seconds: integer
    by_ip: boolean
    exclude_paths:
      - string[]

  # Documentazione
  docs:
    enabled: boolean
    path: string
    redoc_path: string
    openapi_path: string
    swagger_ui_parameters:
      docExpansion: string
      defaultModelsExpandDepth: integer

  # Middleware
  middleware:
    compression:
      enabled: boolean
      minimum_size: integer
      level: integer
    trusted_hosts:
      enabled: boolean
      allowed_hosts:
        - string[]
    http_basic:
      enabled: boolean
      username: string
      password: string

  # Logging
  logging:
    enabled: boolean
    level: string
    format: string
    access_log: boolean
    error_log: boolean
    log_file: string

  # Sicurezza
  security:
    ssl_enabled: boolean
    ssl_keyfile: string
    ssl_certfile: string
    proxy_headers: boolean
    max_upload_size_mb: integer
    allowed_upload_extensions:
      - string[]
```

### services_config.yaml

```yaml
services:
  # Database
  database:
    host: string
    port: integer
    name: string
    user: string
    password: string
    ssl_mode: string
    pool_size: integer
    max_overflow: integer
    pool_timeout: integer
    pool_recycle: integer
    echo: boolean

  # Email
  email:
    smtp_server: string
    smtp_port: integer
    smtp_user: string
    smtp_password: string
    from_email: string
    use_tls: boolean
    timeout: integer
    templates_dir: string
    default_language: string

  # AI
  ai:
    openai:
      api_key: string
      embedding_model: string
      llm_model: string
      max_tokens: integer
      temperature: float
      timeout: integer
      retry_attempts: integer
      retry_delay: integer
    
    ocr:
      engine: string
      language: string
      dpi: integer
      timeout: integer
      enhance_image: boolean
      psm: integer
      oem: integer

  # Vector store
  vector_store:
    engine: string
    collection_name: string
    dimension: integer
    similarity_metric: string
    index_type: string
    index_lists: integer
    probe_lists: integer
    nprobe: integer
    ef_search: integer
    ef_construction: integer

  # Storage
  storage:
    type: string
    local:
      base_path: string
      max_size_mb: integer
      allowed_extensions:
        - string[]
    s3:
      bucket: string
      region: string
      access_key: string
      secret_key: string
      endpoint_url: string

  # Cache
  cache:
    type: string
    redis:
      host: string
      port: integer
      db: integer
      password: string
      ssl: boolean
      timeout: integer
    ttl:
      default: integer
      embeddings: integer
      analysis: integer
      search: integer

  # Task queue
  task_queue:
    broker: string
    redis:
      host: string
      port: integer
      db: integer
      password: string
    rabbitmq:
      host: string
      port: integer
      user: string
      password: string
      vhost: string
    celery:
      workers: integer
      max_tasks_per_child: integer
      task_timeout: integer
      retry_delay: integer
      max_retries: integer
```

### prompts_config.yaml

```yaml
prompts:
  # Classificazione documenti
  document_classification:
    system: string
    user: string
    response_format: string

  # Estrazione entità
  entity_extraction:
    system: string
    user: string
    response_format: string

  # Generazione riassunti
  summarization:
    system: string
    user: string
    response_format: string

  # Analisi semantica
  semantic_analysis:
    system: string
    user: string
    response_format: string

  # Validazione documenti
  document_validation:
    system: string
    user: string
    response_format: string

  # Ricerca semantica
  semantic_search:
    system: string
    user: string
    response_format: string

  # Impostazioni generali
  settings:
    max_input_length: integer
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop_sequences:
      - string[]
    template_format: string
    default_language: string
```

## Validazione

Le configurazioni sono validate usando Pydantic. Ogni sezione ha il suo schema di validazione definito in `config_validator.py`.

## Variabili Sensibili

Le seguenti configurazioni devono essere impostate tramite variabili d'ambiente:
- Database password
- API keys
- Token segreti
- Credenziali SMTP
- Credenziali S3
- Password Redis

## Valori di Default

I valori di default sono definiti in `config_validator.py` e possono essere sovrascritti nei file di configurazione o tramite variabili d'ambiente.

## Priorità

L'ordine di priorità per i valori di configurazione è:
1. Variabili d'ambiente
2. File di configurazione
3. Valori di default

## Versioning

Le configurazioni sono versionate in `config/backups/` con timestamp nel formato:
```
{config_name}_{YYYYMMDD_HHMMSS}.yaml
``` 