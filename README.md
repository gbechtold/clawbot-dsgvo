# ClawBot DSGVO

<!-- logo placeholder -->

![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

**GDPR-compliant customer feedback pipeline with local LLM analysis — no PII ever leaves your infrastructure.**

---

## Architecture

```
Customer Feedback (raw text)
         │
         ▼
┌─────────────────────┐
│   ClawBot Core      │  FastAPI  :8000
│                     │
│  ┌───────────────┐  │
│  │  Detector     │  │  regex PII scan (names, phone, email, address…)
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼────────┐  │
│  │  Anonymizer   │  │  pseudonymise / generalise / redact
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼────────┐  │
│  │  Analyzer     │  │  local Ollama LLM → category / urgency / sentiment
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼────────┐  │
│  │  Audit Logger │  │  immutable DSGVO audit trail → PostgreSQL
│  └───────────────┘  │
└─────────────────────┘
         │                         │                        │
         ▼                         ▼                        ▼
  PostgreSQL :5432          Ollama LLM :11434        Nginx Dashboard :8443
```

---

## Prerequisites

- Docker ≥ 24 and Docker Compose v2
- 8 GB RAM (Ollama model + PostgreSQL)
- Git

---

## Quick Start

```bash
git clone https://github.com/gbechtold/clawbot-dsgvo.git
cd clawbot-dsgvo
cp .env.example .env
./setup.sh
```

The setup script pulls all Docker images, starts the stack, and pulls the default Ollama model (`llama3.2:3b`).

Open the dashboard: http://localhost:8443
Open the API docs: http://localhost:8000/docs

---

## API Reference

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Submit raw customer feedback for processing |
| `GET` | `/signals` | Retrieve analysed signal list (paginated) |
| `GET` | `/signals/{id}` | Get a single signal by ID |
| `GET` | `/audit` | Fetch DSGVO audit log entries |
| `GET` | `/compliance/report` | Generate compliance summary |
| `GET` | `/health` | Health check |

### Submit feedback

```bash
curl -s -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: retail-demo" \
  -d '{
    "content": "Ich bin Max Mustermann und hatte ein Problem mit meiner Bestellung.",
    "source": "email",
    "tenant_id": "retail-demo"
  }' | jq .
```

### Retrieve signals

```bash
curl -s "http://localhost:8000/api/v1/signals?tenant_id=retail-demo&limit=10" | jq .
```

### Audit log

```bash
curl -s "http://localhost:8000/api/v1/audit?tenant_id=retail-demo" | jq .
```

### Health check

```bash
curl -s http://localhost:8000/api/v1/health | jq .
```

---

## Privacy Patterns

ClawBot supports three anonymisation strategies, configurable per tenant via templates:

| Pattern | Code | Behaviour | Example |
|---------|------|-----------|---------|
| **Der Tresor** | `A` | Full redaction — value replaced with type placeholder | `Max Mustermann` → `[PERSON]` |
| **Der Diplomat** | `B` | Pseudonymisation — value replaced with consistent animal-adjective token | `Max Mustermann` → `[alpine-beaver]` |
| **Der Hybrid** | `C` | Generalisation — structured data (address, phone) replaced with category label | `Hauptstraße 12` → `[Adresse anonymisiert]` |

Templates are stored in `templates/` as YAML files and assigned per tenant.

---

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENCRYPTION_KEY` | *(must change)* | 32-byte key for pseudonym vault encryption |
| `DB_PASSWORD` | `clawbot_secure_pass` | PostgreSQL password |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for LLM analysis |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`) |
| `DATABASE_URL` | auto-built | Full PostgreSQL connection string |
| `OLLAMA_URL` | `http://clawbot-llm:11434` | Ollama service URL |

---

## Multi-Tenant Usage

Create a new tenant with a specific privacy template:

```bash
./scripts/create-tenant.sh <tenant-id> <template>
# Example:
./scripts/create-tenant.sh my-shop retail
```

Available templates: `retail`, `energie`, `tourismus`

Each tenant gets an isolated pseudonym vault — the same real name maps to a *different* token across tenants.

---

## Project Structure

```
clawbot/
├── docker-compose.yml          # 4 services: core, db, llm, ui
├── setup.sh                    # One-command setup
├── core/                       # FastAPI application
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── health.py
│   │   ├── ingest.py
│   │   ├── signals.py
│   │   ├── audit.py
│   │   └── compliance.py
│   └── pipeline/
│       ├── detector.py         # PII detection (regex)
│       ├── anonymizer.py       # Pseudonymisation (AES-256)
│       ├── analyzer.py         # LLM analysis (Ollama)
│       └── audit_logger.py     # Audit logging
├── templates/                  # Privacy templates per industry
│   ├── retail.yaml
│   ├── energie.yaml
│   └── tourismus.yaml
├── dashboard/                  # Web UI (Nginx)
└── scripts/                    # Utility scripts
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit with conventional commits: `git commit -m "feat: add …"`
4. Open a Pull Request

Please make sure existing tests pass before submitting.

---

## License

MIT © 2025 ClawBot Contributors
