# Core Electronics Unified PiicoDev Library
Unified device libraries for the PiicoDev ecosystem of sensors and modules.
Built for MicroPython and Python.

## Installation
On Raspberry Pi, run the following to install:
```shell
sudo pip3 install piicodev
```


## Changes

	- v1.6.1 - Add support for Air-Quality Sensor ENS160
	- v1.6.0 - Bad release, use v1.6.1
	- v1.5.4 - Fix device ID address for PiicoDev potentiometers
	- v1.5.3 - Force warning for unconfigured i2c on Raspberry Pi SBC for Potentiometer
	- v1.5.2 - Add warning for unconfigured i2c on Raspberry Pi SBC
	- v1.5.1 - Change device ID for Slide Potentiometer
	- v1.5.0 - Add support for PiicoDev Potentiometers
	- v1.4.0 - Add support for 3-Axis Accelerometer LIS3DH
	- v1.3.1
		- VL53L1X: Rename change_id() to change_addr()
		- SSD1306: Add ASW argument to initialisation function
	- v1.3.0
		- Add support for PiicoDev Real Time Clock RV-3028
		- Bugfix QMC6310: logging function
		- Bugfix RGB module: ensure brightness is an integer
	- v1.2.2 - QMC6310: Change default sign to match silk screen
	- v1.2.1 - Add support for PiicoDev RFID Module
	- v1.2.0 - Bad release, use v1.2.1
	- v1.1.3 - Add support for QMC6310
	- v1.1.2 - No change - deployment test
	- v1.1.1 - SSD1306: Add support for circles & arcs
	- v1.0.1 
		- BME280: Add initialisation error handling
		- SSD1306: Remove PIL dependency (RPi SBC) and improve pbm file handling
	- v1.0.0 - Initial release
 
 
## Developing
To install this package, along with the tools you need to develop and run tests, run the following (in your virtualenv:)
```shell
sudo pip3 install -e .[dev]
```
