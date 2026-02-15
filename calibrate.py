#!/usr/bin/env python3
import time
import yaml
import lgpio

CONFIG_FILE = "config.yaml"

DT = 5
SCK = 6

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(chip, DT)
lgpio.gpio_claim_output(chip, SCK)

def read_raw():
    while lgpio.gpio_read(chip, DT) == 1:
        time.sleep(0.001)

    count = 0
    for _ in range(24):
        lgpio.gpio_write(chip, SCK, 1)
        count = count << 1
        lgpio.gpio_write(chip, SCK, 0)
        if lgpio.gpio_read(chip, DT):
            count += 1

    # set gain 128
    lgpio.gpio_write(chip, SCK, 1)
    lgpio.gpio_write(chip, SCK, 0)

    if count & 0x800000:
        count -= 0x1000000

    return count

def average(n=50):
    vals = [read_raw() for _ in range(n)]
    return sum(vals) / len(vals)

print("Remove all weight. Press Enter.")
input()
zero = average()
print("Zero raw:", zero)

known_weight = float(input("Enter known weight in kg: "))
print("Place weight and press Enter.")
input()

span = average()
print("Span raw:", span)

cal_factor = (span - zero) / known_weight

print("Calibration factor:", cal_factor)

config = {
    "zero_offset": zero,
    "calibration_factor": cal_factor
}

with open(CONFIG_FILE, "w") as f:
    yaml.dump(config, f)

print("Saved to config.yaml")

lgpio.gpiochip_close(chip)
