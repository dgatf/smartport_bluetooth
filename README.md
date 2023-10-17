# Smartport bluetooth client

This is a Frsky Smartport client for devices with bluetooth written in Python 3

- Supported OS: Android, Linux, OS X and Windows
- Support for bluetooth 2. Bluetooth 4 (BLE) supported only in Linux
- Support for ACCST X series. ACCST D series and ACCESS protocols not supported


## Installation

## Linux, OS X and Windows

Prerequisites:

- Python 3
- OpentTx 2.3.6

Install python modules (1)

Linux:

<code>python3 -m pip install kivy pybluez plyer gattlib</code>

To scan for BLE devices sudo privilieges are needed. To run as normal user change python capabilities:

<code>sudo setcap cap_net_raw+ep /usr/bin/$(readlink /usr/bin/python3)</code>

OS X and old windows:

<code>python -m pip install kivy pybluez plyer</code>

Windows 10:

<code>python -m pip install kivy PyBluez-win10 plyer</code>  
\
**Launch** the app from *src* folder:

<code>python3 main.py</code>  
\
(1) If *pybluez* does not install correctly:

<code>sudo apt-get install libbluetooth-dev  
pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez  
python3 -m pip install kivy plyer gattlib</code>  


## Android

Install [smartportbt_unsigned.apk](https://github.com/dgatf/smartport_bluetooth/releases/download/v1.0/smartportbt_unsigned.apk) 

Pair the bluetooth device before launching the app

## Usage

In Opentx go to *Radio settings -> Hardware -> SP power -> ON*

Attach bluetooth device to radio smartport


<p align="center"><img src="./images/models.png" width="300"><br>

<p align="center"><img src="./images/sensors.png" width="300"><br>

<p align="center"><img src="./images/sensor.png" width="300"><br>