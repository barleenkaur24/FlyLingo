# ✈️ FlyLingo — System Architecture & Data Flow

This document details the complete end-to-end architecture of FlyLingo for Japan Airlines (JL740 Delhi &rarr; Tokyo Narita).

---

## 1. High-Level Offline Edge Network Topology

```
+-----------------------------------------------------------------------------------+
|                           AIR-GAPPED BOEING 787 CABIN                             |
|                                                                                   |
|  +----------------------------+                 +------------------------------+  |
|  |     PASSENGER SMARTPHONE   |                 |      CABIN CREW TABLET       |  |
|  |  (Personal iOS / Android)  |                 |      (iPad / Windows Tab)    |  |
|  |    IP: 172.17.132.123      |                 |       IP: 172.17.131.85      |  |
|  +-------------+--------------+                 +--------------+---------------+  |
|                |                                               |                  |
|                |  Local Wi-Fi (No Internet Required)           |                  |
|                v                                               v                  |
|  +-----------------------------------------------------------------------------+  |
|  |                     ONBOARD EDGE SERVER (PORT 8000)                         |  |
|  |                                                                             |  |
|  |  +--------------------+   +-----------------------+   +------------------+  |  |
|  |  |  DYNAMIC LAN IP    |   | ZERO-KNOWLEDGE        |   | PRIORITY QUEUE   |  |  |
|  |  |  AUTO-DETECTOR     |   | PRIVACY FIREWALL      |   | ARRAY (INDEX #0) |  |  |
|  |  |  (172.17.131.85)   |   | (PII Stripper)        |   | (Medical SOS)    |  |  |
|  |  +--------------------+   +-----------------------+   +------------------+  |  |
|  |                                                                             |  |
|  |  +--------------------+   +-----------------------+   +------------------+  |  |
|  |  |  WEBSOCKET BROKER  |   | RULE-BASED KEIGO NLP  |   | QR CODE ENGINE   |  |  |
|  |  |  (/ws/passenger)   |   | (Sonkeigo/Kenjougo)   |   | (Pillow/PNG Gen) |  |  |
|  |  +--------------------+   +-----------------------+   +------------------+  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. The 6-Phase Systematic Flight Lifecycle

```
[Phase 1: Boarding Pass & QR]
  │  Laptop displays authentic JAL Ticket encoding LAN IP URL:
  │  http://172.17.131.85:8000/form
  ▼
[Phase 2: Passenger Registration on Phone]
  │  Passenger scans QR with smartphone camera.
  │  Inputs: Full Name + DOB (DD/MM/YYYY) + Seat (24K).
  │  Auto-computes ID (First 3 letters: AAR) & Password (DOB: 14051998).
  ▼
[Phase 3: Flight Gate Authentication]
  │  Validates calculated ID & DOB against passenger manifest.
  │  Fast-track demo buttons available for instant judging.
  ▼
[Phase 4: Passenger Boarding Simulation]
  │  Cabin is boarded. Countdown timer: 10–12 seconds.
  │  Service request tiles are strictly locked with 🔒 icons.
  ▼
[Phase 5: Boeing 787 Takeoff Animation]
  │  Altimeter HUD climbs from 0 ft -> 35,000 ft cruising altitude.
  │  Plays hardware-synthesized cabin seatbelt chime.
  ▼
[Phase 6: In-Flight Service & 2-Way Resolution Loop]
  │  Service tiles unlock: Water, Blanket, Meal, Customs, Medical SOS.
  │  Passenger taps tile or speaks -> Sent via local WebSocket.
  │  Crew tablet receives alert: Seat 24K highlights Green / Red.
  │  Crew taps "Resolving (対応中)" -> Passenger receives confirmation.
  │  Passenger taps "Mark as Resolved" -> Queue clears, seat resets.
```

---

## 3. Zero-Knowledge Privacy Isolation

| Field | Captured at Registration | Shared with Crew Tablet? | Why? |
|---|---|---|---|
| **Passenger Full Name** | Yes | ❌ Stripped | Privacy compliance |
| **Passport Number** | Yes | ❌ Stripped | Anti-theft & PII protection |
| **Phone Number / Email** | Yes | ❌ Stripped | GDPR / Japanese APPI Act |
| **Seat Number (e.g. 24K)** | Yes | ✅ Shared | Attendant needs physical location |
| **Request Category** | N/A (Dynamic) | ✅ Shared | Attendant needs item type |
| **Urgency / Priority** | N/A (Dynamic) | ✅ Shared | Escalation in Priority Queue |
| **Spoken Text / Translation** | N/A (Dynamic) | ✅ Shared | Understanding passenger need |
