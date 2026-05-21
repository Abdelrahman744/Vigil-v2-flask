"""
Vigil — Entry Point
===================
Start the Flask development server.
"""

import os
import time
import threading
import requests
from app import create_app

def start_heartbeat_loop():
    """Background thread that triggers the heartbeat every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            print("\n[Vigil Cron] Triggering background heartbeat 🫀 ⏳")
            res = requests.get("http://127.0.0.1:5000/api/cron/heartbeat", timeout=60)
            data = res.json()
            print(f"[Vigil Cron] Heartbeat complete  — Checked {data.get('checked', 0)} targets.")
            for r in data.get("results", []):
                icon = "✔️  [UP]" if r['status'] == 'Up' else "❌  [DOWN]"
                print(f"  {icon} Target {r['id']} ({r['name']}): {r['status']} ({r['latency']}ms)")
            print()
        except Exception as e:
            print(f"\n[Vigil Cron] Heartbeat failed [FAIL]: {e}\n")

app = create_app()

if __name__ == "__main__":
    # Start the heartbeat loop only in the Werkzeug worker process to avoid duplication
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        monitor_thread = threading.Thread(target=start_heartbeat_loop, daemon=True)
        monitor_thread.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
