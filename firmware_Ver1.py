import time
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
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        base = base.strip().rstrip('/')
        base_url = f"https://{base}"
    return base_url.rstrip('/')

BASE_URL = normalize_base_url(PC_IP)
print(f"Using server base URL: {BASE_URL}")

AUDIO_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/upload_audio.php"
DATA_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/receive_data.php"

AUDIO_WAV = "/tmp/cry.wav"
AUDIO_MP3 = "/tmp/cry.mp3"
RECORD_SECONDS = 5

# ------------------ INITIALIZATION ------------------

dht_device = adafruit_dht.DHT22(board.D4)
display = drivers.Lcd()
DEGREE = chr(223)

# -------- WEIGHT SENSOR INITIALIZATION --------

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

class KalmanFilter:
    def __init__(self):
        self.q = 0.02
        self.r = 0.5
        self.x = 0
        self.p = 1

    def update(self, measurement):
        self.p += self.q
        k = self.p / (self.p + self.r)
        self.x += k * (measurement - self.x)
        self.p *= (1 - k)
        return self.x

kf = KalmanFilter()

def get_weight():
    """Read real weight from HX711 (kg)"""
    try:
        raw = read_raw()
        weight = (raw - zero_offset) / cal_factor
        filtered_weight = kf.update(weight)
        return round(filtered_weight, 3)
    except Exception as e:
        print(f"Weight read error: {e}")
        return 0.0

# ------------------ LCD FUNCTION ------------------

def lcd_write(text, line):
    display.lcd_display_string(text.ljust(16)[:16], line)

# ------------------ AUDIO FUNCTIONS ------------------

def record_audio():
    try:
        lcd_write("Recording...", 4)

        device_options = ["plughw:2,0", "hw:2,0", "default"]
        success = False

        for device in device_options:
            try:
                cmd = [
                    "arecord",
                    "-D", device,
                    "-d", str(RECORD_SECONDS),
                    "-f", "cd",
                    AUDIO_WAV
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=RECORD_SECONDS + 5
                )

                if result.returncode == 0:
                    success = True
                    break

            except:
                pass

        return success and os.path.exists(AUDIO_WAV)

    except Exception as e:
        print(f"Error in record_audio: {e}")
        return False

def convert_to_mp3():
    try:
        if not os.path.exists(AUDIO_WAV):
            return False

        result = subprocess.run(
            ["lame", "--silent", AUDIO_WAV, AUDIO_MP3],
            capture_output=True
        )

        return result.returncode == 0 and os.path.exists(AUDIO_MP3)

    except:
        return False

def upload_audio():
    try:
        if not os.path.exists(AUDIO_MP3):
            return None

        lcd_write("Uploading audio", 4)

        with open(AUDIO_MP3, "rb") as f:
            r = requests.post(AUDIO_UPLOAD_URL, files={"audio": f}, timeout=30)

        if r.status_code == 200:
            return r.json().get("audio_url")
        return None

    except Exception as e:
        print(f"Upload error: {e}")
        return None

def send_data(temp, hum, weight, audio_url):
    try:
        lcd_write("Sending data", 4)

        payload = {
            "temperature": temp,
            "humidity": hum,
            "weight": weight,
            "audio_url": audio_url if audio_url else ""
        }

        headers = {"Content-Type": "application/json"}
        requests.post(
            DATA_UPLOAD_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )

    except Exception as e:
        print(f"Error in send_data: {e}")

# ------------------ MAIN LOOP ------------------

def main():
    try:
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

                if temp is not None and hum is not None:
                    lcd_write(f"Temp:{temp:.1f}{DEGREE}C", 2)
                    lcd_write(f"Hum :{hum:.0f}%", 3)
                else:
                    lcd_write("Sensor Error", 2)
                    lcd_write("Check DHT22", 3)

                lcd_write(f"Poids:{weight:.3f} Kg", 4)

                print(f"Temp: {temp}, Hum: {hum}, Weight: {weight}")

                time.sleep(3)

                if record_audio():
                    if convert_to_mp3():
                        audio_url = upload_audio()
                        send_data(temp, hum, weight, audio_url)
                    else:
                        send_data(temp, hum, weight, None)
                else:
                    send_data(temp, hum, weight, None)

                for file in [AUDIO_WAV, AUDIO_MP3]:
                    if os.path.exists(file):
                        os.remove(file)

                time.sleep(10)

            except RuntimeError as err:
                print(f"Sensor error: {err}")
                lcd_write("Sensor Error", 4)
                time.sleep(2)

            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nProgram stopped")
        display.lcd_clear()
        display.lcd_display_string("System Stopped", 1)
        time.sleep(1)
        display.lcd_clear()
        lgpio.gpiochip_close(chip)

if __name__ == "__main__":
    main()
