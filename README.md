# 🛡️ Aegis – Intelligent SIEM & Threat Response Platform

> **[📖 Project Explanation](project_explanation.md)** | **[🧪 Testing Guide](testing_guide.md)**

**Aegis** is a production-grade Security Information and Event Management (SIEM) system built for modern threat detection. It unifies high-performance log ingestion, rule-based detection, unsupervised machine learning, real-time WebSocket streaming, JWT-authenticated APIs, and automated incident response into a single, fully deployable platform.

![SOC Dashboard](dashboard_preview.png)

---

## 🌐 Live Deployment

| Service | URL | Platform |
|:--------|:----|:---------|
| **SOC Dashboard** | [aegis-threat-platform-git-main-adhacks541s-projects.vercel.app](https://aegis-threat-platform-git-main-adhacks541s-projects.vercel.app) | Vercel |
| **Backend API** | [aegis-threat-platform.onrender.com](https://aegis-threat-platform.onrender.com) | Render |
| **API Docs** | [aegis-threat-platform.onrender.com/docs](https://aegis-threat-platform.onrender.com/docs) | Render |

> **Default credentials:** `admin` / `aegis-admin`
> ⚠️ Free Render tier sleeps after 15 min of inactivity — first request may take ~30s to wake up.

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
- **Secrets via environment variables**: All credentials (JWT secret key, API tokens, bcrypt password hashes) are loaded from environment variables — never hardcoded.

### ⚡ Real-Time WebSocket Feed
- **Architecture**: Worker → Redis pub/sub (`aegis:feed`) → FastAPI WebSocket → Browser
- **Zero polling**: Next.js dashboard uses `ws.onmessage` to receive processed logs, alerts, and incidents instantly as they're detected.
- **JWT-guarded WebSocket**: Clients authenticate via `?token=<JWT>` query param before the connection is accepted.
- **Live status indicator**: Dashboard header shows `🟢 WS LIVE` / `🟡 CONNECTING` / `🔴 POLLING`.

### 🛡️ Automated Response (SOAR)
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
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4 | SOC Dashboard + Auth UI |
| **Backend API** | Python 3.11, FastAPI | Log Ingestion, REST API, WebSocket |
| **Auth** | python-jose (JWT) + passlib (bcrypt) | Stateless authentication |
| **Processing** | Python async workers | ETL, Detection, Correlation |
| **Stream Buffer** | Redis Streams | Decouples ingestion from processing |
| **Pub/Sub** | Redis pub/sub | Worker → WebSocket fan-out |
| **State Store** | Redis Cloud | Risk scoring, blocking, rate limiting |
| **Log Storage** | Elasticsearch 8.x (Elastic Cloud) | Search & Analytics |
| **ML** | Scikit-Learn (Pipeline + IsolationForest) | Calibrated anomaly detection |
| **Frontend Hosting** | Vercel | Auto-deploy from `main` branch |
| **Backend Hosting** | Render (Docker) | Auto-deploy from `main` branch |
| **CI/CD** | GitHub Actions | Lint → Build → validate on every push |

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Clone & Configure

```bash
git clone https://github.com/adhacks541/aegis-threat-platform.git
cd aegis-threat-platform
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Generate JWT secret:
openssl rand -hex 32

# Generate bcrypt password hash:
python3 -c "from passlib.context import CryptContext; c=CryptContext(schemes=['bcrypt']); print(c.hash('your-password'))"
```

### 2. Run the Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Run the Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |

> Default login: `admin` / `aegis-admin`

### 4. Train the ML Model

```bash
# Generate training dataset (10,000 realistic logs with injected anomalies)
python3 backend/tools/generate_dataset.py

# Train Pipeline(StandardScaler → IsolationForest) — saves to model.joblib
python3 backend/train_model.py
```

### 5. Health Check

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
POST /api/v1/ingest/logs        # Structured JSON log(s) — single or batch
POST /api/v1/ingest/raw         # Raw syslog/plain-text log
```

### Dashboard (protected)
```http
GET /api/v1/dashboard/stats
GET /api/v1/dashboard/alerts
GET /api/v1/dashboard/incidents
GET /api/v1/dashboard/logs?query=<lucene>
```

### WebSocket Live Feed
```
wss://aegis-threat-platform.onrender.com/api/v1/ws/feed?token=<JWT>
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
│   │   │   ├── config.py         # Settings (env-driven, pydantic-settings v2)
│   │   │   ├── security.py       # JWT issuance + get_current_user dependency
│   │   │   └── limiter.py        # Per-IP rate limiter
│   │   ├── models/               # Pydantic models (LogEntry, etc.)
│   │   ├── response/             # YAML response policy
│   │   └── services/
│   │       ├── normalization.py  # Multi-source log parser (Nginx/SSH/UFW)
│   │       ├── detection_rules.py# Rule engine (Sigma-like)
│   │       ├── detection_ml.py   # ML pipeline with calibrated scaler
│   │       ├── correlation.py    # Multi-stage incident engine
│   │       ├── enrichment.py     # GeoIP & Threat Intel (ipinfo + AbuseIPDB)
│   │       ├── storage.py        # Elasticsearch 8.x client (basic_auth)
│   │       └── response.py       # Automated blocking (Redis + iptables)
│   ├── app/worker.py             # Stream consumer → pub/sub publisher
│   ├── tools/                    # Dataset generator, benchmarker, red-team simulator
│   ├── Dockerfile                # Python 3.11-slim image
│   └── train_model.py            # Pipeline(StandardScaler → IsolationForest) trainer
├── frontend/
│   ├── next.config.ts            # API proxy rewrites + standalone output
│   ├── vercel.json               # Vercel deployment config
│   └── app/
│       ├── page.tsx              # Dashboard (auth gate + WebSocket client)
│       └── components/
│           └── LoginForm.tsx     # JWT login form
├── nginx/
│   └── aegis.conf                # SSL termination + WebSocket upgrade config
├── tests/                        # 12-file test suite
├── .env.example                  # Secret template (commit this, NOT .env)
├── .github/workflows/ci-cd.yml  # CI: lint → build (Render & Vercel auto-deploy)
└── docker-compose.yml            # Local full-stack (ES, Redis, all services)
```

---

## 🚢 Cloud Deployment

### Backend → Render

1. Go to [render.com](https://render.com) → New Web Service → Connect `adhacks541/aegis-threat-platform`
2. Set **Root Directory** = `backend`, **Language** = `Docker`
3. Add environment variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD_HASH` | bcrypt hash of your password |
| `REDIS_URL` | `redis://:password@host:port` |
| `ELASTICSEARCH_URL` | Elastic Cloud endpoint |
| `ELASTICSEARCH_USERNAME` | `elastic` |
| `ELASTICSEARCH_PASSWORD` | Elastic Cloud password |
| `CORS_ORIGINS` | `https://your-vercel-app.vercel.app` |
| `IPINFO_TOKEN` | From [ipinfo.io](https://ipinfo.io/account) |
| `ABUSEIPDB_API_KEY` | From [abuseipdb.com](https://www.abuseipdb.com/account/api) |

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → Import `adhacks541/aegis-threat-platform`
2. Set **Root Directory** = `frontend`
3. Add environment variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://aegis-threat-platform.onrender.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://aegis-threat-platform.onrender.com` |

Every push to `main` automatically redeploys both services.

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

> **Note**: All APIs are secured via JWT. The test suite uses `tests/auth_helper.py` to auto-login.

```bash
cd backend && pip install pytest pytest-asyncio httpx
pytest ../tests/ -v --tb=short
```

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
- [x] **Cloud Deployment**: Render (backend) + Vercel (frontend) + Elastic Cloud + Redis Cloud
- [x] **CI/CD Pipeline**: GitHub Actions — lint, type-check, and build on every push
- [ ] Multi-Tenancy Support
- [ ] PDF Incident Report Export
- [ ] MITRE ATT&CK Framework Tagging

---

## 📜 License

MIT License. Open Source Security.

---
*Built with ❤️ for the modern SOC analyst.*