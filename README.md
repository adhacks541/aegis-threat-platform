# 🛡️ Aegis – Intelligent SIEM & Intrusion Detection System

**Aegis** is a next-generation Security Information and Event Management (SIEM) system geared towards modern threat detection. It combines traditional rule-based detection with unsupervised machine learning to identify both known attacks (Brute Force) and zero-day anomalies.

## 🚀 Features

- **🔥 Real-time Log Ingestion**: High-throughput ingestion via HTTP/Webhooks (FastAPI + Redis Streams).
- **🧠 Hybrid Detection Engine**:
    - **Rule-Based**: Instantly flags patterns like SSH Brute Force, Sudo failures, etc.
    - **ML-Based**: Uses *Isolation Forest* to detect anomalous traffic patterns (e.g., unusual payload sizes, off-hours activity) that bypass static rules.
- **🌍 Enrichment**: Automatically adds GeoIP context (Location, ISP) and User-Agent parsing to every log.
- **⚡ Async Architecture**: Fully decoupled ingestion and processing pipeline using Redis and Python workers.
- **📊 Modern Stack**: Built with Python 3.10+, FastAPI, Docker, Elasticsearch, and Redis.

## 🛠️ Tech Stack

- **Backend**: Python (FastAPI)
- **Queue**: Redis Streams
- **Database**: Elasticsearch (Log Storage), Redis (State/Caching)
- **ML**: Scikit-Learn (Isolation Forest)
- **DevOps**: Docker Compose

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local testing scripts)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/aegis-siem.git
   cd aegis-siem
   ```

2. **Start the Infrastructure**
   ```bash
   docker-compose up -d --build
   ```
   This will spin up:
   - `siem-backend` (API on port 8000)
   - `siem-worker` (Background processing)
   - `siem-elasticsearch` (DB)
   - `siem-kibana` (Visualizer on port 5601)
   - `siem-redis` (Queue)

3. **Train the Anomaly Model** (Initial Setup)
   Generate synthetic normal traffic to train the unsupervised model:
   ```bash
   docker-compose exec worker python train_model.py
   docker-compose restart worker
   ```

4. **Verify Functionality**
   Run the end-to-end test suite:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests
   python tests/test_detection.py
   ```
   You should see:
   - `SUCCESS: Rule Alert Found!`
   - `SUCCESS: ML Anomaly Detected!`

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # API Endpoints
│   │   ├── core/         # Config & Settings
│   │   ├── models/       # Pydantic Schemas
│   │   ├── services/     # Business Logic (Normalization, Enrichment, Detection)
│   │   └── worker.py     # Background Log Processor
│   ├── Dockerfile
│   └── train_model.py    # ML Training Script
├── tests/                # Verification Scripts
├── docker-compose.yml
└── README.md
```

## 🔮 Roadmap
- [x] Phase 1: Infrastructure & Ingestion
- [x] Phase 2: Log Storage (Elasticsearch)
- [x] Phase 3: Normalization & GeoIP Enrichment
- [x] Phase 4: Detection Engine (Rules + ML)
- [ ] Phase 5: Correlation Engine (Incident Generation)
- [ ] Phase 6: Threat Dashboard (Next.js)

## 📜 License
MIT
