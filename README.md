# 🛡️ Aegis – Intelligent SIEM & Threat Response Platform

> **[📖 Project Explanation](project_explanation.md)** | **[🧪 Testing Guide](testing_guide.md)**


**Aegis** is a production-grade Security Information and Event Management (SIEM) system built for modern threat detection. It unifies high-performance log ingestion, rule-based detection, unsupervised machine learning, and automated incident response into a single, scalable platform.

![SOC Dashboard](dashboard_preview.png)

## 🚀 Key Features

### 🧠 Advanced Detection Engine
- **Hybrid Detection**: Combines traditional **Sigma-like rules** (for known threats like SSH Brute Force) with **Isolation Forest ML models** (for zero-day anomalies).
- **Correlation Engine**: Stateful tracking of multi-stage attacks (e.g., Brute Force → Successful Login → Privilege Escalation) using Redis.
- **Explainable AI**: Every ML anomaly comes with a human-readable explanation (e.g., "Anomalous Time of Day", "Unusual Message Size").

### 🛡️ Automated Response (SOAR)
- **Active Defense**: Automatically blocks IPs triggering Critical alerts or high risk scores (> 80).
- **Dynamic Risk Scoring**: Calculates risk based on Alert Severity + ML Confidence + Correlation Context.
- **Fail-Safes**: Built-in whitelisting and auto-expiration of blocks to prevent self-lockout.

### 📊 SOC Dashboard
- **Real-Time Monitoring**: Live feed of Logs, Alerts, and Incidents via modern Next.js UI.
- **Cyberpunk Experience**: A fully immersive, sci-fi themed interface with holographic effects, retro-terminal logs, and real-time system status indicators.
- **Investigation**: Deep dive into raw logs with enrichment context (GeoIP, User-Agent).
- **Incident Management**: Track correlated attack chains.

### ⚡ High-Performance Architecture
- **Ingestion**: FastAPI + Redis Streams for buffering high-throughput traffic.
- **Enrichment**: Asynchronous Worker pipeline adds Context (GeoIP, Threat Intel) to every log.
- **Storage**: Elasticsearch with Index Lifecycle Management (ILM) for efficient hot-warm-cold storage.

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React, Tailwind | SOC Dashboard |
| **Backend API** | Python (FastAPI) | Log Ingestion & Query API |
| **Processing** | Python Async Workers | ETL, Detection, Correlation |
| **Stream Buffer** | Redis Streams | Decouples ingestion from processing |
| **State Store** | Redis | Risk scoring, Session tracking, Blocking |
| **Log Storage** | Elasticsearch 8.x | Search & Analytics |
| **ML** | Scikit-Learn | Unsupervised Anomaly Detection |

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for verification scripts)
- Node.js 18+ (for frontend development)

### 1. Launch the Stack
```bash
# Start all services (Backend, Frontend, DBs)
docker-compose up -d --build
```
- **Dashboard**: [http://localhost:3000](http://localhost:3000) (Default)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Kibana**: [http://localhost:5601](http://localhost:5601)

### 2. Initialize System
Set up Elasticsearch templates and indices:
```bash
docker-compose exec worker python tools/setup_elasticsearch.py
```

### 3. Verify Functionality (Full System Check)
Run the automated verification suite to simulation attacks:
```bash
docker-compose exec worker python tools/verify_full_system.py
```
This script acts as a **Red Team** simulator, launching:
- **SSH Brute Force**: Triggers Rule Engine.
- **Suspicious Admin**: Triggers Manual Logic & Blocking.
- **Data Exfiltration**: Triggers ML Anomaly Detection.
- **Privilege Escalation**: Triggers Correlation Engine.

You should see **✅ PASS** for all checks.

### 4. Performance Benchmarking
Test the high-throughput ingestion pipeline (Redis Streams + FastAPI):
```bash
python backend/tools/benchmark_ingest.py
```
This script validates the system's ability to handle **>5,000 Events Per Second (EPS)**.

### 5. API Health Check
Verify the operational status of the backend services:
```bash
curl http://localhost:8000/health
```
Expected output: `{"status": "healthy", "services": {"api": "online"}}`
## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes (Ingest, Dashboard)
│   │   ├── services/     # Core Logic:
│   │   │   ├── detection_rules.py  # Rule Engine
│   │   │   ├── detection_ml.py     # ML Engine
│   │   │   ├── correlation.py      # Incident Engine
│   │   │   └── response.py         # Automated Blocking
│   │   └── worker.py     # Main Async Processor
│   ├── rules/            # Detection Config (YAML)
│   ├── tools/            # Verification & Simulation Scripts
│   └── train_model.py    # ML Training Pipeline
├── frontend/             # Next.js Dashboard
├── docker-compose.yml
└── README.md
```

## 🔮 Roadmap Overview
- [x] **Phase 1-4**: Infrastructure, Ingestion, & Basic Detection
- [x] **Phase 5**: Correlation Engine (Multi-stage attacks)
- [x] **Phase 6**: SOC Dashboard (Frontend)
- [x] **Phase 10-15**: ML Anomaly Detection & Auto-Response
- [x] **Phase 17**: Full System Verification & Production Hardening
- [x] **Phase 18**: UI/UX Overhaul Prototyping (Dark Cyberpunk Aesthetic generated via Google Stitch)
- [ ] **Phase 18+**:
    - [x] Integrated Threat Intelligence Feeds (VirusTotal, AlienVault)
    - [ ] Multi-Tenancy Support
    - [ ] PDF Reporting Module

## 📜 License
MIT License. Open Source Security.

---
*Built with ❤️ by the Aegis Team.*