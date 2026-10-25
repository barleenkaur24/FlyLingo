# FlyLingo 
### Multilingual Passenger–Crew Communication System

FlyLingo is a multilingual web application designed to help airline passengers communicate with cabin crew despite language barriers.

## Problem Statement
Language barriers can make it difficult for passengers to communicate routine needs or urgent concerns to cabin crew. FlyLingo aims to make this communication more accessible.

## Key Features
- **Multilingual Interface:** Language selection for passengers.
- **Passenger Assistance:** Submit requests through a web interface.
- **Japanese Translation:** Japanese messages for supported requests.
- **Urgency Prioritisation:** Helps crew identify high-priority requests.
- **Real-Time Communication:** Passenger-to-crew messaging using WebSockets.
- **Safety Audio Instructions:** Audio instructions in supported languages.
- **QR Code Access:** Quick access to the passenger interface.
- **Local Network Support:** Designed to work across a local network.

## Technology Stack
- Python and FastAPI
- HTML, CSS and JavaScript
- WebSockets and JSON
- NLP and translation components

## Project Structure
- `FlyLingo/` — Main application files
- `FlyLingo/audio/` — Safety instruction audio
- `FlyLingo/css/` — Stylesheets
- `FlyLingo/js/` — JavaScript files
- `FlyLingo/templates/` — HTML templates
- `FlyLingo/docs/` — Project documentation
- `FlyLingo/presentations/` — Project presentation files
- `server.py` — Root backend entry point
- `run.py` — Application runner
- `run_server.bat` — Windows startup script

## Getting Started

### Prerequisites
- Python installed
- A Windows terminal or PowerShell

### Installation
Clone the repository:

```bash
git clone https://github.com/barleenkaur24/FlyLingo.git
cd FlyLingo
```

Install the application's dependencies:

```bash
python -m pip install -r FlyLingo/requirements.txt
```

### Run
From the repository root, launch:

```powershell
.\run_server.bat
```

If necessary, consult `FlyLingo/README.md` and `FlyLingo/docs/offline_hotspot_guide.md` for project-specific instructions.

## Project
Developed as part of JapanHack.

*Language availability, translation capabilities, and audio features depend on the components included in the current build.*
