# ClawBot DSGVO MVP

Privacy-first customer feedback processing with DSGVO compliance for Austrian SMBs (retail, energy, tourism).

## 🦞 Features

- **PII Detection**: Automatic detection of emails, phone numbers (AT/DE), IBAN, IP addresses, credit cards
- **Pseudonymization**: AES-256 encryption with fun animal names (alpine-marmot, munchy-otter, etc.)
- **LLM Analysis**: Sentiment, category, and urgency analysis using Ollama (qwen2.5:3b)
- **Audit Trail**: Complete DSGVO-compliant logging of all operations
- **Dashboard**: Real-time monitoring with dark mode UI

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repo>
cd clawbot

# One-command setup
./setup.sh

# Dashboard: http://localhost:8443
# API Docs:  http://localhost:8000/docs
```

## 📁 Project Structure

```
clawbot/
├── docker-compose.yml          # 4 services: core, db, llm, ui
├── setup.sh                    # One-command setup
├── core/                       # FastAPI application
│   ├── main.py                 # Main app with all routes
│   ├── config.py               # Configuration
│   ├── api/                    # API endpoints
│   │   ├── health.py           # Health check
│   │   ├── ingest.py           # Feedback ingestion
│   │   ├── signals.py          # Signal retrieval
│   │   ├── audit.py            # Audit log
│   │   └── compliance.py       # Compliance reporting
│   ├── models/                 # Data models
│   │   └── schemas.py          # Pydantic schemas
│   └── pipeline/               # Processing pipeline
│       ├── detector.py         # PII detection (regex)
│       ├── anonymizer.py       # Pseudonymization (AES-256)
│       ├── analyzer.py         # LLM analysis (Ollama)
│       └── audit_logger.py     # Audit logging
├── templates/                  # Privacy templates
│   ├── retail.yaml             # Retail configuration
│   ├── energie.yaml            # Energy company config
│   └── tourismus.yaml          # Tourism config
├── dashboard/                  # Web UI
│   ├── index.html              # Dashboard HTML
│   ├── style.css               # Dark mode CSS
│   └── app.js                  # Frontend logic
└── scripts/                    # Utility scripts
    ├── create-tenant.sh        # Create new tenant
    └── test-pipeline.sh        # Test the pipeline
```

## 🔌 API Endpoints

- `GET  /api/v1/health` - Health check
- `POST /api/v1/ingest` - Ingest feedback (full pipeline)
- `GET  /api/v1/signals` - List signals
- `GET  /api/v1/signals/{id}` - Get signal by ID
- `GET  /api/v1/audit-log` - Audit log entries
- `GET  /api/v1/compliance/report` - Compliance report

## 🧪 Testing

```bash
# Test the complete pipeline
./scripts/test-pipeline.sh

# Create a new tenant
./scripts/create-tenant.sh my-tenant

# Manual test
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "default",
    "content": "Kontaktieren Sie mich unter max@example.com oder 0664 1234567",
    "source": "email"
  }'
```

## 🔒 Privacy & Security

- **Local Processing**: All PII detection runs locally (no external APIs)
- **AES-256 Encryption**: Original PII values encrypted before storage
- **Pseudonymization**: Consistent, reversible pseudonyms (alpine-marmot, munchy-otter, etc.)
- **Audit Trail**: Complete logging of all data operations
- **No PII to LLM**: Ollama only processes anonymized content

## 🎯 Use Cases

1. **Retail**: Product complaints, delivery issues, returns
2. **Energy**: Billing complaints, outages, meter readings
3. **Tourism**: Booking issues, facility feedback, cancellations

## 📊 Dashboard

The dashboard (port 8443) shows:
- Total signals processed
- PII entities anonymized
- Critical urgency count
- Recent signals with categories/sentiments
- Audit log entries

Auto-refreshes every 10 seconds.

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL 15
- **LLM**: Ollama with qwen2.5:3b
- **Frontend**: Vanilla JS, modern CSS
- **Encryption**: cryptography (Fernet/AES-256)
- **Deployment**: Docker Compose

## 📝 Environment Variables

See `.env.example` for all configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `ENCRYPTION_KEY`: 32-byte key for AES-256
- `OLLAMA_URL`: Ollama service URL
- `OLLAMA_MODEL`: Model to use (default: qwen2.5:3b)

## 🤝 Contributing

This is an MVP. Contributions welcome!

## 📄 License

MIT License

---

Built with 🦞 for Austrian SMBs • DSGVO Compliant • Privacy First
