import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from datetime import datetime

MODEL_PATH = "model.joblib"

class MLDetector:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                print("ML Model loaded successfully.")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print("No ML model found. Training checks will be skipped until trained.")

    def _extract_features(self, log_entry: dict):
        """
        Extract numerical features for the model.
        Features: [hour_of_day, log_level_int, message_length, source_int]
        This is a VERY basic vectorizer for demonstration.
        """
        try:
            # Timestamp hour
            ts = log_entry.get('timestamp')
            if isinstance(ts, str):
                # Handle isoformat strings roughly
                if 'T' in ts:
                    hour = int(ts.split('T')[1].split(':')[0])
                else:
                    hour = 12 
            elif isinstance(ts, datetime):
                hour = ts.hour
            else:
                hour = 12

            # Level mapping
            level = log_entry.get('level', 'INFO').upper()
            level_map = {'DEBUG': 0, 'INFO': 1, 'WARN': 2, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
            lvl_val = level_map.get(level, 1)

            # Message Length
            msg_len = len(log_entry.get('message', ''))

            # Source Mapping (simple hash or basic int map)
            src = log_entry.get('source', '')
            src_val = hash(src) % 100

            return [hour, lvl_val, msg_len, src_val]
        except:
            return [0, 0, 0, 0]

    def train_initial_model(self):
        """
        Train on synthetic normal data.
        """
        print("Training initial ML model...")
        # Generate synthetic 'normal' data
        # Normal: Info logs, office hours (9-17), medium length
        X_train = []
        for _ in range(1000):
            hour = np.random.randint(9, 18)
            lvl = 1 # INFO
            msg_len = np.random.normal(50, 10)
            src = hash("nginx") % 100
            X_train.append([hour, lvl, msg_len, src])
        
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(X_train)
        
        joblib.dump(clf, MODEL_PATH)
        self.model = clf
        print("Model trained and saved.")

    def predict(self, log_entry: dict):
        """
        Returns anomaly score. -1 is anomaly, 1 is normal.
        """
        if not self.model:
            return 1 # Default to normal if no model
        
        features = self._extract_features(log_entry)
        prediction = self.model.predict([features])[0]
        return prediction

ml_detector = MLDetector()
