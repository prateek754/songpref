

# Raspberry Pi-based operant playback setup and configuration guide

This guide provides step-by-step instructions for setting up a Raspberry Pi-based operant auditory playback experiment. The system uses infrared break beam sensors to detect bird perch landings and automatically triggers audio playback. The DIY modular setup enables researchers to conduct song preference experiments with automated data collection and offers flexible experimental design choices depending on research questions e.g. simple stimulus-response testing to complex multi-choice preference paradigms with stimulus counterbalancing options.


## Table of contents
- [Initial setup](#initial-setup)
- [SSH connection](#ssh-connection)
- [System configuration](#system-configuration)
- [Boot configuration](#boot-configuration)
- [Audio setup and testing](#audio-setup-and-testing)
- [Python testing](#python-testing)
- [Python code setup](#python-code-setup)
- [GPIO break beam sensors](#gpio-break-beam-sensors)
- [Running experiments](#running-experiments)

## Initial setup

### Prerequisites
- Raspberry Pi Zero 2 W (or newer)
- MicroSD card (16GB minimum)
- Power supply
- Network connection (Ethernet or WiFi)
- IR break beam sensors
- Full-range speakers 
- Amplifier
- HiFiBerry DAC+ Zero

### OS installation
1. Flash Raspberry Pi OS to SD card using Raspberry Pi Imager
2. Enable SSH before first boot during OS customization 
3. Configure WiFi if needed

## SSH connection

### Using PuTTY on Windows

1. **Download and install PuTTY**
    - Download from [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) and install it

2. **Basic connection setup**
    - Launch PuTTY
    - Enter Pi's IP address in "Host Name" field (same "Host Name" given during OS customization)
    - Port: 22 (default SSH port)
    - Connection type: SSH
    - Save session for future use

3. **Connection**
    - Click "Open" to connect
    - Login as: `user`
    - Password: `password` (same login information used during OS customization)

### Using WinSCP

1. **Download and install WinSCP**
    - Download from [here](https://winscp.net/eng/download.php) and install it

2. **Basic connection setup**
    - Launch WinSCP
    - File protocol: SFTP
    - Host name: Pi's IP address (the IP address of your Raspberry Pi)
    - Port: 22
    - User name: Raspberry Pi username: `user` (set during OS customization)
    - Password: Raspberry Pi password: `password` (set during OS customization)

3. **Connection**
    - Click "Login" to connect
    - You can now transfer files between your computer and the Raspberry Pi

## System configuration

### Basic configuration
```bash
# Open configuration tool
sudo raspi-config

# Key settings:
# - Change password if needed 
# - Enable interfaces (SSH, I2C, SPI, GPIO)
# - Set timezone
```

### Update system
```bash
sudo apt update
```

## Boot configuration

Boot configuration settings for Raspberry Pi can be found in the `/boot/firmware/config.txt` file. Boot configuration is essential for setting up GPIOs and audio output.

### Editing boot/firmware/config.txt
```bash
sudo nano /boot/firmware/config.txt
```

### Add this line dtoverlay=hifiberry-dac to the config.txt 

```ini
# Enable audio (loads snd_bcm2835)
#dtparam=audio=on
dtoverlay=hifiberry-dac
# Additional overlays and parameters are documented
# /boot/firmware/overlays/README

```
The `config file` is available in this repository for reference.

### Apply changes
```bash
sudo reboot
```

## Audio setup and testing

### Test audio output

```bash
# List audio devices
aplay -l
```
It should list HiFiBerry DAC+ Zero as the audio device. If not, check the connections and configuration. For any other DACs, the process is similar.

```bash
# Test speaker output
speaker-test -c2 -t wav

# Test left speaker 
aplay /usr/share/sounds/alsa/Front_Left.wav

# Test right speaker
aplay /usr/share/sounds/alsa/Front_Right.wav

# Adjust volume
alsamixer
```

## Python testing

## Python code setup

### Check Python installation
```bash
# Verify Python version
python3 --version

# Verify pip installation
pip3 --version
```

### Install required packages
```bash
# Install necessary Python packages
sudo apt install python3-numpy python3-pygame python3-pymixer
```


### RPi.GPIO installation and verification

#### Check if RPi.GPIO is installed
```bash
pip3 list | grep RPi.GPIO
```

If the command above doesn't show RPi.GPIO in the output, you need to install it.

#### Installation
```bash
sudo apt-get install python3-rpi.gpio
```
## GPIO break beam sensors

### Wiring diagram
```
Break Beam Sensor -> Raspberry Pi
VCC              -> 5V (Pin 1)
GND              -> GND (Pin 6)
OUT              -> GPIO Pin (e.g., GPIO 4 (Pin 7) and GPIO 5 (Pin 29))

```
See Supporting Materials of the research paper for more details and reference pinout diagrams from [pinout.xyz](https://pinout.xyz).

### Code for testing break beam detection

First, make sure the sensors work!

```bash
# Quick test command
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup([4,5], GPIO.IN); print(f'GPIO4: {GPIO.input(4)} GPIO5: {GPIO.input(5)}')"
```
The output should be 1/0 for each GPIO/Perch (i.e., GPIO4: 1 GPIO5: 1). Blocking the IR sensor should flip the values of GPIO4 and GPIO5 from 1 to 0. Make sure to test both sensors. If the output is not as expected, check the wiring and connections. Clean the sensor lenses if necessary. If still not working, reset the Raspberry Pi by disconnecting and reconnecting the power. Test again.

## Running experiments

### Running a demo Python script for testing

The test file contains a simple script to test the break beam sensors and audio playback. You can run it using the following command:

```bash
python3 test_script.py
```
This script will continuously check the state of the break beam sensors and play a sound when a beam is broken. Make sure to have sound files in a directory named `audio` in the same directory as the script. 

Check lines 13-16 of `test_script.py` for the specific sound file being played and modify accordingly.

### Running the preference trial script

```bash
python3 experimental_script.py
```

The program should run now and will ask for bird ID and experimental condition (A or B). The experimental condition will switch the playback condition, e.g.:
- A: Perch 1 Stimulus 1 and Perch 2 Stimulus 2
- B: Perch 1 Stimulus 2 and Perch 2 Stimulus 1

To stop the program, press `Ctrl + C` in the terminal.

The data will be saved in the same folder as the script with the name format specified in the script.

### Important line numbers

- **Line 108**: "How long does the bird have to sit on the perch to trigger a trial/audio stimulus?"
- **Line 157**: Inter-trial interval "How long to wait before the next trial?"






