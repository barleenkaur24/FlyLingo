# ==============================================================================
# ✈️ FlyLingo — 1-CLICK LAUNCHER FOR OFFLINE / AIRPLANE MODE
# ==============================================================================
import os
import sys
import threading
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLY_DIR = os.path.join(BASE_DIR, "FlyLingo")
if os.path.isdir(FLY_DIR):
    os.chdir(FLY_DIR)
    sys.path.insert(0, FLY_DIR)
else:
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)

def launch_browser():
    """Wait for uvicorn to initialize, then automatically open Passenger & Crew tabs"""
    time.sleep(1.5)
    print("\n" + "=" * 65)
    print(" ✈️  JAPAN AIRLINES: FlyLingo IS LIVE AND RUNNING OFFLINE!")
    print("=" * 65)
    print("  1. Passenger Language Selection: http://127.0.0.1:8000/language")
    print("  2. Passenger Seat Portal:        http://127.0.0.1:8000/passenger")
    print("  3. Cabin Crew Station (Tablet):  http://127.0.0.1:8000/crew")
    print("  4. Boarding Pass Screen:         http://127.0.0.1:8000/ticket")
    print("  5. Operations Surveillance Deck: http://127.0.0.1:8000/surveillance")
    print("=" * 65)
    print(" Opening Passenger and Crew screens in your browser now...\n")
    webbrowser.open("http://127.0.0.1:8000/language")
    time.sleep(0.5)
    webbrowser.open("http://127.0.0.1:8000/crew")

if __name__ == "__main__":
    threading.Thread(target=launch_browser, daemon=True).start()
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
