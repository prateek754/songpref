import RPi.GPIO as GPIO
import pygame
import time
import os

# GPIO setup
PERCH_1_PIN = 4
PERCH_2_PIN = 5

# Initialize pygame mixer
pygame.mixer.init()

# Sound configuration
SOUND_FOLDER = "audio/"
test_sound_1 = "feebee.wav"
test_sound_2 = "chickadee.wav"

# Load test sounds
sound_1 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, test_sound_1))
sound_2 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, test_sound_2))

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PERCH_1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PERCH_2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def play_sound_in_channel(sound, left_vol, right_vol):
    """Play sound with specific volume in left and right channels"""
    pygame.mixer.set_num_channels(2)  # Ensure there are 2 audio channels
    channel = pygame.mixer.find_channel()  # Find a free channel
    if channel:
        channel.set_volume(left_vol, right_vol)  # Set left and right volumes
        channel.play(sound)  # Play the sound

def test_perch(pin, sound, perch_name, left_vol, right_vol):
    print(f"Testing {perch_name}...")
    print(f"Break the beam on {perch_name}")
    
    while True:
        if GPIO.input(pin) == GPIO.LOW:
            print(f"Beam broken on {perch_name}!")
            play_sound_in_channel(sound, left_vol, right_vol)
            time.sleep(1)  # Wait for 1 second
            while GPIO.input(pin) == GPIO.LOW:
                time.sleep(0.1)  # Wait for beam to be unbroken
            print(f"Beam restored on {perch_name}")
            break
        time.sleep(0.1)

try:
    while True:
        # Test Perch 1 with sound in the left channel only (left_vol=1.0, right_vol=0.0)
        test_perch(PERCH_1_PIN, sound_1, "Perch 1", left_vol=1.0, right_vol=0.0)
        
        # Test Perch 2 with sound in the right channel only (left_vol=0.0, right_vol=1.0)
        test_perch(PERCH_2_PIN, sound_2, "Perch 2", left_vol=0.0, right_vol=1.0)
        
        choice = input("Press Enter to test again, or type 'q' to quit: ")
        if choice.lower() == 'q':
            break

except KeyboardInterrupt:
    print("Test interrupted by user")

finally:
    GPIO.cleanup()
    print("Test completed. GPIO cleaned up.")
