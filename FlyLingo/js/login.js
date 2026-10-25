// === LOGIN JAVASCRIPT CONTROLLER (100% OFFLINE) ===

let selectedRole = "passenger";

    function setLoginRole(role) {
      selectedRole = role;
      const tabP = document.getElementById("btnRolePass");
      const tabC = document.getElementById("btnRoleCrew");
      const lblId = document.getElementById("lblId");
      const lblPw = document.getElementById("lblPw");
      const hintId = document.getElementById("hintId");
      const hintPw = document.getElementById("hintPw");
      const authId = document.getElementById("authId");
      const authPw = document.getElementById("authPw");

      document.getElementById("errorStrip").style.display = "none";

      if (role === "passenger") {
        tabP.classList.add("active");
        tabC.classList.remove("active");
        lblId.innerText = "Passenger Login ID (3 Letters)";
        lblPw.innerText = "Password (Date of Birth: DDMMYYYY)";
        hintId.innerText = "First 3 letters of your registered name (e.g., AAR for Aarav).";
        hintPw.innerText = "Your Date of Birth in DDMMYYYY format (e.g. 14051998).";
        authId.value = "AAR";
        authPw.value = "14051998";
      } else {
        tabC.classList.add("active");
        tabP.classList.remove("active");
        lblId.innerText = "Crew Login ID (先頭3文字)";
        lblPw.innerText = "Crew Password (生年月日: DDMMYYYY)";
        hintId.innerText = "First 3 letters of crew name (e.g., YUK for Yukiko).";
        hintPw.innerText = "Crew Date of Birth in DDMMYYYY format (e.g. 20081995).";
        authId.value = "YUK";
        authPw.value = "20081995";
      }
    }

    function autoFillLogin(id, pw, role) {
      setLoginRole(role);
      document.getElementById("authId").value = id;
      document.getElementById("authPw").value = pw;
      executeLogin(new Event("submit"));
    }

    // Auto-parse query params
    window.addEventListener("DOMContentLoaded", () => {
      const params = new URLSearchParams(window.location.search);
      const r = params.get("role") || "passenger";
      const id = params.get("id");
      const dob = params.get("dob");

      setLoginRole(r);
      if (id) document.getElementById("authId").value = id;
      if (dob) document.getElementById("authPw").value = dob;
    });

    async function executeLogin(e) {
      if (e && e.preventDefault) e.preventDefault();
      const id = document.getElementById("authId").value.trim().toUpperCase();
      const pw = document.getElementById("authPw").value.trim();

      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: selectedRole, id: id, password: pw })
        });
        const data = await res.json();
        if (data.status === "OK") {
          // Direct to systematic Step 4 Boarding!
          if (selectedRole === "passenger") {
            window.location.href = `/passenger?seat=${data.seat || '24K'}&phase=boarding`;
          } else {
            window.location.href = `/crew?phase=boarding`;
          }
        } else {
          document.getElementById("errorStrip").style.display = "block";
          document.getElementById("errorStrip").innerText = data.message || "Invalid credentials.";
        }
      } catch(err) {
        // Offline direct routing fallback
        if (selectedRole === "passenger") {
          window.location.href = `/passenger?phase=boarding`;
        } else {
          window.location.href = `/crew?phase=boarding`;
        }
      }
    }