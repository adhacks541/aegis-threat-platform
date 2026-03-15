# 🛡️ Aegis – Intelligent SIEM & Threat Response Platform

> **[📖 Project Explanation](project_explanation.md)** | **[🧪 Testing Guide](testing_guide.md)**


**Aegis** is a production-grade Security Information and Event Management (SIEM) system built for modern threat detection. It unifies high-performance log ingestion, rule-based detection, unsupervised machine learning, and automated incident response into a single, scalable platform.

![SOC Dashboard](dashboard_preview.png)

## 🚀 Key Features

### 🧠 Advanced Detection Engine
- **Hybrid Detection**: Combines traditional **Sigma-like rules** (for known threats like SSH Brute Force) with **Isolation Forest ML models** (for zero-day anomalies).
- **Correlation Engine**: Stateful tracking of multi-stage attacks (e.g., Brute Force → Successful Login → Privilege Escalation) using Redis.
- **Explainable AI**: Every ML anomaly comes with a human-readable explanation (e.g., "Anomalous Time of Day", "Unusual Message Size").

### 🔍 Multi-Source Log Normalization
- **Nginx**: Full request parsing (IP, method, path, status, bytes, user-agent, referrer).
- **SSH**: Distinguishes `Failed password` vs `Accepted password` events, extracts attacker IP and username.
- **UFW Firewall**: Parses `[UFW BLOCK]` events with source/destination IP and protocol.
- **Extensible**: Regex-based `NormalizationService` makes it trivial to add new log sources.

### 🛡️ Automated Response (SOAR)
- **Active Defense**: Automatically blocks IPs triggering Critical alerts or high risk scores (> 80).
- **Dynamic Risk Scoring**: Calculates risk based on Alert Severity + ML Confidence + Correlation Context.
- **Fail-Safes**: Built-in whitelisting and auto-expiration of blocks to prevent self-lockout.
- **Response Config**: YAML-driven response policy (`response_config.yaml`) for customizable thresholds and actions.

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

### 3. Train the ML Model
Generate a realistic training dataset and train the Isolation Forest model:
```bash
# Generate 10,000 logs with Zipfian IP distribution + injected attack anomalies
python backend/tools/generate_dataset.py

# Train the Isolation Forest model on the generated dataset
python backend/train_model.py
```

### 4. Verify Functionality (Full System Check)
Run the automated verification suite to simulate attacks:
```bash
docker-compose exec worker python tools/verify_full_system.py
```
This script acts as a **Red Team** simulator, launching:
- **SSH Brute Force**: Triggers Rule Engine.
- **Suspicious Admin**: Triggers Manual Logic & Blocking.
- **Data Exfiltration**: Triggers ML Anomaly Detection.
- **Privilege Escalation**: Triggers Correlation Engine.

You should see **✅ PASS** for all checks.

### 5. Performance Benchmarking
Test the high-throughput ingestion pipeline (Redis Streams + FastAPI):
```bash
python backend/tools/benchmark_ingest.py
```
This script validates the system's ability to handle **>5,000 Events Per Second (EPS)**.

### 6. API Health Check
Verify the operational status of the backend services:
```bash
curl http://localhost:8000/health
```
Expected output: `{"status": "healthy", "services": {"api": "online"}}`

## 🧪 Test Suite

Aegis ships with a comprehensive test suite covering every layer of the platform:

| Test File | Coverage Area |
| :--- | :--- |
| `test_detection.py` | ML & Rule-based detection |
| `test_detection_rules.py` | Sigma-like rule engine unit tests |
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

Run any test directly:
```bash
python tests/test_response_automation.py
```

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes (Ingest, Dashboard)
│   │   ├── core/         # Core Config & Settings
│   │   ├── models/       # Pydantic Data Models (LogEntry, etc.)
│   │   ├── response/     # Response Policy Config (YAML)
│   │   ├── services/     # Core Logic:
│   │   │   ├── normalization.py    # Multi-source Log Parser
│   │   │   ├── detection_rules.py  # Rule Engine
│   │   │   ├── detection_ml.py     # ML Engine (Isolation Forest)
│   │   │   ├── correlation.py      # Incident Engine
│   │   │   ├── enrichment.py       # GeoIP & Threat Intel
│   │   │   └── response.py         # Automated Blocking
│   │   └── worker.py     # Main Async Processor
│   ├── tools/            # Verification, Simulation & Dataset Scripts
│   │   ├── generate_dataset.py     # ML Training Data Generator
│   │   ├── benchmark_ingest.py     # EPS Benchmarking
│   │   └── verify_full_system.py   # Red Team Simulator
│   └── train_model.py    # ML Training Pipeline
├── tests/                # Full Test Suite (12 test files)
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
- [x] **Phase 18+**:
    - [x] Integrated Threat Intelligence Feeds (VirusTotal, AlienVault)
    - [x] Multi-Source Log Normalization (Nginx, SSH, UFW Firewall)
    - [x] Comprehensive Test Suite (12 test files, full coverage)
    - [x] ML Training Dataset Generator (Zipfian distribution + anomaly injection)
    - [ ] Multi-Tenancy Support
    - [ ] PDF Reporting Module

## 📜 License
MIT License. Open Source Security.

---
*Built with ❤️ by the Aegis Team.*