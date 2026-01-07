import RPi.GPIO as GPIO
from hx711 import HX711
import time


# Setup GPIO
GPIO.setmode(GPIO.BCM)


# Initialize HX711
hx = HX711(dout_pin=6, pd_sck_pin=5)
while True:
    reading= hx.get_raw_data_mean()
    print('Load Cell Reading: {}'.format(reading))
    time.sleep(2)
