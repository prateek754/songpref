## The readme file contains information about running the python code in Raspberry Pi

1. Check if python is already installed on Pi
	```bash
        python3 --version 
	```
	The output should be something like ```Python 3.11``` or any other version 
2. Install ```pip``` if not installed
  ```bash
    sudo apt install python3-pip
  ```
3. Install the required pakages ``` RPi.GPIO ``` and ```pygame```
	```bash
   pip3 install RPi.GPIO
  ```
  ```bash
   pip3 install pygame
  ```
4. Go to the folder where the python script is stored via ```cd``` command and enter
   ```bash
    python prefscript.py
  ```
  The program should run now and will ask for bird ID and Experimental condition (A or B)
5. To stop the program, press ```Ctrl + C``` in the terminal
6. The data will be saved in the same folder as the script with the name format specified in the script 
