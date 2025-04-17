import network
import urequests
import machine
import time
import os

WIFI_SSID = 'Meter'
WIFI_PASS = 'kilometer'

VERSION_URL = 'https://raw.githubusercontent.com/ha-rish/pico-ota/refs/heads/main/version.txt'
SCRIPT_URL = 'https://raw.githubusercontent.com/ha-rish/pico-ota/refs/heads/main/main.py'


# ==== HARDWARE SETUP ====
led = machine.Pin("LED", machine.Pin.OUT)

def blink(times=1, delay=0.1):
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

# ==== STEP 1: APPLY PENDING UPDATE ON BOOT ====
def apply_pending_update():
    fs = os.listdir()
    if "update.flag" in fs and "new_main.py" in fs:
        try:
            print("Applying OTA update…")
            if "main.py" in fs:
                os.remove("main.py")
            os.rename("new_main.py", "main.py")
            os.remove("update.flag")
            print("Update applied, rebooting…")
            blink(5, 0.1)
            time.sleep(1)
            machine.reset()
        except Exception as e:
            print("Update apply failed:", e)

apply_pending_update()


# ==== STEP 2: WIFI WITH 10 s TIMEOUT ====
def connect_wifi(timeout_s=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print(f"Connecting to Wi‑Fi (timeout {timeout_s}s)…")
    start = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout_s * 1000:
            print("Wi‑Fi connect timed out")
            return False
        time.sleep(0.5)
    print("Wi‑Fi connected:", wlan.ifconfig())
    return True

# ==== STEP 3: VERSION HELPERS ====
def read_local_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except:
        return "0.0.0"

def get_remote_version():
    try:
        r = urequests.get(VERSION_URL)
        ver = r.text.strip()
        r.close()
        return ver
    except:
        return None

def write_local_version(ver):
    with open("version.txt", "w") as f:
        f.write(ver)

# ==== STEP 4: DOWNLOAD & SCHEDULE OTA ====
def schedule_update():
    try:
        r = urequests.get(SCRIPT_URL)
        with open("new_main.py", "w") as f:
            f.write(r.text)
        r.close()
        # flag for next-boot replacement
        with open("update.flag", "w") as f:
            f.write("1")
        print("Update downloaded, scheduled for next boot")
        blink(3, 0.1)
        time.sleep(1)
        machine.reset()
    except Exception as e:
        print("OTA download failed:", e)

# ==== STEP 5: MAIN LOOP (check every 3 min) ====
def main_loop():
    while True:
        if connect_wifi(10):
            local_v = read_local_version()
            remote_v = get_remote_version()
            if remote_v is not None:
                print(f"Local version: {local_v} | Remote version: {remote_v}")
                if remote_v != local_v:
                    print("New version detected, scheduling update…")
                    write_local_version(remote_v)
                    schedule_update()
                else:
                    print("Already up‑to‑date")
            else:
                print("Could not fetch remote version")
        else:
            print("Skipping OTA check (no Wi‑Fi)")

        # heartbeat for 3 minutes (180 s), blinking once per sec
        for _ in range(360):
            led.toggle()
            time.sleep(0.5)

# kick off
main_loop()
