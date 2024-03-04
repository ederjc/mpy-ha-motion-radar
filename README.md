# Summary
This project uses the example of a radar motion sensor to show how to easily integrate custom sensors to a Home Assistant-based smarthome setup.
This repository is part of a Hackster.io post, which can be found [here](https://www.hackster.io/Infineon_Team/upgrade-your-smarthome-with-radar-and-home-assistant-feb4cf).

# Getting Started

## Requirements
* Microcontroller with MicroPython enablement (I use [this](https://www.infineon.com/cms/en/product/evaluation-boards/cy8cproto-062-4343w/) one).
* Custom sensor like the Infineon XENSIV™ [Radar Shield2Go](https://www.infineon.com/cms/de/product/evaluation-boards/s2go-radar-bgt60ltr11/).
* MicroPython IDE like [Thonny IDE](https://thonny.org/).
* [umqtt.simple](https://github.com/micropython/micropython-lib/tree/master/umqtt.simple) MicroPython library on your board -> check the Hackster.io article for instructions.

## secrets.py
Before this application code can be executed on your board you need to create a file `secrets.py` according to the format given in `secrets_example.py` and fill in your credentials:
```
ssid = 'your wifi ssid'
password = 'your wifi password'
mqtt_server = 'your mqtt broker ip address'
mqtt_user = 'your mqtt broker user name'
mqtt_password = 'your mqtt broker password'
```
Make sure to never commit the file with your credentials to any public repository.
Upload the file `secrets.py` onto your MicroPython board and continue with the next step.

## Running the Application Code
Now you can run the code `main.py` on your MicroPython device. If you are satisfied with it's behaviour you can upload `main.py` to your device to make it run automatically after powering up.
