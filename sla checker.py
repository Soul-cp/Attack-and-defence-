#!/usr/bin/env python3
"""
sla_checker.py — Attack/Defense CTF SLA (Service Level Agreement) monitor

Most A&D scoreboards dock your points if your OWN service goes down or
stops behaving correctly after you patch it. This script polls your box
on a loop and tells you the second something breaks, so you can catch a
bad patch before the organizers' real SLA bot does.

HOW TO USE
1. Edit the SERVICES list below with your box(es) + endpoints.
2. For each service, write a `check_fn` that does a *real* functional
   check (not just "is port open") — e.g. register a user, log in,
   create+read a note, verify a known value round-trips. Mirror
   whatever the organizer's actual SLA script probably tests.
3. Run: python3 sla_checker.py
4. (Optional) set a Discord/Slack webhook URL below to get pinged.

This only talks to hosts YOU list — point it at your own team's
services, not at other teams.
"""

import time
import json
import traceback
import datetime
import requests

# ---------------------------------------------------------------------
# CONFIG — fill this in per the event
# ---------------------------------------------------------------------

CHECK_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT = 5
WEBHOOK_URL = None  # e.g. Discord webhook URL, or leave None to just print

SERVICES = [
    {
        "name": "web-pwn-service",
        "base_url": "http://127.0.0.1:8080",
    },
    # add more services here
]


# ---------------------------------------------------------------------
# PER-SERVICE FUNCTIONAL CHECKS — customize these for your actual app
# ---------------------------------------------------------------------

def check_web_pwn_service(base_url):
    """
    Example functional check: hit the homepage, then exercise one
    real feature end-to-end. Replace the logic below with whatever
    your service actually does (register/login/create-post/etc).
    Return (ok: bool, detail: str).
    """
    s = requests.Session()

    r = s.get(base_url, timeout=REQUEST_TIMEOUT)
    if r.status_code != 200:
        return False, f"homepage returned {r.status_code}"

    # Example: create a throwaway resource and read it back.
    # Adjust paths/fields to match your service's real API.
    try:
        create = s.post(
            f"{base_url}/api/notes",
            json={"title": "sla-check", "body": "ping"},
            timeout=REQUEST_TIMEOUT,
        )
        if create.status_code not in (200, 201):
            return False, f"create returned {create.status_code}"

        note_id = create.json().get("id")
        if note_id is None:
            return False, "create response missing id"

        read = s.get(f"{base_url}/api/notes/{note_id}", timeout=REQUEST_TIMEOUT)
        if read.status_code != 200:
            return False, f"read returned {read.status_code}"
        if "ping" not in read.text:
            return False, "round-trip content mismatch"

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return False, f"unexpected response shape: {e}"

    return True, "ok"


# Map service name -> check function
CHECK_FUNCTIONS = {
    "web-pwn-service": check_web_pwn_service,
}


# ---------------------------------------------------------------------
# RUNNER — shouldn't need to touch below this line
# ---------------------------------------------------------------------

def notify(message):
    print(message)
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message}, timeout=5)
        except requests.RequestException:
            pass  # don't let a flaky webhook crash the monitor


def run_once():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for svc in SERVICES:
        name = svc["name"]
        check_fn = CHECK_FUNCTIONS.get(name)
        if not check_fn:
            print(f"[{timestamp}] {name}: no check function registered, skipping")
            continue

        try:
            ok, detail = check_fn(svc["base_url"])
        except requests.RequestException as e:
            ok, detail = False, f"connection error: {e}"
        except Exception:
            ok, detail = False, f"check crashed:\n{traceback.format_exc()}"

        status = "UP  " if ok else "DOWN"
        line = f"[{timestamp}] {name:<20} {status}  {detail}"
        if ok:
            print(line)
        else:
            notify(f"⚠️ SLA FAIL — {line}")


def main():
    print(f"Starting SLA monitor — checking every {CHECK_INTERVAL_SECONDS}s. Ctrl+C to stop.")
    while True:
        run_once()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
