import asyncio
import websockets
import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

async def test_3seats_and_chat():
    print("=====================================================================")
    print("TEST: SIMULTANEOUS 3-PASSENGER REQUESTS & IN-FLIGHT SEAT-TO-SEAT CHAT")
    print("=====================================================================\n")

    # Clear priority queue
    urllib.request.urlopen(f"{BASE_URL}/api/clear-queue")

    uri_crew = "ws://127.0.0.1:8000/ws/crew"
    uri_pax1 = "ws://127.0.0.1:8000/ws/passenger/24K"
    uri_pax2 = "ws://127.0.0.1:8000/ws/passenger/12A"
    uri_pax3 = "ws://127.0.0.1:8000/ws/passenger/14B"

    async with websockets.connect(uri_crew) as ws_crew, \
               websockets.connect(uri_pax1) as ws_pax1, \
               websockets.connect(uri_pax2) as ws_pax2, \
               websockets.connect(uri_pax3) as ws_pax3:

        print("1. [PASS] Connected 4 simultaneous WebSockets:")
        print("   - Crew Tablet")
        print("   - Passenger 1: Seat 24K (Aarav)")
        print("   - Passenger 2: Seat 12A (Priya)")
        print("   - Passenger 3: Seat 14B (Rajesh)")

        # -------------------------------------------------------------
        # TEST 1: Simultaneous Requests from all 3 seats
        # -------------------------------------------------------------
        print("\n2. Sending simultaneous requests from all 3 passenger seats:")

        # Seat 24K sends custom request
        req1 = {
            "type": "speech_input",
            "seat": "24K",
            "text": "Can I please get hot green tea with honey?",
            "request_id": "REQ-24K-TEA",
            "priority": "NORMAL",
            "category": "COMFORT"
        }
        await ws_pax1.send(json.dumps(req1))
        ack1 = json.loads(await asyncio.wait_for(ws_pax1.recv(), timeout=2.0))
        print("   [Seat 24K] -> Sent custom request: 'Can I please get hot green tea with honey?' (ACK received)")

        # Seat 12A sends custom complaint
        req2 = {
            "type": "cabin_complaint",
            "seat": "12A",
            "ticket_id": "CMP-12A-LIGHT",
            "title": "Reading light above seat 12A is flickering",
            "text": "The reading light above seat 12A is flickering and not turning off",
            "issue_type": "reading_light",
            "category": "COMPLAINT",
            "priority": "HIGH"
        }
        await ws_pax2.send(json.dumps(req2))
        ack2 = json.loads(await asyncio.wait_for(ws_pax2.recv(), timeout=2.0))
        print("   [Seat 12A] -> Sent custom complaint: 'Reading light is flickering' (ACK received)")

        # Seat 14B sends Indian Medicine report
        req3 = {
            "type": "speech_input",
            "seat": "14B",
            "text": "Elderly passenger carrying Vertin 16mg blister pack for severe vertigo",
            "request_id": "REQ-14B-MED",
            "priority": "HIGH",
            "category": "MEDICAL"
        }
        await ws_pax3.send(json.dumps(req3))
        ack3 = json.loads(await asyncio.wait_for(ws_pax3.recv(), timeout=2.0))
        print("   [Seat 14B] -> Sent medicine alert: 'Vertin 16mg' (ACK received)")

        # -------------------------------------------------------------
        # TEST 2: Crew Tablet receives ALL 3 simultaneously in queue
        # -------------------------------------------------------------
        print("\n3. Verifying Crew Tablet receives all 3 requests simultaneously:")
        crew_alerts = []
        for _ in range(3):
            msg = json.loads(await asyncio.wait_for(ws_crew.recv(), timeout=3.0))
            crew_alerts.append(msg)

        alert_seats = [a.get("seat") for a in crew_alerts]
        print(f"   [Crew Tablet] Received {len(crew_alerts)} alerts for seats: {alert_seats}")
        assert "24K" in alert_seats, "Seat 24K missing from crew queue"
        assert "12A" in alert_seats, "Seat 12A missing from crew queue"
        assert "14B" in alert_seats, "Seat 14B missing from crew queue"

        # Verify custom text is preserved for all
        for a in crew_alerts:
            orig = a.get("original_text") or a.get("english_text")
            ja = a.get("translated_ja")
            print(f"   -> Seat {a['seat']}: Custom Text='{orig}' | Japanese='{ja}' | Priority={a['priority']}")
            assert len(orig) > 5, f"Original custom text lost for seat {a['seat']}"

        print("   [PASS] All 3 seats are queued simultaneously with full custom text visible to crew!")

        # -------------------------------------------------------------
        # TEST 3: In-Flight Seat-to-Seat Chat between Passengers
        # -------------------------------------------------------------
        print("\n4. Testing In-Flight Seat-to-Seat Cabin Chat (Zero Internet):")

        # Seat 24K sends message to Seat 12A
        chat_msg = {
            "type": "passenger_chat",
            "from_seat": "24K",
            "to_seat": "12A",
            "text": "Hi Priya, are you comfortable in row 12?"
        }
        await ws_pax1.send(json.dumps(chat_msg))

        # Pax 1 receives delivery ack
        chat_ack = json.loads(await asyncio.wait_for(ws_pax1.recv(), timeout=2.0))
        assert chat_ack["type"] == "passenger_chat_sent"
        assert chat_ack["delivered"] is True
        print(f"   [Seat 24K -> Seat 12A] Dispatched chat: '{chat_msg['text']}' (Delivery Status: {chat_ack['status']})")

        # Pax 2 (Seat 12A) receives the message
        pax2_incoming = json.loads(await asyncio.wait_for(ws_pax2.recv(), timeout=2.0))
        assert pax2_incoming["type"] == "passenger_chat_message"
        assert pax2_incoming["from_seat"] == "24K"
        assert pax2_incoming["text"] == "Hi Priya, are you comfortable in row 12?"
        print(f"   [Seat 12A] Successfully received chat from Seat {pax2_incoming['from_seat']}: '{pax2_incoming['text']}'")

        # Seat 12A replies back to Seat 24K
        reply_msg = {
            "type": "passenger_chat",
            "from_seat": "12A",
            "to_seat": "24K",
            "text": "Yes Aarav! Just ordered tea, flight attendants are on the way."
        }
        await ws_pax2.send(json.dumps(reply_msg))
        await ws_pax2.recv() # ack

        # Pax 1 (Seat 24K) receives the reply
        pax1_incoming = json.loads(await asyncio.wait_for(ws_pax1.recv(), timeout=2.0))
        assert pax1_incoming["type"] == "passenger_chat_message"
        assert pax1_incoming["from_seat"] == "12A"
        assert "Yes Aarav!" in pax1_incoming["text"]
        print(f"   [Seat 24K] Successfully received reply from Seat {pax1_incoming['from_seat']}: '{pax1_incoming['text']}'")

        print("   [PASS] 2-Way In-Flight Seat-to-Seat Cabin Chat verified 100% operational!")

        # -------------------------------------------------------------
        # TEST 4: Crew Resolves One Seat at a Time
        # -------------------------------------------------------------
        print("\n5. Testing Instant At-Seat Crew Resolution Loop for Seat 12A:")
        crew_res = {
            "type": "issue_resolved_by_crew",
            "seat": "12A",
            "ticket_id": "CMP-12A-LIGHT",
            "action_taken": "Reading Light Switched and Confirmed Normal",
            "action_taken_ja": "読書灯の不具合を点検し、正常動作を確認いたしました。",
            "crew_name": "Yukiko Tanaka (田中 ゆきこ)"
        }
        await ws_crew.send(json.dumps(crew_res))

        pax2_cert = json.loads(await asyncio.wait_for(ws_pax2.recv(), timeout=2.0))
        assert pax2_cert["type"] == "issue_resolved_by_crew"
        assert pax2_cert["status"] == "RESOLVED"
        print(f"   [Seat 12A] Received Live Resolution Certificate: '{pax2_cert['action_taken_ja']}'")

    print("\n=====================================================================")
    print("ALL TESTS PASSED: 3 SIMULTANEOUS SEATS + SEAT-TO-SEAT CHAT 100% READY!")
    print("=====================================================================")

if __name__ == "__main__":
    asyncio.run(test_3seats_and_chat())
