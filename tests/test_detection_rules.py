from app.services.detection_rules import rule_detector
import redis
from app.core.config import settings

def test_rules():
    print("\n--- Testing Rule-Based Detection ---")
    
    # Reset Redis for clean state
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    r.delete("state:admin_ips:admin")
    
    # 1. Test Sudo
    print("1. Testing Sudo Detection...")
    log_sudo = {"message": "sudo apt-get install crackmapexec"}
    alerts = rule_detector.check_rules(log_sudo)
    if "Suspicious Sudo Command Detection" in alerts:
        print("   SUCCESS: Sudo detected.")
    else:
        print(f"   FAILED: Alerts found: {alerts}")
        
    # 2. Test Suspicious Admin (First Login = Alert + Learn)
    print("2. Testing Suspicious Admin (New IP)...")
    log_admin = {
        "user": "admin", 
        "ip": "1.2.3.4", 
        "event_type": "ssh_login_success"
    }
    alerts = rule_detector.check_rules(log_admin)
    
    # First time: Should Alert (because 1.2.3.4 is new)
    found = any("Suspicious Admin Login (New IP)" in a for a in alerts)
    if found:
        print("   SUCCESS: New Admin IP detected.")
    else:
        print(f"   FAILED: No alert for new admin IP. Alerts: {alerts}")

    # 3. Test Suspicious Admin (Second Login = No Alert)
    print("3. Testing Suspicious Admin (Known IP)...")
    alerts_2 = rule_detector.check_rules(log_admin)
    found_2 = any("Suspicious Admin Login (New IP)" in a for a in alerts_2)
    if not found_2:
        print("   SUCCESS: Known Admin IP ignored (Correct).")
    else:
        print("   FAILED: Alerted on known IP.")

if __name__ == "__main__":
    test_rules()
