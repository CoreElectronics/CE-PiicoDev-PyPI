from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='piicodev',
    version='1.0.1',
    description='Drivers for the PiicoDev ecosystem of sensors and modules',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CoreElectronics/CE-PiicoDev-PyPI",
    author="Core Electronics",
    author_email="production.inbox@coreelectronics.com.au",
    packages=find_packages("src"), # include all packages under src
    package_dir={'': 'src'},       # tell distutils packages are under src
    include_package_data=True,     # include everything in source control
    package_data={'': ['*.dat']},  
    py_modules=[
        "PiicoDev_Unified",
        "PiicoDev_MPU6050",
        "PiicoDev_TMP117",
        "PiicoDev_VEML6030",
        "PiicoDev_VL53L1X",
        "PiicoDev_BME280",
        "PiicoDev_MS5637",
        "PiicoDev_VEML6040",
        "PiicoDev_CAP1203",
        "PiicoDev_SSD1306",
        "PiicoDev_RGB",
        "PiicoDev_Buzzer",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: MicroPython",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires = [
        "smbus2>=0.4.1"
    ],
    extras_require = {
        "dev": [
            "pytest>=3.7",
        ],
    },
)
