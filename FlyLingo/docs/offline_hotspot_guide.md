# 📡 How to Set Up the 100% Offline Aircraft Hotspot

This is the exact configuration Person 2 must set up during the hackathon.

## Step 1: Turn ON Windows Mobile Hotspot
1. Press `Win + I` to open **Settings**.
2. Click **Network & internet** $\rightarrow$ **Mobile hotspot**.
3. Toggle it to **ON**.
4. Click **Edit** and set:
   - **Network name:** `JAL_InFlight_WiFi`
   - **Network password:** `skyconnect123`
   - **Band:** `Any available` or `2.4 GHz / 5 GHz`

## Step 2: Disconnect from Real Internet (The Stunt!)
1. Turn off your Wi-Fi internet connection or unplug Ethernet so there is **NO INTERNET ACCESS**.
2. The laptop will still broadcast the local hotspot `JAL_InFlight_WiFi`.

## Step 3: Find your Local IP Address
1. Open PowerShell or Command Prompt.
2. Type `ipconfig` and press Enter.
3. Look for **Wireless LAN adapter Local Area Connection* ...** or **Wi-Fi**:
   - Find line: `IPv4 Address. . . . . . . . . . . : 192.168.137.1` (or similar).
   - This IP address is your **Aircraft Server Host Address**.

## Step 4: Tell Teammates to Connect
- Person 3 (Passenger Phone) connects to Wi-Fi `JAL_InFlight_WiFi`.
- Person 4 (Crew Tablet) connects to Wi-Fi `JAL_InFlight_WiFi`.
- They open:
  - `http://192.168.137.1:8000/passenger`
  - `http://192.168.137.1:8000/crew`

All communication runs entirely within the local Wi-Fi router with **0 KB consumed over satellite internet**.
