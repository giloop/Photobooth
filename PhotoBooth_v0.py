#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import os
import subprocess
import signal
import sys

# Globals 
SWITCH = 10
READY_LED = 13
POSE_LED = 19
WAIT_LED = 26
    
def GPIO_setup():    
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SWITCH, GPIO.IN)
    GPIO.setup(POSE_LED, GPIO.OUT)
    GPIO.setup(READY_LED, GPIO.OUT)
    GPIO.setup(WAIT_LED, GPIO.OUT)
    GPIO.output(READY_LED, True)
    GPIO.output(WAIT_LED, False)

def mainLoop():
    while True:
        if (GPIO.input(SWITCH)):
            print("pose!")
            GPIO.output(READY_LED, False)
            GPIO.output(POSE_LED, True)
            #time.sleep(1.5)
            for i in range(3):
                GPIO.output(POSE_LED, False)
                time.sleep(0.1)
                GPIO.output(POSE_LED, True)
                time.sleep(0.1)

            GPIO.output(WAIT_LED, True)
            GPIO.output(POSE_LED, False)
            print("SNAP")
            # Create temp lock file in directory
            open("/home/pi/PhotoBooth/lock", "a").close()
            # Take picture and download it
            gpout = subprocess.check_output("gphoto2 --capture-image-and-download --filename /home/pi/PhotoBooth/photo%H%M%S.jpg", stderr=subprocess.STDOUT, shell=True)
            print(gpout)
            GPIO.output(WAIT_LED, True)
            # Delete lock file
            os.remove("/home/pi/PhotoBooth/lock")
            print("Photo downloaded ...")		
            print("ready for next round")
            # Setting LEDs bakc to ready mode
            time.sleep(0.5)
            GPIO.output(WAIT_LED, False)
            GPIO.output(READY_LED, True)


def exitLoop(signal, frame):
    print("Goodbye")
    GPIO.cleanup()
    sys.exit(0)

if __name__ == '__main__':
    # Clean "lock" file on startup
    if os.path.exists("/home/pi/PhotoBooth/lock"):
        os.remove("/home/pi/PhotoBooth/lock")

    print("Ctrl+C will quit with GPIO.cleanup()")
    GPIO.cleanup()
    GPIO_setup()
    signal.signal(signal.SIGINT, exitLoop)
    mainLoop()

    
