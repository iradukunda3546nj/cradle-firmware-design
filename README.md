<<<<<<< HEAD
Git clone

=================

> git clone https://github.com/the-raspberry-pi-guy/lcd

>ls

>cd lcd

>sudo sh install.sh

>Reboot

>Run the demo file as follows:



>python demo_lcd.py  (when you get a Remote I/O error : the problem is on the wrong I2C address of your peripheral connected to the I2C of Raspebrry pi.  



>open lcddriver.py

> nano demo_lcd.py   (check if the I2C address of your lcd matches with the one in the code  : 

 (Here is how to detect the I2C address of your I2C device  : first run

> sudo apt update

> sudo apt install i2c-tools

> Then run : > sudo i2cdetect -y 1    (Note: Please ensure that the I2C is enabled in raspberry pi configurations > raspi-config



If you found that the address of your lcd do not match with the one in the code edit it right and save and exit using the following command

>Ctrl + O → Enter → Ctrl + X



;After running all above I get the realization of this :



Creating VEnv so that you're able to install the libraries using pip:



# Create virtual environment

> python3 -m venv cradlex_env



# Activate the virtual environment

> source cradlex_env/bin/activate





Using Secure copy command

========================================

>scp "D:/cradle-firmware-design/lcdTemp.py" cradle@192.168.1.81:~/       

From Pi to local PC
use e.g > scp cradle@192.168.1.81:~/test.wav "D:/cradle-firmware-design/"                    





                  Re-working on The project

==========================================================================

Recall: to test LCD (we need to go to the lcd folder and run demo_lcd.py)  using the following commands



>cd lcd

>python3 demo_lcd.py





                             Looking for connecting DHT temperature sensor to Rpi

============================================================================================



I have found many works done on connecting DHT sensor to the raspberrypi.However, many of them do not work, when you try to run them you face a runtime error, and this issue might be arising from the lgpio missing library, the one which allows you to interact with the hardware GPIO pins.



Hopefully, Here's a detailed guide to help you connect the digital temperature sensor to the raspberryPi (Go step by step throughout this entire guide).



> https://pimylifeup.com/raspberry-pi-humidity-sensor-dht22/





Now, Let's proceed with installing and connecting RaspberryPi to the edge impulse platform for sending data for model training

===============================================================================

Meanwhile, you can connect the MIC (for me ,I used USB microphone) , CSI camera. (for other sensors you can refer to the way I connected MPU6050 to edge impulse using raspberrypi i.e the way I wrote Python SDK containing API keys of the project).

In fact, connecting raspberrypi to the edge impulse platform requires installing dependencies and the there is an official edge impulse link which streamline process of connecting raspberrypi to the edge impulse 

Follow this:
          >https://docs.edgeimpulse.com/hardware/boards/raspberry-pi-5 

>Then, after you install all dependencies step by step you will run edge_impulse-linux and you will be connected to edge immediately asking you to put the edge impulse account credentials and once you enter them correctly your pi will be connected to edge ,head to that project and then go to devices, then you can start acquiring data from Pi.

                                   Integration of Sensor's data with I2C Lcd Display
===========================================================================================================
The goal was to run all components inside a virtual environment and display real‑time sensor data on the LCD.

During integration, several errors occurred due to legacy libraries, Pi 5 hardware changes, and virtual environment isolation.

This document records each error, its cause, and the exact fix.

Error 1: ModuleNotFoundError: No module named 'smbus'
Error Message

ModuleNotFoundError: No module named 'smbus'

Where it occurred

from smbus import SMBus

Inside:

drivers/i2c_dev.py
Root Cause

The LCD driver uses I2C communication

I2C requires SMBus bindings

smbus is not available inside Python virtual environments by default

Raspberry Pi OS installs smbus at system level, not venv level

Fix Applied (Step‑by‑Step)

Installed system I2C support:

sudo apt update
sudo apt install -y python3-smbus i2c-tools

Installed venv‑compatible SMBus library:

source cradlex_env/bin/activate
pip install smbus2

Updated LCD driver import:

❌ Old:

from smbus import SMBus

✅ New:

from smbus2 import SMBus
Result

✔ SMBus error resolved ✔ I2C communication functional inside virtual environment

Error 2: ModuleNotFoundError: No module named 'RPi'
Error Message
ModuleNotFoundError: No module named 'RPi'
Where it occurred
from RPi.GPIO import RPI_REVISION

Inside:

drivers/i2c_dev.py
Root Cause

Raspberry Pi 5 does not support RPi.GPIO properly

RPi.GPIO is deprecated on Pi 5

Pi 5 officially uses lgpio / libgpiod

The LCD driver was written for older Pi models (3/4)

Virtual environments do not inherit system GPIO libraries

Important Insight

The LCD driver does not actually need GPIO — it only checks RPI_REVISION to guess the I2C bus.

On modern Raspberry Pi models:

I2C bus is always bus 1

Fix Applied (Safe & Engineered)

Modified the driver to gracefully bypass RPi.GPIO:

❌ Old code:

from RPi.GPIO import RPI_REVISION

✅ New code:

try:
    from RPi.GPIO import RPI_REVISION
except ImportError:
    RPI_REVISION = 3  # Safe default for modern Raspberry Pi
Why this works

Avoids installing deprecated RPi.GPIO

Fully compatible with Raspberry Pi 5

Keeps driver future‑proof

Does not interfere with lgpio

Result

✔ GPIO error resolved ✔ LCD driver loads correctly ✔ No conflicts with lgpio

Error 3: Degree Symbol Displaying Incorrectly (-C instead of °C)
Symptom

LCD showed:

25.3-C

Instead of:

25.3°C
Root Cause

HD44780 LCDs do not support Unicode

Unicode degree symbol ° is not part of LCD character ROM

Fix Applied

Used the HD44780‑native degree symbol code:

DEGREE = chr(223)

And updated formatting:

f"{temperature:.1f}{DEGREE}C"
Result

✔ Correct °C symbol displayed


                                         📦 Weighing System Module (Raspberry Pi 5 + HX711 + I2C LCD)
==================================================================================================================================================

1️⃣ Objective

This module adds a reliable digital weighing function to the Raspberry Pi 5 using:

20kg Load Cell

HX711 24-bit ADC amplifier

I2C LCD display

Kalman filtering for stable readings

The goal is to:

Accurately measure weight in kilograms

Provide stable filtered readings

Support calibration using a known weight

Run fully inside a Python virtual environment (cradlex_env)

Be compatible with Raspberry Pi 5 (using lgpio, not RPi.GPIO)

The system is designed for workshop/small-business grade reliability, not hobby-level testing.

2️⃣ Hardware Wiring
HX711 → Raspberry Pi 5 (BCM Numbering)
HX711 Pin	Raspberry Pi 5
DT (DOUT)	GPIO 5
SCK	GPIO 6
VCC	5V
GND	GND

Important Notes:

BCM numbering is used.

Ensure common ground.

Load cell must be mechanically fixed.

Allow 5–10 minutes warm-up before calibration.

3️⃣ Virtual Environment Setup

Activate environment:

source cradlex_env/bin/activate


Install required libraries:

pip install lgpio numpy pyyaml smbus2 RPLCD


System-level dependency:

sudo apt install python3-smbus i2c-tools

4️⃣ Calibration Procedure (calibrate.py)
Purpose

Calibration determines:

zero_offset

calibration_factor

These values convert raw HX711 counts into kilograms.

How It Works

User removes all weight → system measures raw zero value.

User places a known weight → system measures span.

Calibration factor is computed:

calibration_factor = (span_raw - zero_raw) / known_weight


Values are saved into:

config.yaml

How To Run
python3 calibrate.py

Steps:

Remove all weight → press Enter

Enter known weight in kg (e.g., 5)

Place weight → wait stable → press Enter

After completion:

config.yaml


will contain:

zero_offset: XXXXX
calibration_factor: XXXXX

Verification After Calibration

Run:

python3 weighing_system.py


Check:

No load → ~0.000 kg

Known weight → correct value

Remove weight → returns to zero

If slight error exists, fine-tune:

new_factor = old_factor × (measured / real_weight)

5️⃣ Main Weighing Program (weighing_system.py)
Objective

This program:

Reads raw HX711 data

Converts to kg using stored calibration

Applies Kalman filtering

Displays weight on I2C LCD

Runs continuously

Weight Calculation
weight = (raw - zero_offset) / calibration_factor

Filtering

A Kalman filter is applied to:

Reduce noise

Improve stability

Provide smooth readings

Maintain responsiveness

Display

The system shows:

X.XXX kg


Updated continuously.

6️⃣ Important Issue Encountered (SMBus Error)
Problem

While running weighing_system.py, the following error occurred:

NameError: name 'SMBus' is not defined

Root Cause

Inside:

cradlex_env/lib/python3.13/site-packages/RPLCD/i2c.py


The library internally attempted:

self.bus = SMBus(self._port)


However, the module was imported as:

import smbus2 as smbus


This means:

SMBus was not directly defined

Only smbus.SMBus existed

Hence → NameError.

Solution Applied

Opened the file:

nano cradlex_env/lib/python3.13/site-packages/RPLCD/i2c.py


Searched for:

SMBus(


Replaced:

self.bus = SMBus(self._port)


With:

self.bus = smbus.SMBus(self._port)


Saved file.

Result

✔ SMBus error resolved
✔ I2C LCD working inside virtual environment
✔ No need for RPi.GPIO
✔ Compatible with Raspberry Pi 5

7️⃣ Raspberry Pi 5 Compatibility Notes

RPi.GPIO was avoided due to compatibility issues.

lgpio is used instead.

I2C bus on Raspberry Pi 5 is always bus 1.

Virtual environments require smbus2.

8️⃣ Final System Overview

The weighing module now provides:

✔ Pi 5 compatible GPIO control (lgpio)
✔ HX711 24-bit ADC reading
✔ Proper calibration storage
✔ Kalman-filtered stable readings
✔ I2C LCD output
✔ Fully virtual-environment compatible

9️⃣ Future Improvements (Optional)

Add tare button

Add multi-point calibration

Add temperature compensation

Add data logging

Add automatic startup (systemd service)

🔚 Conclusion

The weighing function is now:

Stable

Accurate

Pi 5 compatible

Professionally structured

Fully reproducible from documentation

This documentation ensures future maintenance and upgrades can be performed confidently.



               real embedded-to-server integration || integrating/ sending sensor's data to the cloud platform for Data collection purposes
=================================================================================================================================











=======
>>>>>>> 16ca65192366029ca63078be4c56230614e71125

