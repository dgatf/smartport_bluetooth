# Smartport bluetooth client

This is a Frsky Smartport client for devices with bluetooth written in Python 3 and Kivy

- Support for bluetooth 2. Bluetooth 4 (BLE) not supported
- Support for ACCST X series. ACCST D series and ACCESS protocols not supported
- Supported OS: Android, Linux, OS X and Windows

## Installation

## Linux, OS X and Windows

Prerequisites:

- Python 3 with Kivy and pybluez modules
- OpentTx 2.3.6

Install python modules

*python3 -m pip install kivy pybluez*

Copy folder *src* and execute

*python3 main.py*

## Android

Install [apk](bin/smartportbt_unsigned.apk)

Pair the bluetooth device before launching the app


<p align="center"><img src="./images/models.png" width="300"><br>

<p align="center"><img src="./images/sensors.png" width="300"><br>

<p align="center"><img src="./images/sensor.png" width="300"><br>