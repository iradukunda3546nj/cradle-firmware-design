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


               real embedded-to-server integration || integrating/ sending sensor's data to the cloud platform for Data collection purposes
=================================================================================================================================












