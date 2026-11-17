#!/usr/bin/env python3
"""
attack_runner.py — Attack/Defense CTF flag-farming framework

This is the generic PLUMBING that every A&D team needs: loop over
enemy team IPs, run your exploit against each, pull out flags, submit
them to the scoreboard, log what worked and what didn't. It does NOT
contain any vulnerability-specific logic — that's the `exploit()`
function at the bottom, which you fill in live once you've found and
verified the actual web-pwn bug on your own vulnerable instance.

Do not point this at anything outside the competition's authorized
target range.

HOW TO USE
1. Fill in TEAMS (or load from a file), FLAG_SUBMIT_URL and your token.
2. Write `exploit(target_ip)` to return a flag string, or None.
   Test it against your OWN patched/unpatched instance first.
3. Run: python3 attack_runner.py
"""

import re
import time
import threading
import datetime
import requests

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

TEAMS = [
    # Fill in with the enemy team IPs/hosts given by the organizers.
    # "10.10.1.1",
    # "10.10.2.1",
]

TARGET_PORT = 8080
ROUND_INTERVAL_SECONDS = 60     # how often to re-run the whole sweep
MAX_WORKERS = 8                 # parallel threads across teams
REQUEST_TIMEOUT = 6

FLAG_REGEX = re.compile(r"[A-Za-z0-9_]{3,20}\{[A-Za-z0-9_\-]{1,100}\}")

# Scoreboard flag submission — ask organizers for the exact format,
# this is the common "one flag per POST" pattern.
FLAG_SUBMIT_URL = "https://scoreboard.example/api/submit"
FLAG_SUBMIT_TOKEN = "YOUR_TEAM_TOKEN_HERE"

LOG_FILE = "attack_runner.log"


# ---------------------------------------------------------------------
# EXPLOIT — THIS is the part you write yourselves once you've found
# and confirmed the bug. Keep it idempotent and fast: in A&D you'll
# run it every round against every team.
# ---------------------------------------------------------------------

def exploit(target_ip):
    """
    Return the flag string if successful, otherwise None.
    Replace this with your actual logic once you've identified the
    web-pwn vulnerability (e.g. the specific endpoint/parameter to hit
    and where the flag shows up in the response).
    """
    base_url = f"http://{target_ip}:{TARGET_PORT}"

    try:
        r = requests.get(base_url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return None

    match = FLAG_REGEX.search(r.text)
    if match:
        return match.group(0)

    return None


# ---------------------------------------------------------------------
# SUBMISSION
# ---------------------------------------------------------------------

_submitted = set()
_lock = threading.Lock()


def submit_flag(flag, source_ip):
    with _lock:
        if flag in _submitted:
            return
        _submitted.add(flag)

    try:
        resp = requests.post(
            FLAG_SUBMIT_URL,
            headers={"Authorization": f"Bearer {FLAG_SUBMIT_TOKEN}"},
            json={"flag": flag},
            timeout=REQUEST_TIMEOUT,
        )
        log(f"SUBMIT {flag} (from {source_ip}) -> HTTP {resp.status_code} {resp.text[:200]}")
    except requests.RequestException as e:
        log(f"SUBMIT FAILED {flag} (from {source_ip}) -> {e}")


# ---------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def attack_one(target_ip):
    try:
        flag = exploit(target_ip)
    except Exception as e:
        log(f"{target_ip}: exploit() raised {e!r}")
        return

    if flag:
        log(f"{target_ip}: got flag {flag}")
        submit_flag(flag, target_ip)
    else:
        log(f"{target_ip}: no flag this round")


def run_round():
    threads = []
    for ip in TEAMS:
        t = threading.Thread(target=attack_one, args=(ip,), daemon=True)
        threads.append(t)

    # simple batching so we don't fire MAX_WORKERS+ threads at once
    for i in range(0, len(threads), MAX_WORKERS):
        batch = threads[i:i + MAX_WORKERS]
        for t in batch:
            t.start()
        for t in batch:
            t.join()


def main():
    if not TEAMS:
        log("TEAMS list is empty — add target IPs before running.")
        return

    log(f"Starting attack runner against {len(TEAMS)} teams, "
        f"every {ROUND_INTERVAL_SECONDS}s. Ctrl+C to stop.")
    while True:
        start = time.time()
        run_round()
        elapsed = time.time() - start
        sleep_for = max(0, ROUND_INTERVAL_SECONDS - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
