from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='piicodev',
    version='0.0.4',
    description='Drivers for the PiicoDev ecosystem of sensors and modules',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CoreElectronics/PiicoDev",
    author="Michael Ruppe",
    author_email="production.inbox@coreelectronics.com.au",
    py_modules=[
        "PiicoDev_Unified",
        "PiicoDev_MPU6050",
        "PiicoDev_TMP117",
        "PiicoDev_VEML6030",
        "PiicoDev_VL53L1X",
        "PiicoDev_BME280",
    ],
    package_dir={'': 'src'},
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