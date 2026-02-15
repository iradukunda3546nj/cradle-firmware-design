#!/usr/bin/env python3
import time
import yaml
import lgpio
import numpy as np
from RPLCD.i2c import CharLCD

DT = 5
SCK = 6
CONFIG_FILE = "config.yaml"

# -------- Load calibration --------
with open(CONFIG_FILE) as f:
    cfg = yaml.safe_load(f)

zero_offset = cfg["zero_offset"]
cal_factor = cfg["calibration_factor"]

# -------- GPIO Setup --------
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(chip, DT)
lgpio.gpio_claim_output(chip, SCK)

# -------- LCD Setup --------
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()

# -------- HX711 Read --------
def read_raw():
    while lgpio.gpio_read(chip, DT) == 1:
        time.sleep(0.0005)

    count = 0
    for _ in range(24):
        lgpio.gpio_write(chip, SCK, 1)
        count = count << 1
        lgpio.gpio_write(chip, SCK, 0)
        if lgpio.gpio_read(chip, DT):
            count += 1

    lgpio.gpio_write(chip, SCK, 1)
    lgpio.gpio_write(chip, SCK, 0)

    if count & 0x800000:
        count -= 0x1000000

    return count

# -------- Kalman Filter --------
class KalmanFilter:
    def __init__(self):
        self.q = 0.01     # process noise
        self.r = 0.5      # measurement noise
        self.x = 0        # state
        self.p = 1        # covariance

    def update(self, measurement):
        # prediction
        self.p += self.q

        # update
        k = self.p / (self.p + self.r)
        self.x += k * (measurement - self.x)
        self.p *= (1 - k)

        return self.x

kf = KalmanFilter()

print("Weighing system started...")

try:
    while True:
        raw = read_raw()
        weight = (raw - zero_offset) / cal_factor

        filtered_weight = kf.update(weight)

        lcd.clear()
        lcd.write_string(f"{filtered_weight:.3f} kg")

        time.sleep(0.1)

except KeyboardInterrupt:
    lcd.clear()
    lgpio.gpiochip_close(chip)
    print("Stopped")
