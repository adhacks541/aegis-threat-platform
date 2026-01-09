import joblib
import numpy as np
import os
import redis
import logging
from app.core.config import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)

MODEL_PATH = "model.joblib"

class MLDetector:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.model = None
        self.features_mean = np.array([12, 50, 0, 5]) # Approximate means for [hour, len, ssh, freq] due to lack of scaler
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info("ML Model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                self.model = None
        else:
            logger.warning(f"ML Model not found at {MODEL_PATH}. Prediction will be disabled.")

    def get_login_rate(self, ip: str) -> int:
        """Get approximate request rate for IP in last minute."""
        if not ip: return 0
        # utilizing the keys set by RateLimiter or creating new ones?
        # Let's use the 'rate_limit:{ip}' key from RateLimiter if available, or just fallback to 0
        # Actually, RateLimiter uses `rate_limit:{ip}`.
        val = self.redis.get(f"rate_limit:{ip}")
        return int(val) if val else 0

    def predict(self, log_entry: dict) -> Dict[str, Any]:
        """
        Returns {score: float, explanation: str}
        """
        if not self.model:
            return {"score": 0.0, "explanation": "Model not loaded"}

        try:
            # Feature Extraction
            # 1. Message Length
            msg_len = len(log_entry.get("message", ""))
            
            # 2. Hour
            timestamp = log_entry.get("timestamp", "")
            hour = 12
            if "T" in timestamp:
                try: hour = int(timestamp.split("T")[1].split(":")[0])
                except: pass
            
            # 3. Is SSH
            is_ssh = 1 if "ssh" in log_entry.get("source", "").lower() else 0
            
            # 4. Login Rate (Real-time from Redis)
            ip = log_entry.get("ip") or log_entry.get("metadata", {}).get("ip")
            login_rate = self.get_login_rate(ip)

            # Vector: [hour, msg_len, is_ssh, login_rate]
            features = np.array([[hour, msg_len, is_ssh, login_rate]])
            
            # Prediction
            raw_score = self.model.decision_function(features)[0]
            
            # Normalize to 0..1 (approx)
            # decision_function: positive (normal), negative (outlier)
            anomaly_score = 0.0
            if raw_score < 0:
                anomaly_score = 0.5 + (abs(raw_score) * 2)
                anomaly_score = min(anomaly_score, 1.0)
            else:
                anomaly_score = 0.5 - (raw_score * 2)
                anomaly_score = max(anomaly_score, 0.0)

            explanation = None
            if anomaly_score > 0.6:
                explanation = self._explain_anomaly(features[0])

            return {
                "score": round(anomaly_score, 2),
                "explanation": explanation
            }

        except Exception as e:
            logger.error(f"ML Prediction Error: {e}")
            return {"score": 0.0, "explanation": "Error"}

    def _explain_anomaly(self, features):
        """
        Simple heuristic: Find feature with biggest deviation from 'normal' mean.
        Features: 0:Hour, 1:Len, 2:SSH, 3:Freq
        """
        # Define rough 'normal' baselines (hardcoded or learned)
        # In a real system, we'd save scaler.mean_ from the training phase.
        means = [14, 60, 0, 5] 
        stds = [4, 20, 1, 5] 
        names = ["Time of Day", "Message Size", "Protocol", "Request Frequency"]
        
        max_dev = 0
        top_feature = "Unknown"
        
        for i in range(4):
            dev = abs(features[i] - means[i]) / (stds[i] + 0.1)
            if dev > max_dev:
                max_dev = dev
                top_feature = names[i]
                
        return f"Anomalous {top_feature} detected"

ml_detector = MLDetector()
