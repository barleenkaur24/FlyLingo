// === PASSENGER JAVASCRIPT CONTROLLER (100% OFFLINE) ===

const mySeat = "24K";
    const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    let ws = null;
    let activeReqId = null;

    // Render Compact Seat Map (Rows 20 to 26)
    function renderCabinMap() {
      const container = document.getElementById("mobileCabinRows");
      container.innerHTML = "";
      const rows = [20, 21, 22, 23, 24, 25, 26];

      rows.forEach(r => {
        const line = document.createElement("div");
        line.className = "row-line";

        const label = document.createElement("div");
        label.className = "row-index";
        label.innerText = r;
        line.appendChild(label);

        // Left cluster: A, B, C
        const leftCluster = document.createElement("div");
        leftCluster.className = "seat-cluster";
        ['A', 'B', 'C'].forEach(c => {
          leftCluster.appendChild(createSeatBox(`${r}${c}`));
        });
        line.appendChild(leftCluster);

        // Aisle
        const aisle = document.createElement("div");
        aisle.className = "aisle-walk";
        aisle.innerText = "|";
        line.appendChild(aisle);

        // Right cluster: D, E, K
        const rightCluster = document.createElement("div");
        rightCluster.className = "seat-cluster";
        ['D', 'E', 'K'].forEach(c => {
          rightCluster.appendChild(createSeatBox(`${r}${c}`));
        });
        line.appendChild(rightCluster);

        container.appendChild(line);
      });
    }

    function createSeatBox(seatId) {
      const el = document.createElement("div");
      el.className = "seat-box seated";
      el.id = `m-seat-${seatId}`;
      el.innerText = seatId;
      if (seatId === mySeat) {
        el.classList.add("my-seat");
      }
      return el;
    }

    function setMySeatStatus(statusClass) {
      const el = document.getElementById(`m-seat-${mySeat}`);
      if (el) {
        el.classList.remove("req-green", "req-amber", "req-red");
        if (statusClass) el.classList.add(statusClass);
      }
    }

    // Connect WebSocket
    function connectPassengerSocket() {
      ws = new WebSocket(`${wsProto}//${location.host}/ws/passenger/${mySeat}`);

      ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Passenger WS Received:", data);

        if (data.type === "resolving_started" || data.type === "crew_response") {
          setMySeatStatus("req-amber");
          showOmotenashiStatus(
            "🍵 Attendant En Route (担当乗務員が向かっております)",
            `A cabin attendant is attending to Seat ${mySeat}.<br><em>${data.reply_hi || 'कृपया थोड़ा इंतज़ार करें'}</em>`
          );
        } else if (data.type === "crew_delivered") {
          setMySeatStatus("req-amber");
          showOmotenashiStatus(
            "✅ Assistance Delivered (お届け完了)",
            "Your assistance has been provided. Please confirm resolution below:"
          );
          document.getElementById("resolvePrompt").style.display = "block";
          playChime();
        } else if (data.type === "request_resolved_confirmed") {
          setMySeatStatus(null);
          showOmotenashiStatus(
            "🌸 Resolved (ご用命完了)",
            "Thank you. Japan Airlines wishes you a pleasant flight."
          );
          document.getElementById("resolvePrompt").style.display = "none";
          setTimeout(() => {
            document.getElementById("statusCard").style.display = "none";
          }, 4000);
        }
      };

      ws.onclose = function() {
        setTimeout(connectPassengerSocket, 2000);
      };
    }

    function showOmotenashiStatus(title, msg) {
      const card = document.getElementById("statusCard");
      card.style.display = "block";
      document.getElementById("timelineTitle").innerHTML = title;
      document.getElementById("timelineMsg").innerHTML = msg;
    }

    // Quick Tiles
    function sendQuickTile(key) {
      if (!isServicesUnlocked) {
        alert("🔒 In-Flight Services are locked during boarding. Please wait for cruising altitude (35,000 ft)!");
        return;
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        activeReqId = `REQ-${mySeat}-${Date.now()}`;
        ws.send(JSON.stringify({
          type: "quick_tile",
          key: key,
          seat: mySeat,
          request_id: activeReqId
        }));
        setMySeatStatus("req-green");
        showOmotenashiStatus(
          "💧 Request Dispatched (ご用命を承りました)",
          "Your request is placed in the cabin crew queue. Attendant will assist shortly."
        );
        document.getElementById("resolvePrompt").style.display = "none";
      } else {
        alert("Connecting to local aircraft edge network...");
      }
    }

    // Medical Emergency SOS
    function sendMedicalSOS() {
      if (!isServicesUnlocked) {
        alert("🔒 Please wait until takeoff completes!");
        return;
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        activeReqId = `EM-${mySeat}-${Date.now()}`;
        ws.send(JSON.stringify({
          type: "speech_input",
          text: "Medical Emergency! Severe pain or distress at Seat 24K",
          seat: mySeat,
          priority: "HIGH",
          category: "MEDICAL",
          request_id: activeReqId
        }));
        setMySeatStatus("req-red");
        showOmotenashiStatus(
          "🚨 TOP PRIORITY MEDICAL CALL DISPATCHED",
          "Your emergency call has bypassed standard queues. Attendants & First-Aid Standby dispatched!"
        );
        document.getElementById("resolvePrompt").style.display = "none";
      }
    }

    // Free Text / Spoken Request
    function sendFreeText() {
      if (!isServicesUnlocked) {
        alert("🔒 In-Flight Services unlock upon reaching 35,000 ft cruising altitude!");
        return;
      }
      const input = document.getElementById("freeTextInput");
      const val = input.value.trim();
      if (!val) return;
      if (ws && ws.readyState === WebSocket.OPEN) {
        activeReqId = `REQ-${mySeat}-${Date.now()}`;
        const isMed = val.toLowerCase().includes("dard") || val.toLowerCase().includes("pain") || val.toLowerCase().includes("vomit");
        ws.send(JSON.stringify({
          type: "speech_input",
          text: val,
          seat: mySeat,
          request_id: activeReqId
        }));
        setMySeatStatus(isMed ? "req-red" : "req-green");
        showOmotenashiStatus(
          isMed ? "🚨 Urgent Assistance Called" : "💬 Request Delivered",
          `"${val}" translated into Japanese and queued for cabin attendants.`
        );
        input.value = "";
      }
    }

    // Passenger confirms resolution
    function confirmResolution() {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "passenger_mark_resolved",
          seat: mySeat,
          request_id: activeReqId
        }));
      }
      setMySeatStatus(null);
      showOmotenashiStatus(
        "🌸 Concern Resolved (対応完了)",
        "Thank you! Safe travels to Tokyo Haneda."
      );
      document.getElementById("resolvePrompt").style.display = "none";
      setTimeout(() => {
        document.getElementById("statusCard").style.display = "none";
      }, 3500);
    }

    function playChime() {
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.setValueAtTime(880, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } catch(e) {}
    }

    // Web Speech Offline Fallback
    let recognition = null;
    let isSpeaking = false;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();
      recognition.lang = 'hi-IN';
      recognition.continuous = false;
      recognition.onresult = function(e) {
        const transcript = e.results[0][0].transcript;
        document.getElementById("freeTextInput").value = transcript;
        sendFreeText();
      };
      recognition.onend = function() {
        isSpeaking = false;
        document.getElementById("micButton").classList.remove("active");
        document.getElementById("voiceHeading").innerText = "बोलने के लिए माइक दबाएं";
      };
    }

    function toggleVoiceInput() {
      if (!recognition) {
        const manual = prompt("Type request in Hindi/English (e.g. पानी चाहिए / headache):");
        if (manual) {
          document.getElementById("freeTextInput").value = manual;
          sendFreeText();
        }
        return;
      }
      if (!isSpeaking) {
        try {
          recognition.start();
          isSpeaking = true;
          document.getElementById("micButton").classList.add("active");
          document.getElementById("voiceHeading").innerText = "Listening... बोलिए...";
        } catch(e) {}
      } else {
        recognition.stop();
      }
    }

    // Boarding & Takeoff Systematic Flow
    let pBoardCount = 0;
    let pBoardTimer = null;
    let isServicesUnlocked = false;
    const totalPlaneSeats = 42;

    function startPassengerBoarding() {
      const stepBadge = document.getElementById("stepBadgePhase");
      const fillEl = document.getElementById("passengerBoardFill");
      const subTxt = document.getElementById("boardingSubText");

      pBoardTimer = setInterval(() => {
        if (pBoardCount < totalPlaneSeats) {
          pBoardCount++;
          const pct = Math.round((pBoardCount / totalPlaneSeats) * 100);
          fillEl.style.width = `${pct}%`;
          subTxt.innerText = `Please stow baggage overhead. Boarded: ${pBoardCount} / ${totalPlaneSeats} (${pct}%)`;
        } else {
          clearInterval(pBoardTimer);
          triggerPassengerTakeoff();
        }
      }, 280);
    }

    function skipPassengerTakeoff() {
      if (pBoardTimer) clearInterval(pBoardTimer);
      pBoardCount = totalPlaneSeats;
      document.getElementById("passengerBoardFill").style.width = "100%";
      document.getElementById("boardingSubText").innerText = "All 42 Passengers Boarded (100%)";
      triggerPassengerTakeoff();
    }

    function playTakeoffChimeSound() {
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
        osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.2); // E5
        osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.4); // G5
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.8);
      } catch(e) {}
    }

    function triggerPassengerTakeoff() {
      playTakeoffChimeSound();
      const modal = document.getElementById("phoneTakeoffModal");
      modal.style.display = "flex";

      let alt = 0;
      const altInterval = setInterval(() => {
        alt += 3500;
        if (alt >= 35000) {
          alt = 35000;
          clearInterval(altInterval);
        }
        document.getElementById("phoneAltMeter").innerText = `ALTITUDE: ${alt.toLocaleString()} FT`;
      }, 300);

      setTimeout(() => {
        modal.style.display = "none";
        isServicesUnlocked = true;

        // Unlock services!
        const sec = document.getElementById("servicesSection");
        if (sec) sec.classList.remove("locked-mode");
        const lockNotice = document.getElementById("lockNotice");
        if (lockNotice) lockNotice.style.display = "none";
        const lockTag = document.getElementById("serviceLockTag");
        if (lockTag) { lockTag.innerText = "● Service Active"; lockTag.style.color = "#16A34A"; }

        document.getElementById("boardingCardTitle").innerText = "🛫 Phase 5: Cruising at 35,000 ft (巡航中)";
        document.getElementById("boardingSubText").innerText = "Altitude: 35,000 FT • In-Flight Omotenashi Service is now ACTIVE!";
        document.getElementById("boardingSubText").style.color = "#16A34A";
        document.getElementById("boardingSubText").style.fontWeight = "700";
        document.getElementById("stepBadgePhase").innerText = "5. In-Flight Service";
        playChime();
      }, 3800);
    }

    // Init
    renderCabinMap();
    startPassengerBoarding();
    connectPassengerSocket();