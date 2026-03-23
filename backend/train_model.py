import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import os

DATASET_FILE = "backend/training_data.json"
MODEL_FILE = "model.joblib"


def train():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: Dataset {DATASET_FILE} not found.")
        return

    print("Loading dataset...")
    with open(DATASET_FILE, "r") as f:
        data = json.load(f)

    # Extract Features: [hour, msg_len, is_ssh, login_rate]
    # Train only on normal records so the Isolation Forest learns a clean baseline.
    X = []
    for entry in data:
        if entry.get("is_injected_anomaly"):
            continue
        X.append([
            entry["hour"],
            entry["msg_len"],
            entry["is_ssh"],
            entry.get("login_rate", 0),
        ])

    X = np.array(X)
    print(f"Training on {len(X)} normal records…")

    # Pipeline: StandardScaler → IsolationForest
    # The scaler is now saved INSIDE the pipeline so predict() will always use
    # the correct feature statistics — no more hard-coded means.
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("iforest", IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X)
    joblib.dump(pipeline, MODEL_FILE)
    print(f"Pipeline (scaler + model) saved to {MODEL_FILE}")

    # Print learned scaler statistics for audit
    scaler: StandardScaler = pipeline.named_steps["scaler"]
    names = ["Hour", "MsgLen", "IsSSH", "LoginRate"]
    for name, mean, std in zip(names, scaler.mean_, scaler.scale_):
        print(f"  {name}: mean={mean:.2f}, std={std:.2f}")


if __name__ == "__main__":
    train()
