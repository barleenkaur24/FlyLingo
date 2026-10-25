// === FORM JAVASCRIPT CONTROLLER (100% OFFLINE) ===

let activeRole = "passenger";

    function switchRole(role) {
      activeRole = role;
      const tabP = document.getElementById("tabPass");
      const tabC = document.getElementById("tabCrew");
      const pSec = document.getElementById("passengerSection");
      const cSec = document.getElementById("crewSection");
      const nameLbl = document.getElementById("lblFullName");

      if (role === "passenger") {
        tabP.classList.add("active");
        tabC.classList.remove("active");
        pSec.style.display = "block";
        cSec.style.display = "none";
        nameLbl.innerText = "Passenger Full Name (氏名)";
        document.getElementById("inputName").value = "Aarav Sharma";
        document.getElementById("inputDob").value = "1998-05-14";
      } else {
        tabC.classList.add("active");
        tabP.classList.remove("active");
        pSec.style.display = "none";
        cSec.style.display = "block";
        nameLbl.innerText = "Cabin Attendant Name (乗務員氏名)";
        document.getElementById("inputName").value = "Yukiko Tanaka";
        document.getElementById("inputDob").value = "1995-08-20";
      }
      calculateCreds();
    }

    function calculateCreds() {
      const name = document.getElementById("inputName").value.trim().toUpperCase();
      const dob = document.getElementById("inputDob").value;
      
      let id = name.replace(/[^A-Z]/g, "").slice(0, 3);
      if (id.length < 3) id = (id + "XXX").slice(0, 3);

      let pw = "14051998";
      if (dob && dob.includes("-")) {
        const parts = dob.split("-");
        pw = parts[2] + parts[1] + parts[0]; // DDMMYYYY
      }

      document.getElementById("badgeId").innerText = id;
      document.getElementById("badgePw").innerText = pw;
      return { id, pw };
    }

    function fillQuickDemo() {
      if (activeRole === "passenger") {
        document.getElementById("inputName").value = "Aarav Sharma";
        document.getElementById("inputDob").value = "1998-05-14";
        document.getElementById("selectSeat").value = "24K";
      } else {
        document.getElementById("inputName").value = "Yukiko Tanaka";
        document.getElementById("inputDob").value = "1995-08-20";
        document.getElementById("crewEmpId").value = "JAL-7809";
      }
      calculateCreds();
    }

    async function submitRegistration(e) {
      e.preventDefault();
      const creds = calculateCreds();
      const name = document.getElementById("inputName").value.trim();
      const dob = document.getElementById("inputDob").value;
      const seat = activeRole === "passenger" ? document.getElementById("selectSeat").value : "CREW-TABLET";

      try {
        await fetch("/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            role: activeRole,
            name: name,
            dob: dob,
            id: creds.id,
            password: creds.pw,
            seat: seat
          })
        });
      } catch(err) {}

      document.getElementById("mId").innerText = creds.id;
      document.getElementById("mPw").innerText = creds.pw;
      document.getElementById("btnAdvanceLogin").href = `/login?role=${activeRole}&id=${creds.id}&dob=${creds.pw}`;
      document.getElementById("advanceModal").style.display = "flex";
    }

    calculateCreds();