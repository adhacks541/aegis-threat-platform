# 🧪 Aegis Simulation & Verification Guide

This guide explains how to simulate real-world cyber attacks on the Aegis platform and verify that the detection engines (Rule-based, ML, and Correlation) are working correctly.

---

## 🛠️ Prerequisites

1.  **System Running**: Ensure the full stack is running (Docker is recommended).
    ```bash
    docker compose up --build -d
    ```
2.  **ML Model Trained**: The ML anomaly detection engine requires a trained model.
    ```bash
    # Generate 10k logs and train the Isolation Forest model
    python3 backend/tools/generate_dataset.py
    python3 backend/train_model.py
    ```

---

## 🚀 Scenario 1: Live Dashboard Simulation
Use this to "light up" the SOC dashboard with live traffic, alerts, and incidents.

### Run the Simulator:
```bash
python3 backend/tools/simulate_dashboard_traffic.py
```

### What happens:
1.  **Normal Traffic**: Sends 50 Nginx logs. You'll see the "Total Logs" count rise and the log stream moving.
2.  **SSH Brute Force**: Sends 6 failed login attempts. An alert will pop up in the **Alerts** tab and the "Active Alerts" stat will increase.
3.  **Complex Attack**: Sends a correlated attack chain (Brute Force → Successful Login → Sudo Execution). This will trigger a **Critical Incident** in the incidents table.

---

## 🔍 Scenario 2: Technical Full-System Verification
Use this script to programmatically verify that every layer of the platform (FastAPI, Redis, Elasticsearch, Workers) is communicating perfectly.

### Run the Verification:
```bash
python3 backend/tools/verify_full_system.py
```

### Checks Performed:
-   **SSH Brute Force (Rule)**: Verifies that 6+ failures trigger an alert in Elasticsearch.
-   **Suspicious Admin (Block)**: Verifies that an admin login from a new IP triggers a block in Redis.
-   **ML Anomaly (Machine Learning)**: Verifies that high-frequency requests are flagged as `ml_anomaly: true`.
-   **Correlation (Incident)**: Verifies that a multi-stage attack is correctly grouped into a single high-priority Incident.

---

## 📊 How to Observe Results

### 1. The SOC Dashboard (Visual)
Open [http://localhost:3000](http://localhost:3000) and login.
-   **Overview Tab**: Watch the "Real-time Attack Feed" and stat cards.
-   **Incidents Tab**: Check the "Security Incidents" table for correlated attack chains.
-   **Logs Tab**: View the raw logs being ingested and parsed.

### 2. API Documentation (Technical)
Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive Swagger UI and test ingestion endpoints manually.

### 3. Elasticsearch (Data Layer)
If you have Kibana or a local ES instance running:
-   `logs-*`: Raw normalized logs.
-   `alerts-*`: Individual security alerts.
-   `incidents-*`: Correlated attack incidents.

---

## 🛡️ Troubleshooting Simulation

-   **Backend Unreachable**: Ensure `http://localhost:8000` is active.
-   **No Alerts**: Check if the worker container is running (`docker compose logs -f worker`).
-   **No ML Anomalies**: Ensure `model.joblib` exists in the `backend/` root after running `train_model.py`.
