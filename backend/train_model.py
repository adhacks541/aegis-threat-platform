import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
import os

DATASET_FILE = "backend/training_data.json"
MODEL_FILE = "model.joblib"

def train():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: Dataset {DATASET_FILE} not found. Run 'python3 -m backend.tools.generate_dataset' first.")
        return

    print("Loading dataset...")
    with open(DATASET_FILE, "r") as f:
        data = json.load(f)
    
    # Extract Features: [hour, msg_len, is_ssh, login_rate]
    # Filter out injected anomalies to train on "Normal" baseline only
    X = []
    for entry in data:
        if entry.get('is_injected_anomaly'):
            continue
            
        X.append([
            entry['hour'],
            entry['msg_len'],
            entry['is_ssh'],
            entry.get('login_rate', 0)
        ])
    
    X = np.array(X)
    print(f"Training Isolation Forest on {len(X)} records...")
    
    # Contamination = 0.05 (Assume 5% of training data might be anomalies/noise)
    clf = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
    clf.fit(X)
    
    joblib.dump(clf, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")

if __name__ == "__main__":
    train()
