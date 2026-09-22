# 🚀 Secure B2B Webhook Dispatcher

[![Production Ready](https://img.shields.io/badge/production-ready-green.svg)](https://github.com/melaven/webhook-dispatcher)
[![Security](https://img.shields.io/badge/security-enterprise-blue.svg)](https://github.com/melaven/webhook-dispatcher)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://hub.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-43%20passed-brightgreen.svg)](https://github.com/melaven/webhook-dispatcher)

A **production-ready**, **enterprise-grade** webhook dispatcher built with **FastAPI**, **Pydantic**, and **SQLAlchemy**. Designed to securely capture, validate, and audit incoming webhooks from external B2B systems with **military-grade security** and **professional PDF report generation**.

## ✨ Key Features

🔐 **Multi-layer Security**
- API key authentication with configurable validation
- HMAC-SHA256 signature verification
- Replay attack protection (timestamp + nonce validation)
- Rate limiting via nginx reverse proxy
- Path-based security blocking

📊 **Professional PDF Reports**
- Generate beautiful PDF reports from Excel data
- Clean B2B design with corporate styling
- WeasyPrint + Pandas integration
- Automatic metrics calculation (revenue, leads, conversion)

🏗️ **Clean Architecture**
- Domain/Application/Infrastructure layers separation
- Strict typing with Pydantic v2
- Comprehensive input validation
- Immutable audit trail

🐳 **Production Infrastructure**
- Docker Compose with nginx + Redis + FastAPI
- Health checks and graceful shutdowns
- Configurable environment management
- Zero-downtime deployment ready

🧪 **Comprehensive Testing**
- 43 automated tests covering all scenarios
- Security integration tests
- Replay protection validation
- Business logic verification

## 🎯 Use Cases

- **CRM Integration**: Capture leads from Tilda, Webflow, HubSpot
- **Payment Processing**: Handle Stripe, PayPal, Square webhooks
- **E-commerce**: Process Shopify, WooCommerce order notifications
- **Analytics**: Generate client reports from marketing data
- **B2B Systems**: Secure inter-service communication

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/melaven/webhook-dispatcher.git
cd webhook-dispatcher

# Configure your environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# Build and run with Docker Compose
docker compose up -d --build

# Check services status
docker ps
```

Your webhook dispatcher is now running at `http://localhost:8000`!

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run the application
python main.py
```

## ⚙️ Configuration

### Environment Setup

1. **Copy the example configuration:**
```bash
cp .env.example .env
```

2. **Generate secure API keys:**
```bash
# Generate API key (32 characters)
python -c "import secrets; print('DISPATCHER_API_KEY=' + secrets.token_hex(32))"

# Generate HMAC secret (64 characters)
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_hex(64))"
```

3. **Update .env with your keys:**
```bash
# Required: Your webhook API key
DISPATCHER_API_KEY=your_secure_api_key_here_64_chars_minimum

# Optional: HMAC signature verification
WEBHOOK_SECRET=your_hmac_secret_key_here_128_chars_recommended

# Optional: Database configuration
DATABASE_URL=sqlite:///./data/webhook_audit.db
```

### Security Best Practices

- 🔐 Use different API keys for development/staging/production
- 🔄 Rotate keys regularly (monthly recommended)
- 🛡️ Enable HMAC verification for critical webhooks
- 📝 Monitor audit logs for suspicious activity
- 🔒 Use HTTPS in production (configure nginx SSL)

## 📡 API Usage

### Send a Webhook

```bash
# Lead creation webhook
curl -X POST "http://localhost:8000/api/v1/webhook/incoming" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "lead.created",
    "timestamp": 1726480000,
    "source": "landing_page",
    "data": {
      "name": "John Doe",
      "phone": "+1234567890", 
      "email": "john@example.com",
      "metadata": {
        "utm_source": "google",
        "utm_campaign": "q4_2024"
      }
    }
  }'
```

### Generate PDF Report

```bash
# Generate sample report
curl -X GET "http://localhost:8000/api/reports/sample?client_name=Demo%20Client" \
  -H "X-API-Key: your_api_key_here" \
  --output sample_report.pdf

# Generate report from Excel file
curl -X POST "http://localhost:8000/api/reports/generate" \
  -H "X-API-Key: your_api_key_here" \
  -F "excel_file=@your_data.xlsx" \
  -F "client_name=Your Company Name" \
  --output client_report.pdf
```

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
      "utm_campaign": "q4_2024",
      "landing_page": "/pricing"
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
    "customer_email": "customer@example.com",
    "product_id": "premium_plan"
  }
}
```

### Order Creation (`order.created`)
```json
{
  "event_type": "order.created",
  "timestamp": 1726480000,
  "source": "shopify_store",
  "data": {
    "order_id": "ord_1234567890",
    "customer_email": "customer@example.com",
    "amount": 299.99,
    "currency": "USD",
    "items": [
      {
        "name": "Premium Widget",
        "quantity": 2,
        "price": 149.99
      }
    ]
  }
}
```

## 🧪 Testing

### Run All Tests
```bash
# Run the complete test suite
pytest -v

# Expected output:
# =================== 43 passed, 4 skipped, 0 failed ===================
```

### Test Categories
- **Security Tests**: API authentication, HMAC validation, replay protection
- **Business Logic**: Webhook processing, data validation, audit trail  
- **Integration Tests**: End-to-end webhook processing scenarios
- **PDF Generation**: Report template rendering and Excel processing

### Manual Testing
```bash
# Test webhook endpoint
python test_integration_security.py

# Test PDF generation
python app/services/test_reports.py

# Verify project structure
python check_project.py
```

## 📈 API Documentation

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | Optional | Service status and configuration |
| `GET` | `/health` | None | Health check for load balancers |
| `POST` | `/api/v1/webhook/incoming` | **Required** | Main webhook ingestion endpoint |
| `GET` | `/api/v1/stats` | **Required** | Processing statistics and metrics |
| `POST` | `/api/reports/generate` | **Required** | Generate PDF from Excel data |
| `GET` | `/api/reports/sample` | **Required** | Generate sample PDF report |
| `GET` | `/docs` | None | Interactive API documentation |
| `GET` | `/redoc` | None | Alternative API documentation |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     nginx       │────│   FastAPI       │────│    SQLite       │
│ (Reverse Proxy) │    │ (Application)   │    │ (Audit Trail)   │ 
│ Rate Limiting   │    │ Business Logic  │    │ Webhook Logs    │
│ Path Blocking   │    │ Validation      │    │ Statistics      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │     Redis       │
                       │ (Session Store) │
                       │ Replay Cache    │
                       └─────────────────┘
```

### Technology Stack

- **FastAPI**: High-performance Python web framework
- **Pydantic v2**: Data validation and settings management
- **SQLAlchemy**: SQL toolkit and ORM with async support
- **SQLite**: Lightweight database for audit trail
- **Redis**: In-memory data store for caching and sessions
- **nginx**: Reverse proxy with rate limiting
- **WeasyPrint**: HTML/CSS to PDF rendering engine
- **Pandas**: Data analysis and Excel processing
- **Docker**: Containerization and deployment

## 🔧 Production Deployment

### Docker Stack Configuration

```yaml
# docker-compose.yml includes:
- nginx: Reverse proxy with SSL termination
- api: FastAPI application with security layers  
- redis: Caching and session management
- volumes: Persistent data and configuration
```

### Environment-Specific Deployment

```bash
# Development
docker compose -f docker-compose.yml up -d

# Production with SSL
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scaling (multiple API instances)  
docker compose up -d --scale api=3
```

### Monitoring and Logging

- **Health Checks**: Automatic container health monitoring
- **Audit Trail**: Complete webhook processing history in SQLite
- **Request Logging**: Structured logs for debugging and analysis
- **Metrics**: Built-in statistics API for monitoring dashboards

## 🛡️ Security Features

### Authentication & Authorization
- **API Key Validation**: Secure header-based authentication
- **HMAC Verification**: Optional cryptographic signature validation
- **Rate Limiting**: Request throttling to prevent abuse
- **Path Security**: Blocking access to sensitive files (.env, .git)

### Attack Prevention
- **Replay Protection**: Timestamp + nonce validation prevents replay attacks
- **Input Sanitization**: Strict Pydantic validation prevents injection
- **Request Size Limits**: Protection against DoS attacks
- **CORS Configuration**: Cross-origin request security

### Data Protection
- **Audit Trail**: Immutable log of all webhook processing
- **Sensitive Data Masking**: API keys masked in logs
- **Secure Headers**: Security headers for production deployment
- **Environment Isolation**: Separate configurations per environment

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Add tests** for new functionality
4. **Ensure security tests pass**: `pytest tests/test_security.py -v`
5. **Update documentation** if needed
6. **Submit a pull request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black isort

# Run pre-commit checks
black app/ tests/
isort app/ tests/
pytest -v
```

## 📋 Changelog

### v4.0.0 - Latest
- ✨ Professional PDF report generation system
- 🔐 Enhanced security with replay attack protection  
- 🐳 Complete Docker Compose infrastructure
- 📊 Clean Architecture implementation
- 🧪 Comprehensive test suite (43 tests)
- 📚 Complete API documentation

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)
- **Issues**: [GitHub Issues](https://github.com/melaven/webhook-dispatcher/issues)
- **Security**: Report security issues privately to [@hellofsleepingdolls@gmail.com]

---

<div align="center">

**Built with ❤️ for production B2B integrations that demand reliability, security, and auditability.**

[⭐ Star this repo](https://github.com/melaven/webhook-dispatcher) if you find it useful!

</div>
