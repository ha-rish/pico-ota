import network
import urequests
import machine
import time

WIFI_SSID = 'Meter'
WIFI_PASS = 'kilometer'

VERSION_URL = 'https://raw.githubusercontent.com/ha-rish/pico-ota/refs/heads/main/version.txt'
SCRIPT_URL = 'https://raw.githubusercontent.com/ha-rish/pico-ota/refs/heads/main/main.py'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi connected:", wlan.ifconfig())

def read_local_version():
    try:
        with open('version.txt', 'r') as f:
            return f.read().strip()
    except:
        return '0.0.0'

def get_remote_version():
    try:
        res = urequests.get(VERSION_URL)
        remote_ver = res.text.strip()
        res.close()
        return remote_ver
    except:
        return None

def download_update():
    try:
        res = urequests.get(SCRIPT_URL)
        with open('main.py', 'w') as f:
            f.write(res.text)
        res.close()
        print("Update downloaded.")
        return True
    except Exception as e:
        print("Update failed:", e)
        return False

def write_version(ver):
    with open('version.txt', 'w') as f:
        f.write(ver)

def blink_led(times=5, delay=0.5):
    led = machine.Pin("LED", machine.Pin.OUT)
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)
      
def reboot():
    print("Rebooting to run new version...")
    time.sleep(2)
    machine.reset()

# === Main Flow ===
connect_wifi()
while True:
    blink_led()
    time.sleep(10)
    blink_led(20,0.2)
    time.sleep(1)
    blink_led(5,2)
    time.sleep(1)
    local_version = read_local_version()
    remote_version = get_remote_version()
    
    if remote_version and remote_version != local_version:
        print(f"New version available: {remote_version} (current: {local_version})")
        if download_update():
            write_version(remote_version)
            reboot()
    else:
        print("No update needed.")
