# 🛡️ Aegis – Intelligent SIEM & Threat Response Platform

> **[📖 Project Explanation](project_explanation.md)** | **[🧪 Testing Guide](testing_guide.md)**

**Aegis** is a production-grade Security Information and Event Management (SIEM) system built for modern threat detection. It unifies high-performance log ingestion, rule-based detection, unsupervised machine learning, real-time WebSocket streaming, JWT-authenticated APIs, and automated incident response into a single, fully deployable platform.

![SOC Dashboard](dashboard_preview.png)

---

## 🚀 Key Features

### 🧠 Advanced Detection Engine
- **Hybrid Detection**: Combines traditional **Sigma-like rules** (SSH brute-force, firewall blocks) with an **Isolation Forest ML pipeline** for zero-day anomaly detection.
- **Calibrated ML**: Model is a `sklearn.Pipeline(StandardScaler → IsolationForest)` — feature scaling is learned from data and persisted in `model.joblib`, eliminating hardcoded guesses.
- **Explainable AI**: Every ML anomaly includes a real Z-score explanation (e.g., `"Anomalous Request Frequency (z=4.2)"`).
- **Correlation Engine**: Stateful multi-stage attack detection (Brute Force → Successful Login → Privilege Escalation) using Redis.

### 🔐 Security-First API
- **JWT Authentication**: Every protected endpoint requires a Bearer token issued via OAuth2 password flow (`POST /api/v1/auth/token`).
- **IP Blocking at Ingestion**: Blocked IPs receive HTTP 403 before any processing — enforced at the FastAPI layer via Redis.
- **Rate Limiting**: Per-IP rate limiter on all ingest routes.
- **Secrets via `.env`**: All credentials (JWT secret key, API tokens, bcrypt password hashes) are loaded from `.env` — never hardcoded.

### ⚡ Real-Time WebSocket Feed
- **Architecture**: Worker → Redis pub/sub (`aegis:feed`) → FastAPI WebSocket → Browser
- **Zero polling**: Next.js dashboard uses `ws.onmessage` to receive processed logs, alerts, and incidents instantly as they're detected.
- **JWT-guarded WebSocket**: Clients authenticate via `?token=<JWT>` query param before the connection is accepted.
- **Live status indicator**: Dashboard header shows `🟢 WS LIVE` / `🟡 CONNECTING` / `🔴 POLLING`.

### 🛡️ Automated Response (SOAR) + iptables
- **Redis blocking**: High-risk IPs are added to `blocked:{ip}` Redis keys with TTL-based auto-expiry.
- **Real iptables enforcement**: Worker optionally calls `iptables -I INPUT -s <ip> -j DROP` and syncs removals on a 30-second loop tied to Redis TTL expirations (no permanent blocks).
- **YAML-driven policy**: Block threshold, duration, and IP whitelist configurable in `response_config.yaml`.

### 📊 SOC Dashboard
- **Cyberpunk UI**: Immersive dark interface with holographic effects, retro-terminal log stream, and animated stat cards.
- **Auth Gate**: Login screen with bcrypt-authenticated form before any data is visible.
- **Live Incident Tracker**: Real-time table of correlated attack chains.
- **Alerts & Logs tabs**: Instantly updated via WebSocket — no page refresh needed.

### 🔍 Multi-Source Log Normalization
- **Nginx**: Full request parsing (IP, method, path, status, bytes, user-agent, referrer).
- **SSH**: Distinguishes `Failed password` vs `Accepted password`; extracts attacker IP and username.
- **UFW Firewall**: Parses `[UFW BLOCK]` events with source/destination IP and protocol.
- **Extensible**: Regex-based `NormalizationService` — add new log sources in minutes.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React, Tailwind | SOC Dashboard + Auth UI |
| **Backend API** | Python (FastAPI) | Log Ingestion, REST API, WebSocket |
| **Auth** | python-jose (JWT) + passlib (bcrypt) | Stateless authentication |
| **Processing** | Python async workers | ETL, Detection, Correlation, iptables |
| **Stream Buffer** | Redis Streams | Decouples ingestion from processing |
| **Pub/Sub** | Redis pub/sub | Worker → WebSocket fan-out |
| **State Store** | Redis | Risk scoring, blocking, rate limiting |
| **Log Storage** | Elasticsearch 8.13 | Search & Analytics |
| **ML** | Scikit-Learn (Pipeline + IsolationForest) | Calibrated anomaly detection |
| **Reverse Proxy** | Nginx | SSL termination, WS upgrades |
| **CI/CD** | GitHub Actions | Lint → Build → Push GHCR → Deploy |

---

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local scripts)
- Node.js 20+ (for frontend development)

### 1. Configure Secrets

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
# Generate a real JWT secret:
openssl rand -hex 32

# Generate a bcrypt password hash:
python3 -c "from passlib.context import CryptContext; c=CryptContext(schemes=['bcrypt']); print(c.hash('your-password'))"
```

### 2. Launch the Stack

```bash
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **Kibana** | http://localhost:5601 |

> Default login: `admin` / `aegis-admin`  
> Change `ADMIN_PASSWORD_HASH` in `.env` before production use.

### 3. Initialize Elasticsearch

```bash
docker compose exec worker python tools/setup_elasticsearch.py
```

### 4. Train the ML Model

```bash
# Generate training dataset (10,000 realistic logs with injected anomalies)
python3 backend/tools/generate_dataset.py

# Train Pipeline(StandardScaler → IsolationForest) — saves to model.joblib
python3 backend/train_model.py
```

Sample output:
```
Training on 10000 normal records…
Pipeline (scaler + model) saved to model.joblib
  Hour:      mean=11.48, std=6.90
  MsgLen:    mean=35.24, std=12.34
  IsSSH:     mean=0.15,  std=0.36
  LoginRate: mean=9.66,  std=6.04
```

### 5. Verify Functionality (Red Team Simulation)

```bash
docker compose exec worker python tools/verify_full_system.py
```

Simulates: SSH brute force → suspicious admin login → data exfiltration → privilege escalation.  
Expect **✅ PASS** for all checks.

### 6. Health Check

```bash
curl http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "services": { "api": "online", "elasticsearch": "online", "redis": "online" }
}
```

---

## 🔌 API Reference

All protected endpoints require `Authorization: Bearer <token>`.

### Auth (public)
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=aegis-admin
```
Returns `{ "access_token": "...", "token_type": "bearer" }`

### Ingest (protected)
```http
POST /api/v1/ingest/logs        # Structured JSON log(s)
POST /api/v1/ingest/raw         # Raw syslog text
```

### Dashboard (protected)
```http
GET /api/v1/dashboard/stats
GET /api/v1/dashboard/alerts
GET /api/v1/dashboard/incidents
GET /api/v1/dashboard/logs?query=<lucene>
```

### WebSocket Live Feed (JWT via query param)
```
ws://localhost:8000/api/v1/ws/feed?token=<JWT>
```
Each message is a JSON-encoded processed log entry pushed in real-time.

---

## 🏗️ Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py           # POST /auth/token  (JWT issuer)
│   │   │   ├── ingest.py         # POST /ingest/*    (rate-limited, JWT-guarded)
│   │   │   ├── dashboard.py      # GET  /dashboard/* (JWT-guarded, ES 8.x)
│   │   │   └── feed.py           # WS   /ws/feed     (real-time pub/sub)
│   │   ├── core/
│   │   │   ├── config.py         # Settings (env-driven via .env)
│   │   │   ├── security.py       # JWT issuance + get_current_user dependency
│   │   │   └── limiter.py        # Per-IP rate limiter
│   │   ├── models/               # Pydantic models (LogEntry, etc.)
│   │   ├── response/             # YAML response policy
│   │   └── services/
│   │       ├── normalization.py  # Multi-source log parser (Nginx/SSH/UFW)
│   │       ├── detection_rules.py# Rule engine (Sigma-like)
│   │       ├── detection_ml.py   # ML pipeline with calibrated scaler
│   │       ├── correlation.py    # Multi-stage incident engine
│   │       ├── enrichment.py     # GeoIP & Threat Intel
│   │       ├── storage.py        # Elasticsearch 8.x client (no body= kwarg)
│   │       └── response.py       # Automated blocking (Redis + iptables)
│   ├── app/worker.py             # Stream consumer → pub/sub publisher → iptables sync
│   ├── tools/                    # Dataset generator, benchmarker, red-team simulator
│   └── train_model.py            # Pipeline(StandardScaler → IsolationForest) trainer
├── frontend/
│   └── app/
│       ├── page.tsx              # Dashboard (auth gate + WebSocket client)
│       └── components/
│           └── LoginForm.tsx     # JWT login form
├── nginx/
│   └── aegis.conf                # SSL termination + WebSocket upgrade config
├── tests/                        # 12-file test suite
├── .env.example                  # Secret template (commit this, NOT .env)
├── .github/workflows/ci-cd.yml  # 4-job CI/CD: lint → build → GHCR → VPS deploy
└── docker-compose.yml            # Full stack (ES 8.13, Redis 7.2, NET_ADMIN cap)
```

---

## 🧪 Test Suite

| Test File | Coverage Area |
| :--- | :--- |
| `test_detection.py` | ML & Rule-based detection |
| `test_detection_rules.py` | Rule engine unit tests |
| `test_correlation.py` | Multi-stage attack correlation |
| `test_enrichment.py` | GeoIP & Threat Intel enrichment |
| `test_response_automation.py` | Automated blocking & SOAR response |
| `test_ingest.py` | Log ingestion pipeline |
| `test_ingest_prod.py` | Production-load ingestion testing |
| `test_e2e.py` | End-to-end system flow |
| `test_ml_explainability.py` | AI explanation output validation |
| `test_normalization_firewall.py` | UFW/SSH/Nginx log normalization |
| `test_real_api.py` | Live API integration tests |
| `test_ilm_storage.py` | Elasticsearch ILM storage lifecycle |

```bash
python tests/test_response_automation.py
```

---

## 🚢 Production Deployment (VPS)

### 1. Nginx (SSL + WebSocket)
```bash
sudo cp nginx/aegis.conf /etc/nginx/sites-available/aegis
sudo ln -s /etc/nginx/sites-available/aegis /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
sudo nginx -t && sudo systemctl reload nginx
```

### 2. iptables Enforcement
Set in `.env`:
```bash
IPTABLES_ENABLED=true
```
The worker container has `cap_add: [NET_ADMIN]` — blocks are automatically removed when Redis TTL expires.

### 3. CI/CD via GitHub Actions
Add these secrets to your GitHub repository (`Settings → Secrets`):

| Secret | Value |
|--------|-------|
| `VPS_HOST` | Server IP |
| `VPS_USER` | SSH username |
| `VPS_SSH_KEY` | Private SSH key |
| `DOMAIN` | your-domain.com |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_USERNAME` | Admin login |
| `ADMIN_PASSWORD_HASH` | bcrypt hash |

Every push to `main` → lints, builds, pushes Docker images to GHCR, and deploys to your VPS automatically.

---

## 🗺️ Roadmap

- [x] **Core Infrastructure**: FastAPI + Redis Streams + Elasticsearch 8.x
- [x] **Hybrid Detection**: Rule engine + ML Isolation Forest pipeline
- [x] **Correlation Engine**: Multi-stage attack detection
- [x] **SOC Dashboard**: Cyberpunk Next.js UI
- [x] **Multi-Source Normalization**: Nginx, SSH, UFW
- [x] **Comprehensive Test Suite**: 12 test files, full coverage
- [x] **JWT Authentication**: Protects all API and WebSocket endpoints
- [x] **Real-Time WebSocket Feed**: Redis pub/sub → browser (zero polling)
- [x] **Calibrated ML Scaler**: StandardScaler persisted in pipeline
- [x] **Real iptables Enforcement**: TTL-synced block/unblock cycle
- [x] **Production Packaging**: `.env`, Nginx SSL config, GitHub Actions CI/CD
- [ ] Multi-Tenancy Support
- [ ] PDF Incident Report Export
- [ ] MITRE ATT&CK Framework Tagging

---

## 📜 License

MIT License. Open Source Security.

---
*Built with ❤️ for the modern SOC analyst.*