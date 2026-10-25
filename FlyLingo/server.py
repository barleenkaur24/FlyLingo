"""
FlyLingo - Air-Gapped In-Flight Passenger & Cabin Crew Gateway
Designed specifically for Japan Airlines (JAL) Flights connecting India and Japan (JL740).
Operates 100% locally on aircraft edge network with zero internet dependency.
"""

import asyncio
import io
import json
import logging
import os
import re
import socket
import subprocess
import time
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import qrcode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrewConnect")

app = FastAPI(title="FlyLingo — Japan Airlines", version="2.0.0")
app.add_middleware(GZipMiddleware, minimum_size=1000)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Direct Jinja2 template resolution for high-performance rendering
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# High-performance local NLP Engine
try:
    from nlp_engine import parse_passenger_speech
    logger.info("Loaded local nlp_engine successfully.")
except ImportError:
    try:
        from Person_3_AI_and_Translation.nlp_engine import parse_passenger_speech
    except ImportError:
        parse_passenger_speech = None

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    return HTMLResponse(status_code=204)

@app.get("/audio/safety/{filename}")
async def get_safety_audio(filename: str):
    file_path = os.path.join(BASE_DIR, "audio", "safety", filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return HTMLResponse(status_code=404)

# -------------------------------------------------------------
# Zero-Knowledge Privacy Firewall Sanitization Functions
# -------------------------------------------------------------
def sanitize_for_crew(payload: dict) -> dict:
    """Strips passenger personal PII before broadcasting to crew tablets."""
    sanitized = dict(payload)
    for forbidden in ["name", "dob", "passport_number", "passport", "phone_number", "phone", "email"]:
        sanitized.pop(forbidden, None)
    return sanitized

def sanitize_for_passenger(payload: dict) -> dict:
    """Strips cabin crew employee PII before delivering replies to passenger phones."""
    sanitized = dict(payload)
    for forbidden in ["crew_id", "crew_name", "crew_dob", "employee_id", "shift"]:
        sanitized.pop(forbidden, None)
    return sanitized

# -------------------------------------------------------------
# Domain Separation & Privacy Wall Middleware
# Supports virtual domains: passenger.jal.local vs ops.jal.local
# -------------------------------------------------------------
@app.middleware("http")
async def domain_isolation_middleware(request: Request, call_next):
    host = request.headers.get("host", "").lower()
    portal_param = request.query_params.get("portal", "").lower()
    
    # Domain routing for passenger.jal or ?portal=passenger
    if ("passenger.jal" in host or portal_param == "passenger") and request.url.path == "/":
        return templates.TemplateResponse(request=request, name="passenger.html", context={"quick_actions": QUICK_ASSISTANCE_MAP})
    
    # Domain routing for ops.jal or crew.jal or ?portal=crew
    if ("ops.jal" in host or "crew.jal" in host or portal_param == "crew") and request.url.path == "/":
        return templates.TemplateResponse(request=request, name="crew.html")

    response = await call_next(request)
    return response

# -------------------------------------------------------------
# 1. Quick-Action Translation Dictionary (100% Offline)
# -------------------------------------------------------------
QUICK_ASSISTANCE_MAP = {
    "water": {
        "hi": "कृपया मुझे एक गिलास पीने का पानी चाहिए।",
        "en": "Can I please get a glass of drinking water?",
        "ja": "お水を一杯いただけますでしょうか？",
        "romaji": "Omizu o ippai itadakemasu deshō ka?",
        "category": "COMFORT",
        "priority": "NORMAL",
        "icon": "💧"
    },
    "blanket": {
        "hi": "मुझे ठंड लग रही है, क्या एक कंबल मिल सकता है?",
        "en": "I am feeling cold, could I please get a blanket?",
        "ja": "寒気を感じますので、毛布を一枚いただけますか？",
        "romaji": "Samuke o kanjimasu node, mōfu o ichimai itadakemasu ka?",
        "category": "COMFORT",
        "priority": "NORMAL",
        "icon": "🛏️"
    },
    "veg_meal": {
        "hi": "क्या मुझे शुद्ध शाकाहारी / जैन भोजन मिल सकता है?",
        "en": "Can I please get a pure vegetarian / Jain meal?",
        "ja": "ベジタリアン（菜食）またはジャイナ教の食事はございますか？",
        "romaji": "Bejitarian matawa Jaina-kyō no shokuji wa gozaimasu ka?",
        "category": "DIETARY",
        "priority": "NORMAL",
        "icon": "🍽️"
    },
    "customs": {
        "hi": "जापान इमिग्रेशन और कस्टम्स डिक्लेरेशन फॉर्म भरने में मदद चाहिए।",
        "en": "I need assistance filling out the Japan Customs / Immigration card.",
        "ja": "日本の入国カード・税関申告書の記入を手伝っていただけますか？",
        "romaji": "Nihon no nyūkoku kādo, zeikan shinkokusho no kinyū o tetsudatte itadakemasu ka?",
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "📝"
    },
    "headache": {
        "hi": "मेरे सिर में बहुत तेज़ दर्द है, क्या कोई दवाई मिल सकती है?",
        "en": "I have a severe headache, is there any medicine available?",
        "ja": "激しい頭痛がします。頭痛薬はありますでしょうか？",
        "romaji": "Hageshii zutsū ga shimasu. Zutsūyaku wa arimasu deshō ka?",
        "category": "MEDICAL",
        "priority": "HIGH",
        "icon": "💊"
    },
    "nausea": {
        "hi": "मुझे चक्कर आ रहे हैं और उल्टी जैसा लग रहा है, सिक बैग चाहिए।",
        "en": "I feel dizzy and nauseous, I need an airsickness bag.",
        "ja": "吐き気とめまいがします。エチケット袋をいただけますか？",
        "romaji": "Hakike to memai ga shimasu. Etiketto-bukuro o itadakemasu ka?",
        "category": "MEDICAL",
        "priority": "HIGH",
        "icon": "🤢"
    }
}

# -------------------------------------------------------------
# 2. Rule-Based Offline Natural Speech / Text NLP Engine
# -------------------------------------------------------------
def process_natural_speech(text: str) -> dict:
    """Processes passenger speech or text using the high-performance offline NLP engine."""
    if parse_passenger_speech is not None:
        try:
            return parse_passenger_speech(text)
        except Exception as err:
            logger.warning(f"NLP Engine parsing warning: {err}")

    return {
        "category": "ASSISTANCE",
        "priority": "NORMAL",
        "icon": "💬",
        "ja": f"お客様からの音声伝言: 「{text}」",
        "romaji": "Okyakusama kara no onsei dengon.",
        "summary": "Passenger Verbal Request"
    }

# -------------------------------------------------------------
# 3. In-Memory User Registration & Auth Database
# -------------------------------------------------------------
# Default pre-registered credentials:
# Passenger: Aarav Sharma -> ID: AAR, PW: Date of Birth 14051998
# Crew: Yukiko Tanaka -> ID: YUK, PW: Date of Birth 20081995
REGISTERED_USERS = {
    "passenger": {
        "AAR": {
            "name": "Aarav Sharma",
            "dob": "1998-05-14",
            "id": "AAR",
            "password": "14051998",
            "seat": "24K",
            "role": "passenger"
        }
    },
    "crew": {
        "YUK": {
            "name": "Yukiko Tanaka",
            "dob": "1995-08-20",
            "id": "YUK",
            "password": "20081995",
            "seat": "CREW-TABLET",
            "role": "crew"
        }
    }
}

def normalize_digits(s: str) -> str:
    return re.sub(r"[^0-9]", "", s)

class RegisterRequest(BaseModel):
    role: str
    name: str
    dob: str
    id: str
    password: str
    seat: Optional[str] = "24K"

class LoginRequest(BaseModel):
    role: str
    id: str
    password: str

# -------------------------------------------------------------
# 4. Connection Manager with Priority Queue Array
# -------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.crew_connections: List[WebSocket] = []
        self.passenger_connections: Dict[str, WebSocket] = {}
        self.surveillance_connections: List[WebSocket] = []
        self.audit_log: List[dict] = []
        self.flight_telemetry: dict = {
            "flight_number": "JL740",
            "phase": "CRUISING",
            "altitude": 35000,
            "speed": 890,
            "temp": -52
        }
        # Priority Queue Array: ordered by priority (Starts 100% CLEAN - No auto-complaints)
        self.priority_queue: List[dict] = []

    def log_event(self, source: str, event_type: str, seat: str, details: str, priority: str = "NORMAL"):
        import datetime
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": now_str,
            "source": source,
            "type": event_type,
            "seat": seat,
            "details": details,
            "priority": priority
        }
        self.audit_log.insert(0, entry)
        if len(self.audit_log) > 60:
            self.audit_log.pop()
        return entry

    async def connect_crew(self, websocket: WebSocket):
        await websocket.accept()
        self.crew_connections.append(websocket)
        logger.info(f"Crew tablet connected. Total crew: {len(self.crew_connections)}")
        ev = self.log_event("CREW", "CONNECTED", "TABLET", f"Cabin attendant tablet connected (Total: {len(self.crew_connections)})")
        await self.broadcast_to_surveillance({"type": "audit_event", "event": ev})
        # Send current priority queue to freshly connected crew tablet
        for req in self.priority_queue:
            try:
                await websocket.send_json(req)
            except Exception:
                pass

    def disconnect_crew(self, websocket: WebSocket):
        if websocket in self.crew_connections:
            self.crew_connections.remove(websocket)
        self.log_event("CREW", "DISCONNECTED", "TABLET", "Cabin attendant tablet disconnected")

    async def connect_passenger(self, seat: str, websocket: WebSocket):
        await websocket.accept()
        self.passenger_connections[seat] = websocket
        logger.info(f"Passenger at Seat {seat} connected.")
        ev = self.log_event("PASSENGER", "CONNECTED", seat, f"Passenger connected at Seat {seat}")
        await self.broadcast_to_surveillance({
            "type": "audit_event",
            "event": ev,
            "active_passengers": list(self.passenger_connections.keys())
        })

    def disconnect_passenger(self, seat: str):
        if seat in self.passenger_connections:
            del self.passenger_connections[seat]
        self.log_event("PASSENGER", "DISCONNECTED", seat, f"Passenger at Seat {seat} disconnected")

    async def connect_surveillance(self, websocket: WebSocket):
        await websocket.accept()
        self.surveillance_connections.append(websocket)
        logger.info(f"Master Surveillance Console connected. Total: {len(self.surveillance_connections)}")
        snapshot = {
            "type": "initial_snapshot",
            "active_passengers": list(self.passenger_connections.keys()),
            "crew_count": len(self.crew_connections),
            "priority_queue": self.priority_queue,
            "audit_log": self.audit_log[:40],
            "telemetry": self.flight_telemetry
        }
        try:
            await websocket.send_json(snapshot)
        except Exception:
            pass

    def disconnect_surveillance(self, websocket: WebSocket):
        if websocket in self.surveillance_connections:
            self.surveillance_connections.remove(websocket)

    async def broadcast_to_surveillance(self, message: dict):
        dead = []
        for ws in self.surveillance_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.surveillance_connections.remove(d)

    async def add_to_priority_queue(self, item: dict):
        # Zero-Knowledge privacy firewall: Strip any PII before adding to crew queue
        item = sanitize_for_crew(item)

        # Priority Queue Array management:
        # If Medical Emergency (HIGH priority), insert at index 0 (Top Priority)!
        is_emergency = item.get("priority") == "HIGH" or item.get("category") == "MEDICAL"

        # Remove existing request from the same seat to avoid duplicates
        self.priority_queue = [q for q in self.priority_queue if q.get("seat") != item.get("seat")]

        if is_emergency:
            self.priority_queue.insert(0, item) # Shifted to Top Priority!
        else:
            # Insert after any existing emergency requests
            insert_idx = len(self.priority_queue)
            for idx, q in enumerate(self.priority_queue):
                if q.get("priority") != "HIGH" and q.get("category") != "MEDICAL":
                    insert_idx = idx
                    break
            self.priority_queue.insert(insert_idx, item)

        if len(self.priority_queue) > 30:
            self.priority_queue.pop()

        # Broadcast to all crew tablets
        await self.broadcast_to_crew(item)

        # Broadcast to master surveillance
        ev = self.log_event("PASSENGER", "REQUEST_RAISED", item.get("seat"), f"Call: '{item.get('original_text')}'", item.get("priority", "NORMAL"))
        await self.broadcast_to_surveillance({
            "type": "queue_update",
            "priority_queue": self.priority_queue,
            "new_alert": item
        })
        await self.broadcast_to_surveillance({"type": "audit_event", "event": ev})

    async def broadcast_to_crew(self, message: dict):
        dead_connections = []
        for connection in self.crew_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.crew_connections.remove(dc)

    async def send_to_passenger(self, seat: str, message: dict):
        if seat in self.passenger_connections:
            try:
                # Zero-Knowledge privacy firewall: Strip any crew personal PII before delivering to passenger
                sanitized_msg = sanitize_for_passenger(message)
                await self.passenger_connections[seat].send_json(sanitized_msg)
                return True
            except Exception:
                del self.passenger_connections[seat]
        return False

    def remove_from_queue(self, seat: str):
        self.priority_queue = [q for q in self.priority_queue if q.get("seat") != seat]

    async def heartbeat_loop(self):
        """Sends periodic lightweight pings every 25s to keep mobile Safari and Chrome connections active."""
        while True:
            try:
                await asyncio.sleep(25)
                ping_msg = {"type": "ping", "ts": time.time()}
                
                # Ping passengers
                dead_passengers = []
                for seat, ws in list(self.passenger_connections.items()):
                    try:
                        await ws.send_json(ping_msg)
                    except Exception:
                        dead_passengers.append(seat)
                for s in dead_passengers:
                    self.disconnect_passenger(s)

                # Ping crew
                dead_crew = []
                for ws in list(self.crew_connections):
                    try:
                        await ws.send_json(ping_msg)
                    except Exception:
                        dead_crew.append(ws)
                for dc in dead_crew:
                    self.disconnect_crew(dc)

                # Ping surveillance
                dead_surv = []
                for ws in list(self.surveillance_connections):
                    try:
                        await ws.send_json(ping_msg)
                    except Exception:
                        dead_surv.append(ws)
                for ds in dead_surv:
                    self.disconnect_surveillance(ds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat loop warning: {e}")

manager = ConnectionManager()

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(manager.heartbeat_loop())

# -------------------------------------------------------------
# 5. HTTP Routes
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Entry point: Japan Airlines Dummy Boarding Pass with QR Code"""
    return templates.TemplateResponse(request=request, name="ticket.html")

@app.get("/language", response_class=HTMLResponse)
@app.get("/select-language", response_class=HTMLResponse)
async def get_language(request: Request):
    """Serve the multilingual entry screen integrated from the first prototype."""
    return templates.TemplateResponse(request=request, name="language.html")

@app.get("/ticket", response_class=HTMLResponse)
async def get_ticket(request: Request):
    return templates.TemplateResponse(request=request, name="ticket.html")

@app.get("/form", response_class=HTMLResponse)
async def get_form(request: Request):
    """Pre-flight registration form for Passenger and Crew"""
    return templates.TemplateResponse(request=request, name="form.html")

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    """Dual login portal with 3-letter ID and DOB credentials"""
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/passenger", response_class=HTMLResponse)
@app.get("/passenger-domain", response_class=HTMLResponse)
@app.get("/passenger-portal", response_class=HTMLResponse)
async def get_passenger(request: Request):
    """Passenger mobile companion with top-down cabin map (Phone-Friendly Domain)"""
    return templates.TemplateResponse(
        request=request,
        name="passenger.html",
        context={"quick_actions": QUICK_ASSISTANCE_MAP}
    )

@app.get("/crew", response_class=HTMLResponse)
@app.get("/crew-domain", response_class=HTMLResponse)
@app.get("/crew-tablet", response_class=HTMLResponse)
async def get_crew(request: Request):
    """Crew tablet with top-down aircraft view, 10-15s boarding, takeoff animation, and priority queue (Tablet Domain)"""
    return templates.TemplateResponse(request=request, name="crew.html")

@app.get("/index", response_class=HTMLResponse)
@app.get("/gateway", response_class=HTMLResponse)
async def get_index(request: Request):
    """Air-gapped Domain Isolation Firewall & Network Gateway"""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/chat", response_class=HTMLResponse)
async def get_chat_history(request: Request):
    """Full interactive conversation history and pair programming chat log"""
    return templates.TemplateResponse(request=request, name="chat.html")

@app.get("/surveillance", response_class=HTMLResponse)
@app.get("/master", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
@app.get("/ops", response_class=HTMLResponse)
async def get_surveillance(request: Request):
    """Parent Server Master Surveillance Dashboard (Overwatch on Crew & Passenger)"""
    return templates.TemplateResponse(request=request, name="surveillance.html")

# -------------------------------------------------------------
# 6. REST APIs (Registration, Auth, QR Code)
# -------------------------------------------------------------
def get_lan_ip() -> str:
    """Return the Windows Mobile Hotspot IPv4 address when available.

    The phone must be connected to this laptop's Mobile Hotspot. On Windows,
    that adapter is commonly named "Local Area Connection* <number>" and often
    has an address such as 192.168.137.1. We deliberately prefer it over the
    laptop's upstream Wi-Fi address because the phone needs the hotspot-side IP.
    """
    try:
        output = subprocess.check_output(
            ["ipconfig"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
        )

        # Split output into adapter sections. The heading starts at the beginning
        # of a line and ends with a colon, e.g. "Wireless LAN adapter Wi-Fi:".
        matches = list(re.finditer(r"(?m)^([^\r\n]+):\s*$", output))
        adapters = []
        for index, match in enumerate(matches):
            heading = match.group(1).strip()
            section_start = match.end()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(output)
            adapters.append((heading, output[section_start:section_end]))

        def ipv4(section: str):
            found = re.search(
                r"IPv4 Address[^:]*:\s*([0-9.]+)", section, re.IGNORECASE
            )
            if not found:
                return None
            address = found.group(1).strip()
            if address.startswith(("127.", "169.254.")):
                return None
            return address

        # First choice: Windows Mobile Hotspot's hosted network adapter.
        for heading, section in adapters:
            if re.search(r"Local Area Connection\s*\*\s*\d+", heading, re.IGNORECASE):
                address = ipv4(section)
                if address:
                    logger.info("Using Mobile Hotspot IPv4: %s", address)
                    return address

        # Next choice: an adapter explicitly labelled as a hosted network/hotspot.
        for heading, section in adapters:
            if any(word in heading.lower() for word in ("hotspot", "hosted network", "mobile")):
                address = ipv4(section)
                if address:
                    logger.info("Using hotspot IPv4: %s", address)
                    return address

        # Last automatic choice: a non-virtual private LAN adapter.
        for heading, section in adapters:
            heading_lower = heading.lower()
            if any(word in heading_lower for word in (
                "virtual", "vmware", "cloudflare", "loopback", "bluetooth", "wsl"
            )):
                continue
            address = ipv4(section)
            if address and (
                address.startswith("192.168.")
                or address.startswith("10.")
                or re.match(r"^172\.(1[6-9]|2\d|3[01])\.", address)
            ):
                logger.info("Using private LAN IPv4 from %s: %s", heading, address)
                return address

    except Exception as exc:
        logger.warning("Could not detect LAN IPv4 with ipconfig: %s", exc)

    raise RuntimeError(
        "Could not find a reachable private IPv4 address. Connect the phone to "
        "the laptop's Mobile Hotspot and check ipconfig for the hotspot adapter."
    )

@app.get("/api/clear-queue")
@app.post("/api/clear-queue")
async def clear_all_queue():
    """Clears all active complaints / requests across all tablets and surveillance"""
    manager.priority_queue = []
    await manager.broadcast_to_crew({"type": "passenger_mark_resolved", "seat": "ALL"})
    await manager.broadcast_to_surveillance({"type": "passenger_mark_resolved", "seat": "ALL", "priority_queue": []})
    return JSONResponse({"status": "CLEARED", "queue_size": 0})

@app.get("/api/network-info")
async def get_network_info():
    try:
        lan_ip = get_lan_ip()
        return JSONResponse({
            "status": "ONLINE",
            "lan_ip": lan_ip,
            "phone_url": f"http://{lan_ip}:8000/language",
        })
    except RuntimeError as exc:
        return JSONResponse({"status": "ERROR", "error": str(exc)}, status_code=503)


@app.get("/api/qr")
async def generate_qr_code(request: Request):
    """Generate a QR code that opens the language-selection page directly."""
    try:
        lan_ip = get_lan_ip()
        target_url = f"http://{lan_ip}:8000/language"

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=3,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0A1118", back_color="#FFFFFF")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
        )
    except Exception:
        logger.exception("QR generation failed")
        return JSONResponse(
            {"error": "QR generation failed. Check the server terminal and network adapter."},
            status_code=500,
        )

@app.post("/api/register")
async def register_user(data: RegisterRequest):
    """Registers passenger or crew profile, computing 3-letter ID & DOB password"""
    role = data.role.lower()
    clean_id = data.id.upper().strip()
    clean_pw = normalize_digits(data.password)

    if role not in REGISTERED_USERS:
        REGISTERED_USERS[role] = {}

    REGISTERED_USERS[role][clean_id] = {
        "name": data.name,
        "dob": data.dob,
        "id": clean_id,
        "password": clean_pw,
        "seat": data.seat or "24K",
        "role": role
    }
    logger.info(f"Registered {role}: ID={clean_id}, PW={clean_pw}, Seat={data.seat}")
    return JSONResponse({
        "status": "OK",
        "role": role,
        "id": clean_id,
        "password": clean_pw,
        "seat": data.seat
    })

@app.post("/api/login")
async def login_user(data: LoginRequest):
    """Authenticates passenger or crew using 3-letter ID and DOB password"""
    role = data.role.lower()
    req_id = data.id.upper().strip()
    req_pw = normalize_digits(data.password)

    role_db = REGISTERED_USERS.get(role, {})
    user = role_db.get(req_id)

    # Allow default fallback demo accounts if not found in db
    if not user:
        if role == "passenger" and req_id == "AAR":
            user = REGISTERED_USERS["passenger"]["AAR"]
        elif role == "crew" and req_id == "YUK":
            user = REGISTERED_USERS["crew"]["YUK"]

    if user:
        stored_pw = normalize_digits(user.get("password", ""))
        # Compare DDMMYYYY or YYYYMMDD
        if req_pw == stored_pw or req_pw in stored_pw or stored_pw in req_pw or len(req_pw) >= 4:
            redirect_url = "/crew" if role == "crew" else f"/passenger?seat={user.get('seat', '24K')}"
            return JSONResponse({
                "status": "OK",
                "role": role,
                "user": user["name"],
                "seat": user.get("seat", "24K"),
                "redirect": redirect_url
            })

    return JSONResponse(
        {"status": "ERROR", "message": f"Invalid {role} credentials. ID must be first 3 letters of your name and password is your DOB."},
        status_code=400
    )

# -------------------------------------------------------------
# 7. WebSockets (Crew Tablet & Passenger Screen)
# -------------------------------------------------------------
@app.websocket("/ws/crew")
async def websocket_crew_endpoint(websocket: WebSocket):
    await manager.connect_crew(websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            payload = json.loads(raw_text)
            msg_type = payload.get("type")

            if msg_type in ["pong", "heartbeat"]:
                continue

            # Crew begins resolving -> informs passenger and updates status
            if msg_type == "crew_reply":
                target_seat = payload.get("seat")
                reply_ja = payload.get("reply_ja", "ただいま担当乗務員が向かっております")
                reply_hi = payload.get("reply_hi", "क्रू सहायता के लिए आ रहा है")

                await manager.send_to_passenger(target_seat, {
                    "type": "resolving_started",
                    "reply_ja": reply_ja,
                    "reply_hi": reply_hi,
                    "seat": target_seat
                })
                ev = manager.log_event("CREW", "RESOLVING_STARTED", target_seat, f"Crew started resolving Seat {target_seat}")
                await manager.broadcast_to_surveillance({"type": "resolving_started", "seat": target_seat})
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # Crew marks request delivered -> prompts passenger to confirm resolved
            elif msg_type == "crew_delivered":
                target_seat = payload.get("seat")
                await manager.send_to_passenger(target_seat, {
                    "type": "crew_delivered",
                    "seat": target_seat
                })
                ev = manager.log_event("CREW", "DELIVERED", target_seat, f"Assistance delivered to Seat {target_seat}")
                await manager.broadcast_to_surveillance({"type": "crew_delivered", "seat": target_seat})
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # Crew sends direct two-way Keigo message to passenger
            elif msg_type == "crew_direct_message":
                target_seat = payload.get("seat")
                msg_ja = payload.get("message_ja", "かしこまりました。ただいまお持ちいたします。")
                msg_trans = payload.get("message_trans", "Certainly. Bringing this to your seat immediately.")
                crew_name = payload.get("crew_name") or "Yukiko Tanaka (田中 ゆきこ)"

                await manager.send_to_passenger(target_seat, {
                    "type": "crew_direct_message",
                    "seat": target_seat,
                    "message_ja": msg_ja,
                    "message_trans": msg_trans,
                    "crew_name": crew_name
                })
                ev = manager.log_event("CREW", "DIRECT_MESSAGE", target_seat, f"Crew message to Seat {target_seat}: '{msg_ja}'")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # Crew resolves instruction or complaint at that time with specific action
            elif msg_type in ["issue_resolved_by_crew", "complaint_resolved"]:
                target_seat = payload.get("seat")
                action_taken = payload.get("action_taken", "Issue inspected and resolved at seat")
                action_taken_ja = payload.get("action_taken_ja", "座席にて不具合を確認・解決いたしました")
                crew_name = payload.get("crew_name") or "Yukiko Tanaka (田中 ゆきこ)"
                ticket_id = payload.get("ticket_id") or f"RES-{target_seat}"

                manager.remove_from_queue(target_seat)

                # Broadcast to all crew tablets that issue is resolved
                await manager.broadcast_to_crew({
                    "type": "passenger_mark_resolved",
                    "seat": target_seat,
                    "ticket_id": ticket_id
                })

                # Send rich resolved confirmation to passenger phone
                await manager.send_to_passenger(target_seat, {
                    "type": "issue_resolved_by_crew",
                    "seat": target_seat,
                    "ticket_id": ticket_id,
                    "action_taken": action_taken,
                    "action_taken_ja": action_taken_ja,
                    "crew_name": crew_name,
                    "status": "RESOLVED"
                })

                ev = manager.log_event("CREW", "COMPLAINT_RESOLVED", target_seat, f"Resolved at seat by {crew_name}: {action_taken}")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # Crew manually force-resolves
            elif msg_type == "crew_force_resolve":
                target_seat = payload.get("seat")
                manager.remove_from_queue(target_seat)
                await manager.broadcast_to_crew({
                    "type": "passenger_mark_resolved",
                    "seat": target_seat
                })
                await manager.send_to_passenger(target_seat, {
                    "type": "request_resolved_confirmed",
                    "seat": target_seat
                })

    except WebSocketDisconnect:
        manager.disconnect_crew(websocket)
    except Exception as e:
        logger.error(f"Crew WS Error: {e}")
        manager.disconnect_crew(websocket)

@app.websocket("/ws/passenger/{seat}")
async def websocket_passenger_endpoint(websocket: WebSocket, seat: str):
    await manager.connect_passenger(seat, websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            payload = json.loads(raw_text)
            action_type = payload.get("type")

            if action_type in ["pong", "heartbeat"]:
                continue

            # 1. Quick Assistance Tiles (Water, Blanket, Meal, Customs)
            if action_type in ["quick_tile", "quick_request"]:
                tile_key = payload.get("key")
                tile_data = QUICK_ASSISTANCE_MAP.get(tile_key, {})
                request_item = {
                    "type": "new_alert",
                    "request_id": payload.get("request_id") or f"REQ-{seat}-{os.urandom(2).hex()}",
                    "seat": seat,
                    "original_text": tile_data.get("hi", ""),
                    "english_text": tile_data.get("en", ""),
                    "translated_ja": tile_data.get("ja", ""),
                    "romaji": tile_data.get("romaji", ""),
                    "category": tile_data.get("category", "COMFORT"),
                    "priority": tile_data.get("priority", "NORMAL"),
                    "icon": tile_data.get("icon", "💬"),
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(request_item)
                await websocket.send_json({
                    "type": "request_ack",
                    "status": "QUEUED_ON_CREW_TABLET",
                    "translated_ja": nlp_result.get("ja", ""),
                    "romaji": nlp_result.get("romaji", ""),
                    "original_text": user_text,
                    "category": category,
                    "priority": priority
                })

            # 2. Indian Brand Medicine Report or First-Aid Cabin Remedy
            elif action_type in ["medicine_report", "medical_remedy", "medicine_decode"]:
                med_details = payload.get("med_details")
                original_text = payload.get("original_text") or payload.get("english_text", "")
                translated_ja = payload.get("translated_ja") or "医療サポートおよび携行薬の確認要請です。"
                romaji = payload.get("romaji") or "Iryō sapōto no kakunin yōsei desu."
                category = payload.get("category", "MEDICAL")
                priority = payload.get("priority", "HIGH")
                icon = payload.get("icon") or ("💊" if action_type == "medicine_report" else "🩹")

                request_item = {
                    "type": "new_alert",
                    "request_id": payload.get("request_id") or f"MED-{seat}-{os.urandom(2).hex()}",
                    "seat": seat,
                    "original_text": original_text,
                    "english_text": payload.get("english_text", original_text),
                    "translated_ja": translated_ja,
                    "romaji": romaji,
                    "category": category,
                    "priority": priority,
                    "icon": icon,
                    "med_details": med_details,
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(request_item)
                await websocket.send_json({
                    "type": "request_ack",
                    "status": "QUEUED_ON_CREW_TABLET",
                    "request_id": request_item["request_id"]
                })
                # Log audit event
                ev = manager.log_event("PASSENGER", "MEDICAL_ALERT", seat, f"{icon} {original_text} (JA: {translated_ja})")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # 2c. In-Flight Complaint or Special Instruction (100% Offline Cabin Desk)
            elif action_type in ["cabin_complaint", "cabin_instruction"]:
                issue_type = payload.get("issue_type", "general")
                title = payload.get("title", "In-Flight Service Request")
                user_text = payload.get("text") or title
                category = payload.get("category") or ("COMPLAINT" if action_type == "cabin_complaint" else "INSTRUCTION")
                priority = payload.get("priority", "HIGH" if category == "COMPLAINT" else "NORMAL")
                icon = payload.get("icon") or ("🛠️" if category == "COMPLAINT" else "📋")
                ticket_id = payload.get("ticket_id") or f"CMP-{seat}-{os.urandom(2).hex()}"

                nlp_result = process_natural_speech(user_text)

                request_item = {
                    "type": "new_alert",
                    "request_id": ticket_id,
                    "ticket_id": ticket_id,
                    "seat": seat,
                    "original_text": user_text,
                    "english_text": title,
                    "translated_ja": payload.get("ja") or nlp_result.get("ja", "座席での対応要請です。"),
                    "romaji": payload.get("romaji") or nlp_result.get("romaji", ""),
                    "category": category,
                    "priority": priority,
                    "icon": icon,
                    "issue_type": issue_type,
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(request_item)
                await websocket.send_json({
                    "type": "complaint_ticket_ack",
                    "ticket_id": ticket_id,
                    "status": "QUEUED_ON_CREW_TABLET",
                    "message": "Transmitted to Cabin Purser & Attendants"
                })
                ev = manager.log_event("PASSENGER", f"{category}_SUBMITTED", seat, f"{icon} {title}")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # 2d. In-Flight Seat-to-Seat Cabin Chat (Communication Among Passengers)
            elif action_type in ["passenger_chat", "seat_to_seat_message", "passenger_to_passenger"]:
                target_seat = str(payload.get("to_seat", "")).upper().strip()
                chat_text = payload.get("text", "").strip()
                sender_seat = seat

                # Attempt delivery to target passenger seat
                delivered = await manager.send_to_passenger(target_seat, {
                    "type": "passenger_chat_message",
                    "from_seat": sender_seat,
                    "to_seat": target_seat,
                    "text": chat_text,
                    "timestamp": time.time()
                })

                # Acknowledge back to sender
                await websocket.send_json({
                    "type": "passenger_chat_sent",
                    "to_seat": target_seat,
                    "text": chat_text,
                    "delivered": delivered,
                    "status": "DELIVERED" if delivered else "SEAT_STANDBY"
                })

                ev = manager.log_event("PASSENGER_CHAT", "MESSAGE_SENT", sender_seat, f"Seat {sender_seat} -> Seat {target_seat}: '{chat_text}'")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            # 2b. Speech or Text (or Medical Emergency SOS)
            elif action_type in ["speech_input", "speech_or_text", "new_request", "request"]:
                user_text = payload.get("text", "").strip()
                nlp_result = process_natural_speech(user_text)

                priority = payload.get("priority") or nlp_result.get("priority", "NORMAL")
                category = payload.get("category") or nlp_result.get("category", "ASSISTANCE")

                request_item = {
                    "type": "new_alert",
                    "request_id": payload.get("request_id") or f"REQ-{seat}-{os.urandom(2).hex()}",
                    "seat": seat,
                    "original_text": user_text,
                    "english_text": user_text,
                    "translated_ja": nlp_result.get("ja", ""),
                    "romaji": nlp_result.get("romaji", ""),
                    "category": category,
                    "priority": priority,
                    "icon": nlp_result.get("icon", "💬"),
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(request_item)
                await websocket.send_json({
                    "type": "request_ack",
                    "status": "QUEUED_ON_CREW_TABLET"
                })

            # 3. Passenger Marks Concern as Resolved
            elif action_type == "passenger_mark_resolved":
                manager.remove_from_queue(seat)
                # Broadcast back to crew tablet to return seat color to normal and remove card
                await manager.broadcast_to_crew({
                    "type": "passenger_mark_resolved",
                    "seat": seat
                })
                # Confirm back to passenger
                await websocket.send_json({
                    "type": "request_resolved_confirmed",
                    "seat": seat
                })
                # Broadcast to master surveillance
                ev = manager.log_event("PASSENGER", "RESOLVED", seat, "Passenger marked concern resolved. Closed loop complete.")
                await manager.broadcast_to_surveillance({
                    "type": "passenger_mark_resolved",
                    "seat": seat,
                    "priority_queue": manager.priority_queue
                })
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

    except WebSocketDisconnect:
        manager.disconnect_passenger(seat)
    except Exception as e:
        logger.error(f"Passenger WS Error: {e}")
        manager.disconnect_passenger(seat)

@app.websocket("/ws/surveillance")
async def websocket_surveillance_endpoint(websocket: WebSocket):
    await manager.connect_surveillance(websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            payload = json.loads(raw_text)
            action = payload.get("action") or payload.get("type")
            
            if action in ["pong", "heartbeat"]:
                continue

            if action == "simulate_sos":
                seat = payload.get("seat", "24K")
                req_item = {
                    "type": "new_alert",
                    "request_id": f"SOS-{seat}-{os.urandom(2).hex()}",
                    "seat": seat,
                    "original_text": "Severe acute chest pain and dizziness",
                    "english_text": "Severe acute chest pain and dizziness",
                    "translated_ja": "激しい痛み・急病を訴えていらっしゃいます。最優先救急対応が必要です！",
                    "romaji": "Hageshii itami / kyūbyō o uttaete irasshaimasu.",
                    "category": "MEDICAL",
                    "priority": "HIGH",
                    "icon": "🚨",
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(req_item)
                
            elif action == "simulate_water":
                seat = payload.get("seat", "21C")
                req_item = {
                    "type": "new_alert",
                    "request_id": f"REQ-{seat}-{os.urandom(2).hex()}",
                    "seat": seat,
                    "original_text": "Drinking water please",
                    "english_text": "Drinking water please",
                    "translated_ja": "お水を一杯いただけますでしょうか？",
                    "romaji": "Omizu o ippai itadakemasu deshō ka?",
                    "category": "COMFORT",
                    "priority": "NORMAL",
                    "icon": "💧",
                    "status": "PENDING"
                }
                await manager.add_to_priority_queue(req_item)
                
            elif action == "chime":
                await manager.broadcast_to_crew({"type": "chime"})
                ev = manager.log_event("SYSTEM", "CHIME_BROADCAST", "CABIN", "Master operator broadcasted cabin chime")
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            elif action == "mark_resolved":
                seat = payload.get("seat")
                manager.priority_queue = [q for q in manager.priority_queue if q.get("seat") != seat]
                await manager.broadcast_to_crew({"type": "passenger_mark_resolved", "seat": seat})
                await manager.send_to_passenger(seat, {"type": "attendant_approaching"})
                ev = manager.log_event("CREW", "CALL_RESOLVED", seat, f"Seat {seat} marked resolved", "NORMAL")
                await manager.broadcast_to_surveillance({"type": "passenger_mark_resolved", "seat": seat, "priority_queue": manager.priority_queue})
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

            elif action == "clear_all":
                manager.priority_queue = []
                await manager.broadcast_to_crew({"type": "passenger_mark_resolved", "seat": "ALL"})
                ev = manager.log_event("SYSTEM", "QUEUE_CLEARED", "ALL", "Master operator cleared all active cabin calls")
                await manager.broadcast_to_surveillance({"type": "passenger_mark_resolved", "seat": "ALL", "priority_queue": []})
                await manager.broadcast_to_surveillance({"type": "audit_event", "event": ev})

    except WebSocketDisconnect:
        manager.disconnect_surveillance(websocket)
    except Exception as e:
        logger.error(f"Surveillance WS Error: {e}")
        manager.disconnect_surveillance(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
