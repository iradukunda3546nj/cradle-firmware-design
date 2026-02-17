import time
import threading
import statistics
from urllib.parse import urlparse
import board
import adafruit_dht
import drivers
import subprocess
import requests
import json
import os
import lgpio
import yaml

# ------------------ CONFIG ------------------

PC_IP = "https://www.zolilabs.com"

def normalize_base_url(base: str) -> str:
    parsed = urlparse(base)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return f"https://{base.strip().rstrip('/')}"

BASE_URL = normalize_base_url(PC_IP)
AUDIO_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/upload_audio.php"
DATA_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/receive_data.php"

AUDIO_WAV = "/tmp/cry.wav"
AUDIO_MP3 = "/tmp/cry.mp3"
RECORD_SECONDS = 5

# ------------------ INITIALIZATION ------------------

dht_device = adafruit_dht.DHT22(board.D4)
display = drivers.Lcd()
DEGREE = chr(223)

# ------------------ WEIGHT SYSTEM ------------------

DT = 5
SCK = 6
CONFIG_FILE = "config.yaml"

with open(CONFIG_FILE) as f:
    cfg = yaml.safe_load(f)

zero_offset = cfg["zero_offset"]
cal_factor = cfg["calibration_factor"]

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(chip, DT)
lgpio.gpio_claim_output(chip, SCK)

# Industrial parameters
SAMPLE_COUNT = 20
AUTO_ZERO_THRESHOLD = 0.3   # kg
PRESENCE_THRESHOLD = 2.0    # kg (baby detection)
TEMP_COEFF = -0.002         # kg per °C (simple compensation)

current_weight = 0.0
weight_lock = threading.Lock()

def read_raw():
    while lgpio.gpio_read(chip, DT) == 1:
        time.sleep(0.0005)

    count = 0
    for _ in range(24):
        lgpio.gpio_write(chip, SCK, 1)
        count <<= 1
        lgpio.gpio_write(chip, SCK, 0)
        if lgpio.gpio_read(chip, DT):
            count += 1

    lgpio.gpio_write(chip, SCK, 1)
    lgpio.gpio_write(chip, SCK, 0)

    if count & 0x800000:
        count -= 0x1000000

    return count

def weight_acquisition_thread():
    global current_weight, zero_offset

    while True:
        samples = []
        for _ in range(SAMPLE_COUNT):
            raw = read_raw()
            weight = (raw - zero_offset) / cal_factor
            samples.append(weight)
            time.sleep(0.01)

        median_val = statistics.median(samples)
        filtered = [s for s in samples if abs(s - median_val) < 0.5]

        if not filtered:
            continue

        avg_weight = sum(filtered) / len(filtered)

        # Auto-zero correction (slow drift removal)
        if abs(avg_weight) < AUTO_ZERO_THRESHOLD:
            zero_offset += (avg_weight * cal_factor * 0.001)

        # Temperature compensation
        try:
            temp = dht_device.temperature
            if temp is not None:
                avg_weight += TEMP_COEFF * (temp - 25)
        except:
            pass

        # Commercial rounding
        rounded = round(avg_weight)

        with weight_lock:
            current_weight = max(0, rounded)

        time.sleep(0.2)

# Start weight thread
threading.Thread(target=weight_acquisition_thread, daemon=True).start()

def get_weight():
    with weight_lock:
        return current_weight

# ------------------ LCD ------------------

def lcd_write(text, line):
    display.lcd_display_string(text.ljust(16)[:16], line)

# ------------------ AUDIO ------------------

def record_audio():
    device_options = ["plughw:2,0", "hw:2,0", "default"]

    for device in device_options:
        try:
            cmd = [
                "arecord",
                "-D", device,
                "-d", str(RECORD_SECONDS),
                "-f", "cd",
                AUDIO_WAV
            ]

            result = subprocess.run(cmd, timeout=RECORD_SECONDS + 5)

            if result.returncode == 0:
                return os.path.exists(AUDIO_WAV)

        except:
            pass

    return False

def convert_to_mp3():
    if not os.path.exists(AUDIO_WAV):
        return False

    result = subprocess.run(
        ["lame", "--silent", AUDIO_WAV, AUDIO_MP3]
    )

    return result.returncode == 0 and os.path.exists(AUDIO_MP3)

def upload_audio():
    if not os.path.exists(AUDIO_MP3):
        return None

    try:
        with open(AUDIO_MP3, "rb") as f:
            files = {"audio": ("cry.mp3", f, "audio/mpeg")}
            r = requests.post(AUDIO_UPLOAD_URL, files=files, timeout=20)

        try:
            return r.json().get("audio_url")
        except:
            return None
    except:
        return None

# ------------------ SEND DATA ------------------

def send_data(temp, hum, weight, audio_url):
    payload = {
        "temperature": temp,
        "humidity": hum,
        "weight": weight,
        "presence": weight >= PRESENCE_THRESHOLD,
        "audio_url": audio_url if audio_url else ""
    }

    try:
        requests.post(
            DATA_UPLOAD_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
    except:
        pass

# ------------------ MAIN LOOP ------------------

def main():
    display.lcd_clear()
    lcd_write("Smart BabyCradle", 1)
    lcd_write("System Starting", 2)
    time.sleep(2)

    while True:
        try:
            temp = dht_device.temperature
            hum = dht_device.humidity
            weight = get_weight()

            display.lcd_clear()
            lcd_write("Smart BabyCradle", 1)

            if temp and hum:
                lcd_write(f"Temp:{temp:.1f}{DEGREE}C", 2)
                lcd_write(f"Hum :{hum:.0f}%", 3)
            else:
                lcd_write("Sensor Error", 2)

            lcd_write(f"Weight:{weight} Kg", 4)

            print(f"T:{temp} H:{hum} W:{weight}")

            # Send every 5 seconds
            send_data(temp, hum, weight, None)

            time.sleep(5)

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        lgpio.gpiochip_close(chip)
        display.lcd_clear()
