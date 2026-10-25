// === CREW JAVASCRIPT CONTROLLER (100% OFFLINE) ===

const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    let ws = null;
    let priorityQueue = []; // Explicit Priority Queue Array
    const allSeats = [];
    const rows = [20, 21, 22, 23, 24, 25, 26];

    // Build Fuselage Schematic Rows (Rows 20-26, Columns A,B,C | D,E,K)
    function buildSchematic() {
      const stack = document.getElementById("schematicStack");
      stack.innerHTML = "";

      rows.forEach(r => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "schematic-row";

        const marker = document.createElement("div");
        marker.className = "row-marker";
        marker.innerText = r;
        rowDiv.appendChild(marker);

        // Left 3: A, B, C
        const leftGroup = document.createElement("div");
        leftGroup.className = "seat-cluster-3";
        ['A', 'B', 'C'].forEach(c => {
          const sId = `${r}${c}`;
          allSeats.push(sId);
          leftGroup.appendChild(createTabletSeat(sId));
        });
        rowDiv.appendChild(leftGroup);

        // Aisle
        const aisle = document.createElement("div");
        aisle.className = "schematic-aisle";
        aisle.innerText = "|";
        rowDiv.appendChild(aisle);

        // Right 3: D, E, K
        const rightGroup = document.createElement("div");
        rightGroup.className = "seat-cluster-3";
        ['D', 'E', 'K'].forEach(c => {
          const sId = `${r}${c}`;
          allSeats.push(sId);
          rightGroup.appendChild(createTabletSeat(sId));
        });
        rowDiv.appendChild(rightGroup);

        stack.appendChild(rowDiv);
      });
    }

    function createTabletSeat(sId) {
      const el = document.createElement("div");
      el.className = "tablet-seat";
      el.id = `tab-seat-${sId}`;
      el.innerText = sId;
      el.onclick = () => focusQueueCard(sId);
      return el;
    }

    // Boarding Simulation (12 seconds)
    let boardedTotal = 0;
    let boardTimer = null;

    function runBoardingSequence() {
      const total = allSeats.length; // 42 seats
      const delay = (12 * 1000) / total; // ~280ms per passenger

      boardTimer = setInterval(() => {
        if (boardedTotal < total) {
          const sId = allSeats[boardedTotal];
          const el = document.getElementById(`tab-seat-${sId}`);
          if (el) el.classList.add("boarded");
          boardedTotal++;

          const pct = Math.round((boardedTotal / total) * 100);
          document.getElementById("tabletBoardFill").style.width = `${pct}%`;
          document.getElementById("boardProgressLabel").innerText = `Boarded: ${boardedTotal} / ${total} (${pct}%)`;
        } else {
          clearInterval(boardTimer);
          launchTakeoffSequence();
        }
      }, delay);
    }

    function skipToTakeoffNow() {
      if (boardTimer) clearInterval(boardTimer);
      allSeats.forEach(s => {
        const el = document.getElementById(`tab-seat-${s}`);
        if (el) el.classList.add("boarded");
      });
      document.getElementById("tabletBoardFill").style.width = "100%";
      document.getElementById("boardProgressLabel").innerText = "Boarded: 42 / 42 (100%)";
      launchTakeoffSequence();
    }

    function launchTakeoffSequence() {
      playTakeoffChime();
      const modal = document.getElementById("takeoffModalOverlay");
      modal.style.display = "flex";

      let alt = 0;
      const altTimer = setInterval(() => {
        alt += 3500;
        if (alt >= 35000) {
          alt = 35000;
          clearInterval(altTimer);
        }
        document.getElementById("altimeterText").innerText = `ALTITUDE: ${alt.toLocaleString()} FT`;
      }, 300);

      setTimeout(() => {
        modal.style.display = "none";
        document.getElementById("tabletPhaseStatus").innerText = "Cruising at 35,000 ft (巡航中・サービス開始)";
        document.getElementById("tabletPhaseStatus").style.color = "#16A34A";
        playChime();
      }, 4200);
    }

    // Connect WebSocket
    function connectCrewTabletSocket() {
      ws = new WebSocket(`${wsProto}//${location.host}/ws/crew`);

      ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Crew WS Event:", data);

        if (data.type === "new_alert" || data.type === "incoming_request") {
          enqueueRequest(data);
        } else if (data.type === "passenger_mark_resolved") {
          dequeueRequest(data.seat);
        }
      };

      ws.onclose = function() {
        setTimeout(connectCrewTabletSocket, 2000);
      };
    }

    // Add Request to Priority Queue Array (Medical Emergenices go to Index 0)
    function enqueueRequest(req) {
      playChime();

      // Remove existing from same seat
      priorityQueue = priorityQueue.filter(q => q.seat !== req.seat);

      const isEmergency = req.priority === "HIGH" || req.category === "MEDICAL";
      if (isEmergency) {
        priorityQueue.unshift(req); // Pinned to Position #1
        setTabletSeatColor(req.seat, "alert-red");
        showEmergencyBanner(req);
        playEmergencyAlarm();
      } else {
        // Insert after existing emergencies
        const firstNormalIdx = priorityQueue.findIndex(q => q.priority !== "HIGH" && q.category !== "MEDICAL");
        if (firstNormalIdx === -1) {
          priorityQueue.push(req);
        } else {
          priorityQueue.splice(firstNormalIdx, 0, req);
        }
        setTabletSeatColor(req.seat, "call-green");
      }

      renderQueueView();
    }

    function setTabletSeatColor(seatId, stateClass) {
      const el = document.getElementById(`tab-seat-${seatId}`);
      if (el) {
        el.classList.remove("call-green", "resolving-amber", "alert-red");
        if (stateClass) el.classList.add(stateClass);
      }
    }

    function renderQueueView() {
      const list = document.getElementById("queueFeedList");
      const emptyNotice = document.getElementById("emptyListNotice");
      const badge = document.getElementById("queueBadgeCount");

      badge.innerText = `${priorityQueue.length} Active`;

      if (priorityQueue.length === 0) {
        list.innerHTML = "";
        list.appendChild(emptyNotice);
        emptyNotice.style.display = "block";
        document.getElementById("emBannerCard").style.display = "none";
        return;
      }

      emptyNotice.style.display = "none";
      list.innerHTML = "";

      priorityQueue.forEach((req, idx) => {
        const isEm = req.priority === "HIGH" || req.category === "MEDICAL";
        const isResolving = req.status === "RESOLVING";
        const cardClass = isEm ? "HIGH" : (isResolving ? "RESOLVING" : "NORMAL");

        const card = document.createElement("div");
        card.className = `q-request-item ${cardClass}`;
        card.id = `qcard-${req.seat}`;

        card.innerHTML = `
          <div class="q-item-top">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="seat-badge-box">SEAT ${req.seat}</span>
              <span class="q-index-pill">Queue #${idx + 1}</span>
            </div>
            <span class="priority-badge-pill ${cardClass}">
              ${isEm ? '🚨 EMERGENCY [TOP PRIORITY]' : (isResolving ? '● IN PROGRESS' : '● NORMAL SERVICE')}
            </span>
          </div>

          <div class="keigo-phrase-jp">${req.translated_ja || 'お伺いいたします。'}</div>
          <div class="romaji-reading-sub">${req.romaji || ''}</div>
          <div class="passenger-sanitized-speech">
            <strong>Passenger Request (Masked):</strong> "${req.original_text || req.english_text || ''}"
          </div>

          <div class="q-btn-group">
            <button class="btn-tablet-action btn-tts" onclick="speakJapaneseKeigo('${req.translated_ja || ''}')">
              🔊 読み上げ (Hear JA)
            </button>
            <button class="btn-tablet-action btn-resolving" onclick="startResolvingTablet('${req.seat}', '${req.request_id || ''}')">
              ⏳ 対応開始 (Start Resolving)
            </button>
            <button class="btn-tablet-action btn-delivered" onclick="markDeliveredTablet('${req.seat}', '${req.request_id || ''}')">
              ✓ 提供完了 (Deliver to Seat)
            </button>
          </div>
        `;
        list.appendChild(card);
      });
    }

    // Crew Action: Start Resolving
    function startResolvingTablet(seat, reqId) {
      setTabletSeatColor(seat, "resolving-amber");
      const item = priorityQueue.find(q => q.seat === seat);
      if (item) item.status = "RESOLVING";

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "crew_reply",
          seat: seat,
          request_id: reqId,
          reply_ja: "ただいま担当乗務員が向かっております",
          reply_hi: "केबिन क्रू आपकी सीट की तरफ आ रहा है"
        }));
      }
      renderQueueView();
    }

    // Crew Action: Mark Delivered (prompts passenger)
    function markDeliveredTablet(seat, reqId) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "crew_delivered",
          seat: seat,
          request_id: reqId
        }));
      }
      alert(`Delivered to Seat ${seat}! Passenger will confirm resolution.`);
    }

    // Dequeue upon resolution
    function dequeueRequest(seat) {
      priorityQueue = priorityQueue.filter(q => q.seat !== seat);
      setTabletSeatColor(seat, null);
      renderQueueView();
      if (!priorityQueue.some(q => q.priority === "HIGH" || q.category === "MEDICAL")) {
        document.getElementById("emBannerCard").style.display = "none";
      }
    }

    function showEmergencyBanner(req) {
      const banner = document.getElementById("emBannerCard");
      banner.style.display = "block";
      document.getElementById("emBannerText").innerText = 
        `🚨 EMERGENCY at Seat ${req.seat}: "${req.original_text || req.english_text}". Pinned at Position #1! Standby First-Aid Kit.`;
    }

    function focusQueueCard(sId) {
      const card = document.getElementById(`qcard-${sId}`);
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.style.transform = "scale(1.02)";
        setTimeout(() => { card.style.transform = "scale(1)"; }, 350);
      }
    }

    // Fast Demo Calls
    function simulateCall(seat, ja, romaji, orig, priority, cat) {
      enqueueRequest({
        seat: seat,
        request_id: `DEMO-${seat}-${Date.now()}`,
        translated_ja: ja,
        romaji: romaji,
        original_text: orig,
        priority: priority,
        category: cat,
        status: "PENDING"
      });
    }

    function resetAllDemoSeats() {
      priorityQueue = [];
      allSeats.forEach(s => setTabletSeatColor(s, null));
      renderQueueView();
      document.getElementById("emBannerCard").style.display = "none";
    }

    // Sound Synthesizers (Web Audio API - 100% Offline)
    function playChime() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
        osc.start();
        osc.stop(ctx.currentTime + 0.5);
      } catch(e) {}
    }

    function playEmergencyAlarm() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        [0, 0.2, 0.4].forEach((delay, idx) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.type = "sawtooth";
          osc.frequency.setValueAtTime(idx % 2 === 0 ? 880 : 1174, ctx.currentTime + delay);
          gain.gain.setValueAtTime(0.3, ctx.currentTime + delay);
          gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + delay + 0.18);
          osc.start(ctx.currentTime + delay);
          osc.stop(ctx.currentTime + delay + 0.18);
        });
      } catch(e) {}
    }

    function playTakeoffChime() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.2);
        osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.4);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
        osc.start();
        osc.stop(ctx.currentTime + 0.8);
      } catch(e) {}
    }

    function speakJapaneseKeigo(text) {
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'ja-JP';
        window.speechSynthesis.speak(u);
      }
    }

    // Init
    buildSchematic();
    runBoardingSequence();
    connectCrewTabletSocket();