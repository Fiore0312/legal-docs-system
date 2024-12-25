# Guida al Deployment

## Requisiti di Sistema

### Hardware Minimo
- CPU: 4 core
- RAM: 8GB
- Storage: 50GB SSD
- Rete: 100Mbps

### Hardware Raccomandato
- CPU: 8+ core
- RAM: 16GB+
- Storage: 200GB+ SSD
- Rete: 1Gbps

### Software
- Ubuntu 20.04 LTS o superiore
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx
- Supervisor

## Installazione

### 1. Preparazione Sistema

```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa dipendenze
sudo apt install -y python3-pip python3-venv postgresql redis-server nginx supervisor

# Crea utente applicazione
sudo useradd -m -s /bin/bash legaldocs
sudo usermod -aG sudo legaldocs
```

### 2. Database Setup

```bash
# Configura PostgreSQL
sudo -u postgres psql

CREATE DATABASE legaldocs;
CREATE USER legaldocs WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE legaldocs TO legaldocs;
\q

# Test connessione
psql -h localhost -U legaldocs -d legaldocs
```

### 3. Applicazione

```bash
# Clone repository
git clone https://github.com/tuouser/legal-docs-system.git
cd legal-docs-system

# Setup ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura environment
cp .env.example .env
nano .env  # Modifica parametri

# Inizializza database
python scripts/init_db.py
```

### 4. Configurazione Web Server

```nginx
# /etc/nginx/sites-available/legaldocs
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/legaldocs/static;
    }

    location /media {
        alias /path/to/legaldocs/media;
    }
}
```

### 5. Supervisor Setup

```ini
# /etc/supervisor/conf.d/legaldocs.conf
[program:legaldocs]
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/path/to/legaldocs
user=legaldocs
autostart=true
autorestart=true
stderr_logfile=/var/log/legaldocs/err.log
stdout_logfile=/var/log/legaldocs/out.log
```

### 6. SSL/TLS

```bash
# Installa Certbot
sudo apt install certbot python3-certbot-nginx

# Ottieni certificato
sudo certbot --nginx -d your_domain.com
```

## Configurazione

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/legaldocs
REDIS_URL=redis://localhost
SECRET_KEY=your_secure_key
ALLOWED_HOSTS=your_domain.com
DEBUG=False
```

### Logging

```python
# config/logging.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/legaldocs/app.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## Backup e Recovery

### Backup Automatico

```bash
#!/bin/bash
# /scripts/backup.sh

# Backup database
pg_dump legaldocs > /backup/db/legaldocs_$(date +%Y%m%d).sql

# Backup media
rsync -av /path/to/media /backup/media/

# Backup config
cp -r /path/to/config /backup/config/

# Rotazione backup (mantieni ultimi 30 giorni)
find /backup -mtime +30 -delete
```

### Recovery

```bash
# Ripristino database
psql legaldocs < /backup/db/legaldocs_20231225.sql

# Ripristino media
rsync -av /backup/media/ /path/to/media/

# Ripristino config
cp -r /backup/config/ /path/to/config/
```

## Monitoring

### Metriche Chiave

1. **Sistema**
   - CPU Usage
   - Memory Usage
   - Disk I/O
   - Network Traffic

2. **Applicazione**
   - Response Time
   - Error Rate
   - Active Users
   - Queue Length

3. **Database**
   - Connection Count
   - Query Performance
   - Table Size
   - Index Usage

### Prometheus + Grafana

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'legaldocs'
    static_configs:
      - targets: ['localhost:8000']
```

### Alerting

```yaml
# alerts.yml
groups:
  - name: legaldocs
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.01
        for: 5m
        labels:
          severity: critical
```

## Manutenzione

### Checklist Giornaliera
- [ ] Verifica logs
- [ ] Monitoraggio risorse
- [ ] Backup automatico
- [ ] Queue status

### Checklist Settimanale
- [ ] Analisi performance
- [ ] Pulizia storage
- [ ] Update security
- [ ] Backup manuale

### Checklist Mensile
- [ ] System updates
- [ ] SSL renewal
- [ ] DB optimization
- [ ] Performance review

## Scaling

### Verticale
- Aumenta CPU/RAM
- SSD più veloce
- Ottimizza queries
- Cache tuning

### Orizzontale
- Load balancer
- Read replicas
- Sharding
- CDN

## Sicurezza

### Checklist
- [ ] Firewall configurato
- [ ] SSL/TLS attivo
- [ ] Rate limiting
- [ ] Backup criptati
- [ ] Updates automatici
- [ ] Monitoring attivo

### Best Practices
1. Principle of least privilege
2. Regular security audits
3. Automated updates
4. Encrypted backups
5. Access logging
6. Regular pentesting 