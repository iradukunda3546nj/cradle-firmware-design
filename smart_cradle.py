import time
from urllib.parse import urlparse
import random
import board
import adafruit_dht
import drivers
import subprocess
import requests
import json
import os

# ------------------ CONFIG ------------------

PC_IP = "https://www.zolilabs.com"  # Can be domain or full URL

def normalize_base_url(base: str) -> str:
    parsed = urlparse(base)
    if parsed.scheme and parsed.netloc:
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        base = base.strip().rstrip('/')
        base_url = f"https://{base}"  # default to HTTPS
    return base_url.rstrip('/')

BASE_URL = normalize_base_url(PC_IP)
print(f"Using server base URL: {BASE_URL}")
AUDIO_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/upload_audio.php"
DATA_UPLOAD_URL = f"{BASE_URL}/smart_cradle/api/receive_data.php"

AUDIO_WAV = "/tmp/cry.wav"
AUDIO_MP3 = "/tmp/cry.mp3"
RECORD_SECONDS = 5  # Reduced for testing, change back to 30 when working

# ------------------ INITIALIZATION ------------------

dht_device = adafruit_dht.DHT22(board.D4)
display = drivers.Lcd()
DEGREE = chr(223)

# ------------------ FUNCTIONS ------------------

def get_weight():
    """Simulated baby weight (kg)"""
    return round(random.uniform(5, 20), 1)

def lcd_write(text, line):
    display.lcd_display_string(text.ljust(16)[:16], line)

def record_audio():
    """Record audio from USB microphone"""
    try:
        lcd_write("Recording...", 4)
        
        # Test if audio device exists first
        test_cmd = ["arecord", "-l"]
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        print("Audio devices detected:")
        print(result.stdout)
        
        # Alternative device specifications to try
        device_options = [
            "plughw:2,0",    # Direct hardware access
            "hw:2,0",        # Alternative hardware syntax
            "default",       # System default
        ]
        
        success = False
        for device in device_options:
            try:
                print(f"Trying device: {device}")
                cmd = [
                    "arecord",
                    "-D", device,
                    "-d", str(RECORD_SECONDS),
                    "-f", "cd",
                    "-v",  # Verbose output for debugging
                    AUDIO_WAV
                ]
                
                print(f"Running command: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=RECORD_SECONDS + 5
                )
                
                if result.returncode == 0:
                    print(f"Recording successful with device: {device}")
                    success = True
                    break
                else:
                    print(f"Failed with device {device}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"Recording timeout with device: {device}")
            except Exception as e:
                print(f"Error with device {device}: {str(e)}")
        
        if success:
            # Verify file was created
            if os.path.exists(AUDIO_WAV):
                file_size = os.path.getsize(AUDIO_WAV)
                print(f"Audio file created: {AUDIO_WAV}, Size: {file_size} bytes")
                return True
            else:
                print("Audio file was not created")
                return False
        else:
            print("All device options failed")
            return False
            
    except Exception as e:
        print(f"Error in record_audio: {str(e)}")
        return False

def convert_to_mp3():
    """Convert WAV to MP3"""
    try:
        if not os.path.exists(AUDIO_WAV):
            print(f"WAV file not found: {AUDIO_WAV}")
            return False
        
        print("Converting to MP3...")
        result = subprocess.run(
            ["lame", "--silent", AUDIO_WAV, AUDIO_MP3],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and os.path.exists(AUDIO_MP3):
            print(f"Converted to MP3: {AUDIO_MP3}")
            return True
        else:
            print(f"Conversion failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error in convert_to_mp3: {str(e)}")
        return False

def upload_audio():
    """Upload audio file to server"""
    try:
        if not os.path.exists(AUDIO_MP3):
            print(f"MP3 file not found: {AUDIO_MP3}")
            return None
            
        lcd_write("Uploading audio", 4)
        print(f"Uploading {AUDIO_MP3}...")
        
        with open(AUDIO_MP3, "rb") as f:
            r = requests.post(AUDIO_UPLOAD_URL, files={"audio": f}, timeout=30)
        
        print(f"Upload response: {r.status_code}")
        if r.status_code == 200:
            response = r.json()
            print(f"Upload successful: {response}")
            return response.get("audio_url")
        else:
            print(f"Upload failed: {r.text}")
            return None
            
    except Exception as e:
        print(f"Error in upload_audio: {str(e)}")
        return None

def send_data(temp, hum, weight, audio_url):
    """Send sensor data to server"""
    try:
        lcd_write("Sending data", 4)
        print("Sending sensor data...")
        
        payload = {
            "temperature": temp,
            "humidity": hum,
            "weight": weight,
            "audio_url": audio_url if audio_url else ""
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            DATA_UPLOAD_URL, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=10
        )
        
        print(f"Data sent: Status {response.status_code}")
        
    except Exception as e:
        print(f"Error in send_data: {str(e)}")

# ------------------ MAIN LOOP ------------------

def main():
    try:
        # Initial display test
        display.lcd_clear()
        lcd_write("Smart BabyCradle", 1)
        lcd_write("System Starting", 2)
        lcd_write("Audio: Card 2,0", 3)
        lcd_write("Waiting...", 4)
        time.sleep(2)
        
        while True:
            try:
                # Read sensor data
                temp = dht_device.temperature
                hum = dht_device.humidity
                weight = get_weight()
                
                # Display sensor data
                display.lcd_clear()
                lcd_write("Smart BabyCradle", 1)
                if temp is not None and hum is not None:
                    lcd_write(f"Temp:{temp:.1f}{DEGREE}C", 2)
                    lcd_write(f"Hum :{hum:.0f}%", 3)
                else:
                    lcd_write("Sensor Error", 2)
                    lcd_write("Check DHT22", 3)
                lcd_write(f"Poids:{weight} Kg", 4)
                
                print(f"Sensor Data - Temp: {temp}, Hum: {hum}, Weight: {weight}")
                time.sleep(3)
                
                # Record and process audio
                if record_audio():
                    if convert_to_mp3():
                        audio_url = upload_audio()
                        # Send data even if audio upload failed
                        send_data(temp, hum, weight, audio_url)
                    else:
                        print("Audio conversion failed, sending data without audio")
                        send_data(temp, hum, weight, None)
                else:
                    print("Recording failed, sending data without audio")
                    send_data(temp, hum, weight, None)
                
                # Cleanup
                for file in [AUDIO_WAV, AUDIO_MP3]:
                    if os.path.exists(file):
                        try:
                            os.remove(file)
                            print(f"Cleaned up: {file}")
                        except:
                            pass
                
                print("Cycle complete, waiting 10 seconds...")
                time.sleep(10)
                
            except RuntimeError as err:
                print(f"Sensor error: {err.args[0]}")
                lcd_write("Sensor Error", 4)
                time.sleep(2)
            except Exception as e:
                print(f"Unexpected error in main loop: {str(e)}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
        display.lcd_clear()
        display.lcd_display_string("System Stopped", 1)
        time.sleep(1)
        display.lcd_clear()

if __name__ == "__main__":
    main()