# 🛡️ Aegis – Intelligent SIEM & Threat Response Platform

> **[📖 Project Explanation](project_explanation.md)** | **[🧪 Testing Guide](testing_guide.md)**

**Aegis** is a production-grade Security Information and Event Management (SIEM) system built for modern threat detection. It unifies high-performance log ingestion, rule-based detection, unsupervised machine learning, real-time WebSocket streaming, Clerk-authenticated access control, automated incident response, and a standalone-capable SOC dashboard into a single, fully deployable platform.

![SOC Dashboard](dashboard_preview.png)

---

## 🌐 Live Deployment

| Service | URL | Platform |
|:--------|:----|:---------|
| **SOC Dashboard** | [aegis-threat-platform.vercel.app](https://aegis-threat-platform-git-main-adhacks541s-projects.vercel.app) | Vercel |
| **Backend API** | [aegis-threat-platform.onrender.com](https://aegis-threat-platform.onrender.com) | Render |
| **API Docs** | [aegis-threat-platform.onrender.com/docs](https://aegis-threat-platform.onrender.com/docs) | Render |

> **Authentication:** Clerk-managed (Google, GitHub, Apple, or email sign-in). Access is restricted to allowlisted emails via server-side enforcement.
> 
> ⚠️ Free Render tier sleeps after 15 min of inactivity — first request may take ~30s to wake up.
> 
> 💡 **Standalone Mode:** If the backend is offline, the dashboard still renders with a subtle amber banner — the Vercel deployment is always presentable.

---

## 🚀 Key Features

### 🔐 Clerk Authentication + Server-Side Access Control
- **Clerk Integration**: Social logins (Google, GitHub, Apple) + email/password via `@clerk/nextjs` — replaces custom credential management.
- **Token Exchange Flow**: Clerk JWT → `POST /api/v1/auth/clerk` → verified via Clerk JWKS (RS256) → internal backend JWT issued.
- **Email Allowlist**: Server-side enforcement via `ALLOWED_EMAILS` — the backend fetches the user's verified primary email from Clerk's Backend API and checks it before issuing a token. Unauthorized users get a styled **ACCESS DENIED** page.
- **Custom Sign-In Page**: Dark cybersecurity-themed Clerk `<SignIn />` component with comprehensive dark mode overrides at `/sign-in`.
- **Backward Compatible**: The legacy `POST /api/v1/auth/token` (username/password) endpoint still works for API access and testing.

### 🧠 Advanced Detection Engine
- **Hybrid Detection**: Combines traditional **Sigma-like rules** (SSH brute-force, firewall blocks) with an **Isolation Forest ML pipeline** for zero-day anomaly detection.
- **Calibrated ML**: Model is a `sklearn.Pipeline(StandardScaler → IsolationForest)` — feature scaling is learned from data and persisted in `model.joblib`, eliminating hardcoded guesses.
- **Explainable AI**: Every ML anomaly includes a real Z-score explanation (e.g., `"Anomalous Request Frequency (z=4.2)"`).
- **Correlation Engine**: Stateful multi-stage attack detection (Brute Force → Successful Login → Privilege Escalation) using Redis.

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
- **Clerk Auth Gate**: Social sign-in with custom dark-themed UI before any data is visible.
- **Standalone Mode**: Dashboard renders even when backend is offline — shows empty state with amber `⚠ BACKEND OFFLINE` banner instead of crashing.
- **Live Incident Tracker**: Real-time table of correlated attack chains.
- **Alerts & Logs tabs**: Instantly updated via WebSocket — no page refresh needed.

### 🔍 Multi-Source Log Normalization
- **Nginx**: Full request parsing (IP, method, path, status, bytes, user-agent, referrer).
- **SSH**: Distinguishes `Failed password` vs `Accepted password`; extracts attacker IP and username.
- **UFW Firewall**: Parses `[UFW BLOCK]` events with source/destination IP and protocol.
- **Extensible**: Regex-based `NormalizationService` — add new log sources in minutes.

---

## 🔑 Authentication Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      USER FLOW                                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  User visits aegis.vercel.app                                 │
│       ↓                                                       │
│  Clerk middleware → redirect to /sign-in                      │
│       ↓                                                       │
│  Clerk <SignIn /> (Google / GitHub / email)                    │
│       ↓                                                       │
│  Frontend: getToken() → Clerk JWT                             │
│       ↓                                                       │
│  POST /api/v1/auth/clerk { Authorization: Bearer <jwt> }      │
│       ↓                                                       │
│  Backend: Verify JWT via Clerk JWKS (RS256, 5-min cache)      │
│       ↓                                                       │
│  Backend: Fetch user email from Clerk Backend API             │
│       ↓                                                       │
│  Check email ∈ ALLOWED_EMAILS                                 │
│       ↓                              ↓                        │
│  ✅ Issue internal JWT          ❌ 403 → /unauthorized         │
│       ↓                                                       │
│  All dashboard API calls use internal JWT                     │
└───────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4 | SOC Dashboard + Clerk Auth UI |
| **Authentication** | Clerk (`@clerk/nextjs`) + JWKS verification | Social login, access control, email allowlist |
| **Backend API** | Python 3.11, FastAPI | Log Ingestion, REST API, WebSocket |
| **Token System** | python-jose (JWT) + Clerk JWKS (RS256) | Stateless authentication (internal + Clerk) |
| **Processing** | Python async workers | ETL, Detection, Correlation |
| **Stream Buffer** | Redis Streams | Decouples ingestion from processing |
| **Pub/Sub** | Redis pub/sub | Worker → WebSocket fan-out |
| **State Store** | Redis Cloud | Risk scoring, blocking, rate limiting |
| **Log Storage** | Elasticsearch 8.x (Elastic Cloud) | Search & Analytics |
| **ML** | Scikit-Learn (Pipeline + IsolationForest) | Calibrated anomaly detection |
| **Frontend Hosting** | Vercel | Auto-deploy from `main` branch |
| **Backend Hosting** | Render (Docker) | Auto-deploy from `main` branch |
| **CI/CD** | GitHub Actions | Lint → Type-check → Build on every push |

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

# Clerk keys (from clerk.com → your app → API Keys):
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json

# Email allowlist (comma-separated):
ALLOWED_EMAILS=you@gmail.com,teammate@company.com
```

### 2. Run with Docker Compose

```bash
docker compose up --build -d
```

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **Kibana** | http://localhost:5601 |

### 3. Run Frontend Standalone (development)

```bash
cd frontend
cp .env.local.example .env.local   # Add your Clerk publishable key
npm install
npm run dev
```

Required `frontend/.env.local`:
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

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

### Auth — Clerk Token Exchange (primary)
```http
POST /api/v1/auth/clerk
Authorization: Bearer <clerk-jwt>

→ { "access_token": "...", "token_type": "bearer", "email": "user@example.com" }
```
Verifies Clerk JWT via JWKS, checks email allowlist, returns internal JWT.

### Auth — Legacy Password Flow
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin

→ { "access_token": "...", "token_type": "bearer" }
```

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
│   │   │   ├── auth.py           # POST /auth/token + POST /auth/clerk
│   │   │   ├── ingest.py         # POST /ingest/*    (rate-limited, JWT-guarded)
│   │   │   ├── dashboard.py      # GET  /dashboard/* (JWT-guarded, ES 8.x)
│   │   │   └── feed.py           # WS   /ws/feed     (real-time pub/sub)
│   │   ├── core/
│   │   │   ├── config.py         # Settings (env-driven, pydantic-settings v2)
│   │   │   ├── security.py       # JWT issuance + Clerk JWKS verification
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
│   ├── middleware.ts             # Clerk route protection (public: /sign-in, /sign-up)
│   ├── next.config.ts            # API proxy rewrites + standalone output
│   ├── vercel.json               # Vercel deployment config
│   └── app/
│       ├── layout.tsx            # ClerkProvider + dark theme globals
│       ├── page.tsx              # Dashboard (Clerk auth gate + WebSocket client)
│       ├── sign-in/
│       │   └── [[...sign-in]]/page.tsx  # Custom dark Clerk sign-in page
│       ├── unauthorized/
│       │   └── page.tsx          # ACCESS DENIED page for non-allowlisted users
│       └── components/
│           └── LoginForm.tsx     # Legacy JWT login form (backup)
├── nginx/
│   └── aegis.conf                # SSL termination + WebSocket upgrade config
├── tests/                        # 12-file test suite
├── .env.example                  # Secret template (commit this, NOT .env)
├── .github/workflows/ci-cd.yml  # CI: lint → type-check → build
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
| `CLERK_SECRET_KEY` | From [clerk.com](https://clerk.com) → API Keys |
| `CLERK_JWKS_URL` | `https://your-app.clerk.accounts.dev/.well-known/jwks.json` |
| `ALLOWED_EMAILS` | Comma-separated list of authorized emails |
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
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_test_...` from Clerk dashboard |
| `CLERK_SECRET_KEY` | `sk_test_...` from Clerk dashboard |
| `NEXT_PUBLIC_API_URL` | `https://aegis-threat-platform.onrender.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://aegis-threat-platform.onrender.com` |

> **CORS**: The backend automatically allows all `*.vercel.app` origins via `allow_origin_regex`. No manual CORS URL updates needed for Vercel preview deployments.

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
- [x] **Clerk Authentication**: Social login (Google/GitHub/Apple) + email allowlist
- [x] **Server-Side Access Control**: Clerk JWKS verification + email allowlist enforcement
- [x] **Real-Time WebSocket Feed**: Redis pub/sub → browser (zero polling)
- [x] **Calibrated ML Scaler**: StandardScaler persisted in pipeline
- [x] **Real iptables Enforcement**: TTL-synced block/unblock cycle
- [x] **CORS Wildcard**: `allow_origin_regex` for all Vercel preview URLs
- [x] **Standalone Mode**: Dashboard renders offline with backend-down banner
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