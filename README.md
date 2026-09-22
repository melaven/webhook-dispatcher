# Webhook Dispatcher 🚀

🚀 **Secure B2B Webhook Dispatcher** — production-ready FastAPI service for enterprise webhook processing.

✨ **Features:**
• 🔐 Multi-layer security: API keys + HMAC + replay protection
• 📊 PDF reports from Excel (WeasyPrint + Pandas)  
• 🏗️ Clean Architecture + strict typing
• 🐳 Docker + nginx + Redis
• 🧪 43 tests + audit trail

A high-performance, secure B2B gateway built with **FastAPI**, **Pydantic**, and **SQLAlchemy**, designed to capture, strictly validate, and audit incoming webhooks from external business systems.

## 🎯 What & Why
* **The Problem:** External systems (CRMs, payment gateways, lead forms) send chaotic, unvalidated payloads that can crash backend services or corrupt databases.
* **The Solution:** A lightweight, production-ready middleware that authenticates requests via API keys, validates schemas strictly, and stores a permanent audit trail.

## 🛠 Core Stack & Architecture
* **Framework:** FastAPI (AsyncIO, high throughput performance)
* **Validation:** Pydantic v2 (strict typing, custom constraints, email checks)
* **Persistence:** SQLAlchemy (Async) + aiosqlite (Immutable Audit Trail)
* **Security:** API-Key Header Authentication (`X-API-Key`)
* **Reports:** WeasyPrint + Pandas for PDF generation from Excel data

## 🚀 Quick Start

### Docker Deployment (Recommended)
```bash
git clone https://github.com/melaven/webhook-dispatcher.git
cd webhook-dispatcher

# Configure environment
cp .env.example .env
# Edit .env with your API keys and secrets

# Build and run with Docker
docker compose up -d --build

# Check status
docker ps
```

## 🔒 Security Features
* **Multi-layer Authentication** - API keys + HMAC-SHA256 signatures
* **Replay Attack Protection** - Timestamp + nonce validation
* **Input Sanitization** - Strict Pydantic validation prevents injection attacks
* **Audit Trail** - Immutable SQLite log of all requests and responses
* **Rate Limiting** - nginx-based request throttling

## 📊 PDF Report Generation

Generate professional PDF reports from Excel data:

```bash
# Sample report
curl -X GET "http://localhost/api/reports/sample?client_name=Demo Client" \
     -H "X-API-Key: your_api_key"

# Report from Excel file  
curl -X POST "http://localhost/api/reports/generate" \
     -H "X-API-Key: your_api_key" \
     -F "excel_file=@data.xlsx" \
     -F "client_name=Your Company"
```

## 📈 API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/` | Optional | Service status |
| GET | `/health` | None | Health check |
| POST | `/api/v1/webhook/incoming` | **Required** | Webhook ingestion |
| GET | `/api/v1/stats` | **Required** | Processing statistics |
| POST | `/api/reports/generate` | **Required** | Generate PDF from Excel |
| GET | `/api/reports/sample` | **Required** | Generate sample report |

## 🔧 Production Deployment

### Docker Stack
- **API**: FastAPI application with security & business logic
- **nginx**: Reverse proxy with rate limiting & path blocking
- **Redis**: Session storage and caching
- **SQLite**: Audit trail and persistence

## 📚 Documentation
* **Interactive API Docs**: `http://localhost:8000/docs`
* **ReDoc Documentation**: `http://localhost:8000/redoc`

---

**Built for production B2B integrations that demand reliability, security, and auditability.**
   python -m venv venv
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and secrets
   ```

3. Launch the service:
   ```bash
   python main.py
   # Server starts at http://localhost:8000
   ```

## 🔒 Security Features
* **API Key Authentication** - All endpoints require valid `X-API-Key` header
* **HMAC Signature Validation** - Optional webhook integrity verification
* **Input Sanitization** - Strict Pydantic validation prevents injection attacks
* **Audit Trail** - Immutable SQLite log of all requests and responses

## 📊 Supported Event Types

### Lead Creation (`lead.created`)
```json
{
  "event_type": "lead.created",
  "timestamp": 1726480000,
  "source": "tilda_landing",
  "data": {
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john@example.com",
    "metadata": {
      "utm_source": "google",
      "utm_campaign": "q4_2024"
    }
  }
}
```

### Payment Success (`payment.succeeded`)
```json
{
  "event_type": "payment.succeeded",
  "timestamp": 1726480000,
  "source": "stripe_gateway",
  "data": {
    "transaction_id": "txn_1234567890",
    "amount": 99.99,
    "currency": "USD",
    "customer_email": "customer@example.com"
  }
}
```

## 🧪 Testing & Validation

### Pre-flight Checks
```bash
python check_project.py  # Verify setup
```

### Schema Validation Tests
```bash
python test_examples.py  # Pydantic validation
```

### Security Integration Tests
```bash
python test_integration_security.py  # Full security suite
```

## 📈 API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/` | Optional | Service status |
| GET | `/health` | None | Health check |
| POST | `/api/v1/webhook/incoming` | **Required** | Webhook ingestion |
| GET | `/api/v1/stats` | **Required** | Processing statistics |
| GET | `/api/v1/security/config` | **Required** | Security configuration |

## 🔧 Production Deployment

### Environment Variables
```bash
DISPATCHER_API_KEY=your-production-api-key
WEBHOOK_SECRET=your-hmac-secret-key
```

### Docker Support (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

## 🏛 Architecture Benefits
* **Zero Dependencies** on external databases or message queues
* **Fail-Safe Design** - Invalid payloads are rejected but logged for debugging
* **High Throughput** - AsyncIO architecture handles 1000+ concurrent requests
* **Minimal Attack Surface** - Single ingestion point with comprehensive validation

## 📚 Documentation
* **Interactive API Docs**: `http://localhost:8000/docs`
* **ReDoc Documentation**: `http://localhost:8000/redoc`
* **Testing Guide**: See `TESTING.md`

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all security tests pass
5. Submit a pull request

## 📄 License
MIT License - see LICENSE file for details

---

**Built for production B2B integrations that demand reliability, security, and auditability.**
=======
# webhook-dispatcher
🚀 **Secure Webhook Dispatcher** — production-ready FastAPI service for enterprise webhook processing.  ✨ **Features:** • 🔐 Multi-layer security: API keys + HMAC + replay protection • 📊 PDF reports from Excel (WeasyPrint + Pandas) • 🏗️ Clean Architecture + strict typing • 🐳 Docker + nginx + Redis • 🧪 43 tests + audit trail
>>>>>>> 8e178220ceb2b983295c7c0a3d8067ff4837584b
