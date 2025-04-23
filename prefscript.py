# Import the modules and packages to run the code

import RPi.GPIO as GPIO
import pygame
import time
import os
import random
import threading
import csv
from datetime import datetime
from collections import defaultdict

# Define the perch GPIO pins from Pi to have perch 1 and perch 2 
# Here connected to GPIO 4 and GPIO 5 respectively
# The sound files are stored in the "audio" folder
# The perch folders are defined for each condition; perch 1 sound files are in "perch_1" and perch 2 sound files are in "perch_2" folders
# The sound files are in .wav format
PERCH_PINS = {1: 4, 2: 5}
SOUND_FOLDER = "audio/"
PERCH_FOLDERS = {1: os.path.join(SOUND_FOLDER, "perch_1"),
                 2: os.path.join(SOUND_FOLDER, "perch_2")}

# Initialize pygame mixer to play sound files
pygame.mixer.init()
pygame.mixer.set_num_channels(2)

# Initialize GPIO for Raspberry Pi in BCM mode
# Set up GPIO pins for input with pull-up 
GPIO.setmode(GPIO.BCM)
for pin in PERCH_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define Global variables for recording data
# The recordings list will store the data for each trial
# The lock is used to ensure thread safety when accessing the recordings list
# The playing variable indicates if a sound is currently being played
# The played_sounds dictionary keeps track of which sounds have been played for each perch
# The perch_visits dictionary counts the number of visits to each perch
# The total_time_on_perch dictionary tracks the total time spent on each perch
# The inter_perch_intervals list stores the time intervals between perch visits
# The last_perch_time dictionary keeps track of the last time a perch was visited
# The experimental_condition variable indicates the current condition (A or B) for perch bias
recordings = []
lock = threading.Lock()
playing = False
played_sounds = defaultdict(list)
perch_visits = defaultdict(int)
total_time_on_perch = defaultdict(float)
inter_perch_intervals = []
last_perch_time = defaultdict(float)
experimental_condition = None

# Function to load sound files from the specified folders
def load_sound_files(folder):
    return [f for f in os.listdir(folder) if f.endswith('.wav')]

# Function to get the current folder based on the experimental condition
# If condition A, use perch 1 folder for perch 1 and perch 2 folder for perch 2
# If condition B, use perch 2 folder for perch 1 and perch 1 folder for perch 2
# If condition is not set, raise an error
def get_current_folder(perch_number):
    if experimental_condition == 'A':
        return PERCH_FOLDERS[perch_number]
    elif experimental_condition == 'B':
        return PERCH_FOLDERS[3 - perch_number]
    else:
        raise ValueError("Experimental condition not set")

# Function to play a random sound from the current folder for the specified perch
# The function checks if the sound has already been played
# If all sounds have been played, it resets the list and plays a new sound
# The function also sets the volume for each perch based on the condition
# The sound is played on a free channel
def play_random_sound(perch_number):
    sound_folder = get_current_folder(perch_number)
    available_sounds = [f for f in load_sound_files(sound_folder) if f not in played_sounds[perch_number]]
    
    if not available_sounds:  # If all sounds have been played, reset the list
        played_sounds[perch_number].clear()
        available_sounds = load_sound_files(sound_folder)

    sound_file = random.choice(available_sounds)
    sound = pygame.mixer.Sound(os.path.join(sound_folder, sound_file))
    
    channel = pygame.mixer.find_channel()
    if channel:
        channel.set_volume(1.0 if perch_number == 1 else 0.0, 0.0 if perch_number == 1 else 1.0)
        channel.play(sound)
    
    played_sounds[perch_number].append(sound_file)
    return sound_file, sound.get_length()

# Function to test the perches
# The function checks if the beam is broken (bird on perch) and plays a sound
# If the bird stays on the perch for 2 seconds, it plays a sound
# The function also tracks the time spent on the perch and whether the trial was interrupted
# The function uses threading to monitor both perches simultaneously
# The function also tracks the time intervals between perch visits
# The function uses a lock to ensure thread safety when accessing the recordings list
def test_perch(perch_number):
    global playing, last_perch_time
    pin = PERCH_PINS[perch_number]
    
    if GPIO.input(pin) == GPIO.LOW and not playing:
        # Add check for 2-second perch time before playing
        perch_start = time.time()
        while GPIO.input(pin) == GPIO.LOW:
            if time.time() - perch_start >= 2:  # Bird stayed for 2 seconds
                break
            time.sleep(0.1)
        
        # If bird left before 2 seconds, return without playing
        if GPIO.input(pin) == GPIO.HIGH:
            return
        played_sound, duration = play_random_sound(perch_number)
        print(f"Beam broken on perch {perch_number}! Playing: {played_sound}")
        
        playing = True
        start_time = time.time()

        if last_perch_time[perch_number] != 0:
            interval = start_time - last_perch_time[perch_number]
            inter_perch_intervals.append(interval)
        last_perch_time[perch_number] = start_time

        # Track if bird leaves during sound playback
        interrupted_trial = False
        while pygame.mixer.get_busy():
            if GPIO.input(pin) == GPIO.HIGH:  # Bird left the perch
                interrupted_trial = True
                break
            time.sleep(0.1)
        
        end_time = time.time()
        duration_spent = end_time - start_time
        
        # Only increment visit count for complete (non-interrupted) trials
        if not interrupted_trial:
            perch_visits[perch_number] += 1
            
        total_time_on_perch[perch_number] += duration_spent

        with lock:
            recordings.append({
                'timestamp': datetime.now().isoformat(),
                'perch_number': perch_number,
                'interrupted_trial': interrupted_trial,
                'sound_file': played_sound,
                'duration_spent': duration_spent,
                'visit_count': perch_visits[perch_number],  # This will now only count completed trials without interrupted trials 
                'total_time_on_perch': total_time_on_perch[perch_number],
                'experimental_condition': experimental_condition
            })

        print(f"Beam restored on perch {perch_number}")
        print("Waiting for 5 seconds before the next trial...")
        time.sleep(5) # Wait for 5 seconds before the next trial
        
        playing = False
# Monitor both perches in a loop
# The function creates a thread for each perch and starts them
# The threads are joined to ensure they complete before the next iteration
# The function runs indefinitely until interrupted by the user
def monitor_perches():
    while True:
        threads = [threading.Thread(target=test_perch, args=(perch,)) for perch in PERCH_PINS]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

# write the data to a CSV file
# The function creates a CSV file with the current date and time
# The filename is based on the bird ID and the current date
def record_data_to_csv(filename):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'perch_number', 'interrupted_trial', 'sound_file', 
                     'duration_spent', 'visit_count', 'total_time_on_perch', 
                     'experimental_condition']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(recordings)

# The function is called when the script is run at the beginning in command line
# The function prompts the user for the bird ID and experimental condition
# The function also handles keyboard interrupts to save the data to a CSV file
# The function cleans up the GPIO pins and exits
# The function also prints the experimental condition and the sound files being played
if __name__ == "__main__":
    bird_id = input("Enter the bird ID: ")
    
    while True:
        experimental_condition = input("Enter experimental condition (A or B): ").upper()
        if experimental_condition in ['A', 'B']:
            break
        print("Invalid input. Please enter either 'A' or 'B'")
    
    print(f"Bird {bird_id} assigned to experimental condition {experimental_condition}")
    print("Condition A: Perch 1 plays Perch 1 sounds, Perch 2 plays Perch 2 sounds")
    print("Condition B: Perch 1 plays Perch 2 sounds, Perch 2 plays Perch 1 sounds")
    
    try:
        monitor_perches()
    except KeyboardInterrupt:
        print("Test interrupted by user")
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f'bird_{bird_id}_{current_date}_condition{experimental_condition}.csv'
        record_data_to_csv(filename)
        print(f"Data exported to '{filename}'")
    finally:
        GPIO.cleanup()
        print("Test completed. GPIO cleaned up.")
