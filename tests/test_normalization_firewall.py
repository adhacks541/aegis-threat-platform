from app.services.normalization import normalization_service

def test_ufw_parsing():
    print("\n--- Testing Firewall Normalization ---")
    
    raw_log = "Feb  1 12:34:56 server kernel: [UFW BLOCK] IN=eth0 OUT= MAC=00:00:00:00:00:00 SRC=192.168.1.50 DST=10.0.0.5 PROTO=TCP SPT=12345 DPT=80 WINDOW=1024 RES=0x00 SYN URGP=0"
    
    normalized = normalization_service.parse_log(raw_log, "syslog")
    
    print(f"Raw: {raw_log}")
    print(f"Parsed: {normalized}")
    
    assert normalized['event_type'] == 'firewall_block'
    assert normalized['ip'] == '192.168.1.50'
    assert normalized['dst'] == '10.0.0.5'
    assert normalized['proto'] == 'TCP'
    print("SUCCESS: UFW Log correctly parsed.")

if __name__ == "__main__":
    test_ufw_parsing()
