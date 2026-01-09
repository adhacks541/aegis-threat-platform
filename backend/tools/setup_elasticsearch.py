import os
import requests
import json
import time

# Configuration
ES_HOST = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

# ILM Policies
POLICIES = {
    "siem_logs_policy": {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_size": "50gb",
                            "max_age": "1d"
                        }
                    }
                },
                "delete": {
                    "min_age": "7d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    },
    "siem_alerts_policy": {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_size": "50gb",
                            "max_age": "30d"
                        }
                    }
                },
                "delete": {
                    "min_age": "30d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    },
    "siem_incidents_policy": {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_size": "50gb",
                            "max_age": "30d"
                        }
                    }
                },
                "delete": {
                    "min_age": "90d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }
}

# Index Templates
TEMPLATES = {
    "siem_logs_template": {
        "index_patterns": ["logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "siem_logs_policy",
                "index.lifecycle.rollover_alias": "logs-write"
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "ip": {"type": "ip"},
                    "location": {"type": "geo_point"}
                }
            }
        }
    },
    "siem_alerts_template": {
        "index_patterns": ["alerts-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "siem_alerts_policy",
                "index.lifecycle.rollover_alias": "alerts-write"
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "severity": {"type": "keyword"},
                    "rule_name": {"type": "keyword"}
                }
            }
        }
    },
    "siem_incidents_template": {
        "index_patterns": ["incidents-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "siem_incidents_policy",
                "index.lifecycle.rollover_alias": "incidents-write"
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "status": {"type": "keyword"}
                }
            }
        }
    }
}

def setup_ilm():
    print(f"Connecting to Elasticsearch at {ES_HOST}...")
    
    # Wait for ES
    for _ in range(30):
        try:
            r = requests.get(ES_HOST)
            if r.status_code == 200:
                print("Connected to Elasticsearch.")
                break
        except:
            print("Waiting for Elasticsearch...")
            time.sleep(2)
    else:
        print("Could not connect to Elasticsearch.")
        return

    # 1. Create Policies
    print("\n--- Creating ILM Policies ---")
    for name, body in POLICIES.items():
        r = requests.put(f"{ES_HOST}/_ilm/policy/{name}", json=body, headers={"Content-Type": "application/json"})
        print(f"Policy {name}: {r.status_code} - {r.text}")

    # 2. Create Templates
    print("\n--- Creating Index Templates ---")
    for name, body in TEMPLATES.items():
        r = requests.put(f"{ES_HOST}/_index_template/{name}", json=body, headers={"Content-Type": "application/json"})
        print(f"Template {name}: {r.status_code} - {r.text}")

    # 3. Bootstrap Initial Indices (If not exist)
    # We must create the first index manually with the alias IS_WRITE_INDEX=true so ILM can take over
    print("\n--- Bootstrapping Indices ---")
    
    bootstraps = [
        ("logs-000001", "logs-write"),
        ("alerts-000001", "alerts-write"),
        ("incidents-000001", "incidents-write")
    ]
    
    for index, alias in bootstraps:
        # Check if alias exists
        r = requests.head(f"{ES_HOST}/{alias}")
        if r.status_code == 200:
            print(f"Alias {alias} already exists. Skipping bootstrap.")
            continue
            
        # Create index with alias
        body = {
            "aliases": {
                alias: {
                    "is_write_index": True
                }
            }
        }
        r = requests.put(f"{ES_HOST}/{index}", json=body, headers={"Content-Type": "application/json"})
        print(f"Bootstrap {index} -> {alias}: {r.status_code} - {r.text}")

if __name__ == "__main__":
    setup_ilm()
