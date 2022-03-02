# Core Electronics Unified PiicoDev Library
Unified device libraries for the PiicoDev ecosystem of sensors and modules.
Built for MicroPython and Python.

## Installation
On Raspberry Pi, run the following to install:
```shell
sudo pip3 install piicodev
```


## Changes

	- v1.1.2 - No change - deployment test
	- v1.1.1 - Add support for QMC6310
	- v1.0.1 
		- BME280: Add initialisation error handling
		- SSD1306: Remove PIL dependency (RPi SBC) and improve pbm file handling
	- v1.0.0 - Initial release
 
 
## Developing
To install this package, along with the tools you need to develop and run tests, run the following (in your virtualenv:)
```shell
sudo pip3 install -e .[dev]
```
