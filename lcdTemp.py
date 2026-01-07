import time
import random
import board
import adafruit_dht
import drivers

# ------------------ INITIALIZATION ------------------

# DHT22 on GPIO4
dht_device = adafruit_dht.DHT22(board.D4)

# LCD (16x4)
display = drivers.Lcd()

# LCD degree symbol (HD44780)
DEGREE = chr(223)

# ------------------ FUNCTIONS ------------------

def get_weight():
    """Simulated baby weight (kg)"""
    return round(random.uniform(5, 20), 1)

def lcd_write(text, line):
    """Always write exactly 16 chars from column 1"""
    display.lcd_display_string(text.ljust(16)[:16], line)

# ------------------ MAIN LOOP ------------------

try:
    while True:
        try:
            temp = dht_device.temperature
            hum = dht_device.humidity
            weight = get_weight()

            display.lcd_clear()

            lcd_write("Smart BabyCradle", 1)
            lcd_write(f"Temp:{temp:.1f}{DEGREE}C", 2)
            lcd_write(f"Hum :{hum:.0f}%", 3)
            lcd_write(f"Poids:{weight} Kg", 4)

        except RuntimeError as err:
            print("Sensor error:", err.args[0])

        time.sleep(3)

except KeyboardInterrupt:
    display.lcd_clear()
    print("Program stopped cleanly")
