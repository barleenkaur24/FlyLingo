# FlyLingo — Integrated Hackathon Prototype

**JapanHack 2026 · JAL PS-02 · Offline in-flight communication, translation, and crew response**

This integrated build combines the stronger, newer FlyLingo implementation from P2 with the multilingual language-selection entry screen from P1. The main application has one source of truth (`server.py`, `nlp_engine.py`, and `templates/`) rather than competing server copies.

## What is integrated

- **Passenger-to-crew communication:** quick actions and free-text requests from a passenger phone.
- **Cross-language support:** offline rule-based intent handling and Japanese cabin-service phrasing, with romaji for crew assistance. The language-selection page supports English, Hindi, Punjabi, Japanese, Tamil, Telugu, and Bengali.
- **Emotion/urgency-aware routing:** medical distress is elevated over routine comfort requests; this is an intent/keyword heuristic, not a validated emotion-recognition model.
- **Crew operations dashboard:** seat/cabin view, priority queue, resolving/delivered workflow, and audible alerts.
- **Surveillance/operations view:** separate operational websocket and dashboard.
- **Privacy-oriented payload sanitization:** selected personal fields are stripped from messages sent to the opposite role. This is a prototype safeguard, not a complete security guarantee.
- **Offline-friendly behavior:** local server, locally generated QR, and browser-generated audio; Japanese speech synthesis depends on the browser/device having a Japanese voice installed.

## Run locally

Requires Python 3.10+ (Python 3.11 or 3.12 recommended). From this folder:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Or on Windows, double-click `run_server.bat`. Then open:

- Boarding pass: `http://127.0.0.1:8000/` or `/ticket`
- Language selection: `http://127.0.0.1:8000/language`
- Passenger screen: `http://127.0.0.1:8000/passenger?seat=24K`
- Crew tablet: `http://127.0.0.1:8000/crew`
- Operations dashboard: `http://127.0.0.1:8000/surveillance`
- Gateway: `http://127.0.0.1:8000/gateway`
- API docs: `http://127.0.0.1:8000/docs`

For phone/tablet access, connect the devices to the same local Wi-Fi/hotspot and open `http://<HOST_LAN_IP>:8000/`. No public internet is required for the core local demo.

## Tests

Run the root-level test files explicitly (the older prototype contained duplicate copies of tests in nested folders):

```bash
python -m pytest -q test_nlp.py test_backend.py test_full_system.py
```

## Project layout

- `server.py` — canonical FastAPI app, endpoints, WebSocket routing, priority queue, sanitization
- `nlp_engine.py` — offline speech/text intent and translation logic
- `templates/` — server-served screens, including the integrated `language.html`
- `html/`, `css/`, `js/` — modular UI assets retained from P2 for team editing/reference
- `docs/` — architecture, offline hotspot guide, judge Q&A, pitch script
- `presentations/` — presentation source files
- `test_*.py` — NLP, backend, and end-to-end checks

## Demo limitation to state honestly

The prototype does not perform reliable psychological emotion recognition or fully understand unrestricted conversation. It classifies text using local rules and keywords, then maps the detected request to a Japanese service phrase and priority. Treat high-priority medical flags as prompts for human crew assessment, not as medical diagnosis.


## P6 Milestone Additions (October 2026)

### 1. Offline Indian Brand-Name Medicine ➔ Japanese PMDA Generic Decoder
- **Offline Medical Dictionary**: Maps 15 common Indian pharmaceutical trade brands carried by elderly passengers (e.g., *Vertin, Dolo-650, Pan-D, Telma-40, Glycomet, Asthalin Inhaler, Combiflam, Meftal-Spas, Avomine, Allegra, Eldoper, Sorbitrate, Ecosprin, Digene, Restyl*) to:
  - **International Nonproprietary Name (INN)** (e.g., *Betahistine, Paracetamol, Pantoprazole + Domperidone, Telmisartan, Metformin, Salbutamol*)
  - **Ministry of Health Japan (PMDA) Katakana & Kanji** (e.g., *ベタヒスチン塩酸塩 / メリスロン, アセトアミノフェン / カロナール*)
  - **Aviation Cabin Safety Advisory** (altitude pressure interaction, low cabin humidity 10-15%, dehydration prevention, meal delay hypoglycemia risk)
- **1-Tap Direct Transmit to Crew Tablet**: Dispatches rich bilingual pharmacology dossier via WebSocket to `crew.html`, alerting Japanese cabin attendants and onboard physicians with exact Japanese generic equivalents and immediate cabin comfort protocols (e.g. warm water delivery, headrest stabilization).

### 2. Onboard Cabin First-Aid Kit Remedies
- 1-tap requests for 6 airline-approved first-aid amenities:
  - 🤢 *Motion Sickness Relief Kit* (airsickness bag, chilled peppermint towel, cold water)
  - 🧊 *Cooling Gel Forehead Sheet* (Japanese hydrogel patch for fever/migraine)
  - 💧 *ORS Electrolytes + Warm Water* (WHO rehydration powder to prevent cabin dehydration collapse)
  - 👂 *Cabin Pressure Ear Decompression Plugs* (ceramic micro-filter plugs for descent ear popping)
  - 🩹 *Sterile Band-Aids & Antiseptic Swabs* (waterproof adhesive strips and wipes)
  - 🩺 *Vital Signs Check* (crew brings certified Omron digital BP cuff and SpO2 pulse oximeter)

### 3. Senior Accessibility Mode & Persistent Multilingual Experience
- High-contrast Canary-Yellow senior mode (`👵 Senior Zoom: Aa+`, 24px `#FDE047` on `#000000`).
- Persistent language preference across screens from `language.html` into `passenger.html` across 7 languages (Hindi, Punjabi, English, Japanese, Tamil, Telugu, Bengali).
- Safety demonstration theater with sequential live stream mode transitioning into user-controlled video playback.
