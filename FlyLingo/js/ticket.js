// === TICKET JAVASCRIPT CONTROLLER (100% OFFLINE) ===

// Fetch live local Wi-Fi IP so the exact phone URL is displayed
    fetch("/api/network-info")
      .then(res => res.json())
      .then(data => {
        if (data.phone_url) {
          document.getElementById("phoneUrlNotice").innerText = data.phone_url;
          document.getElementById("directFormLink").href = data.phone_url;
        }
      })
      .catch(() => {
        document.getElementById("phoneUrlNotice").innerText = `http://${location.host}/form`;
      });