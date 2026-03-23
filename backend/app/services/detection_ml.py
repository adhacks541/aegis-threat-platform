import joblib
import numpy as np
import os
import redis
import logging
from app.core.config import settings
from typing import Dict, Any
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

MODEL_PATH = "model.joblib"


class MLDetector:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.model: Pipeline | None = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info("ML pipeline (scaler + IsolationForest) loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                self.model = None
        else:
            logger.warning(f"ML model not found at {MODEL_PATH}. Prediction disabled.")

    def get_login_rate(self, ip: str) -> int:
        """Get approximate request rate for IP from Redis."""
        if not ip:
            return 0
        val = self.redis.get(f"rate_limit:{ip}")
        return int(val) if val else 0

    def predict(self, log_entry: dict) -> Dict[str, Any]:
        """Returns {score: float, explanation: str | None}"""
        if not self.model:
            return {"score": 0.0, "explanation": "Model not loaded"}

        try:
            # Feature extraction
            msg_len = len(log_entry.get("message", ""))

            timestamp = log_entry.get("timestamp", "")
            hour = 12
            if "T" in timestamp:
                try:
                    hour = int(timestamp.split("T")[1].split(":")[0])
                except Exception:
                    pass

            is_ssh = 1 if "ssh" in log_entry.get("source", "").lower() else 0

            ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
            login_rate = self.get_login_rate(ip)

            features = np.array([[hour, msg_len, is_ssh, login_rate]])

            # Pipeline contains scaler → IsolationForest.
            # decision_function: positive = normal, negative = anomaly.
            raw_score = self.model.decision_function(features)[0]

            # Normalise to 0..1 (anomaly probability proxy)
            if raw_score < 0:
                anomaly_score = min(0.5 + abs(raw_score) * 2, 1.0)
            else:
                anomaly_score = max(0.5 - raw_score * 2, 0.0)

            explanation = None
            if anomaly_score > 0.6:
                explanation = self._explain_anomaly(features[0])

            return {
                "score": round(anomaly_score, 2),
                "explanation": explanation,
            }

        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return {"score": 0.0, "explanation": "Error"}

    def _explain_anomaly(self, raw_features: np.ndarray) -> str:
        """
        Use the pipeline's scaler to compute per-feature Z-scores and
        highlight the feature with the largest deviation.
        """
        try:
            scaler = self.model.named_steps["scaler"]
            z_scores = np.abs((raw_features - scaler.mean_) / (scaler.scale_ + 1e-9))
        except Exception:
            z_scores = np.zeros(4)

        names = ["Time of Day", "Message Size", "Protocol (SSH)", "Request Frequency"]
        top_idx = int(np.argmax(z_scores))
        return f"Anomalous {names[top_idx]} detected (z={z_scores[top_idx]:.1f})"


ml_detector = MLDetector()
