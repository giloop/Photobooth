#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Photobooth, version utilisant la librairie pigpio
qui gère des pwm pour allumer un ruban de led en 12V
"""

import pigpio
import time
import os
import subprocess
import signal
import sys
import SlideShowNoSound_v1 as sl
import testDiskUsage as du
from threading import Thread
    
# Globals
SWITCH = 22
SHUTDOWN = 17
HIGH3V = 27 # pin used as +3.3V
RED = 19
BLUE = 13
GREEN = 26
pi = pigpio.pi()
imgDir = "/home/pi/public_html/PhotoBooth/images/PhotosBooth"

def GPIO_setup():
    """
    Initialisation des pins utilisées pour le GPIO
    """
    # GPIO setup
    pi.set_mode(SWITCH, pigpio.INPUT)
    pi.set_mode(GREEN,  pigpio.OUTPUT)
    pi.set_mode(RED,    pigpio.OUTPUT)
    pi.set_mode(BLUE,   pigpio.OUTPUT)
    pi.set_mode(HIGH3V, pigpio.OUTPUT)
    
    # Switch off LEDs
    pi.set_PWM_dutycycle(GREEN, 0) # PWM off
    pi.set_PWM_dutycycle(RED,   0) # PWM off
    pi.set_PWM_dutycycle(BLUE,  0) # PWM off
    pi.write(HIGH3V, 1)
    time.sleep(0.1)

def prendrePhoto():
    # Prise d'une photo
    # Clignote orange : temps de mise en place
    for i in range(3):
        pi.set_PWM_dutycycle(GREEN, 80-20*i)
        pi.set_PWM_dutycycle(RED,   255)
        pi.set_PWM_dutycycle(BLUE,  0)
        time.sleep(0.5)
        pi.set_PWM_dutycycle(GREEN, 0) # PWM off
        pi.set_PWM_dutycycle(RED,   0) # PWM off
        pi.set_PWM_dutycycle(BLUE,  0) # PWM offt
        time.sleep(0.5)

    # Rouge fixe : temps de pause
    pi.set_PWM_dutycycle(GREEN, 0) # PWM off
    pi.set_PWM_dutycycle(RED,   255) # PWM off
    pi.set_PWM_dutycycle(BLUE,  0) # PWM offt
    # Temps de pause suivant l'appareil (A40 ou EOS ...)
    # time.sleep(0.5)

    # temp lock file in directory
    open("/home/pi/lock", "a").close()
    # Take picture and download it
    try:
        gpout = subprocess.check_output("sudo gphoto2 --capture-image-and-download --filename {}/photo%y%m%d%H%M%S.jpg".format(imgDir), stderr=subprocess.STDOUT, shell=True)
        print(gpout)
    except subprocess.CalledProcessError:
        # Create empty file in directory
        open("/home/pi/NoCamera", "a").close()
        cptR = 0
        r = 255
        g = 0
        b = 0
        timeOutSec = 10.0
        startTime = time.time()
        while (time.time()-startTime) < timeOutSec:
            if (pi.read(SWITCH)):
                break
            time.sleep(0.15)
            cptR += 1
            if cptR>2:
                cptR = 0
                r = abs(255-r)
                pi.set_PWM_dutycycle(GREEN, min(255,max(g,0)))
                pi.set_PWM_dutycycle(RED,   min(255,max(r,0)))
                pi.set_PWM_dutycycle(BLUE,  min(255,max(b,0)))

        os.remove("/home/pi/NoCamera")
        time.sleep(0.15)
                
    # Delete lock file
    os.remove("/home/pi/lock")
    print("Photo downloaded ... ready for next round")

                
class gestionHardware(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):

        # LED colors value
        r = 0
        g = 0
        b = 0
        speed = 10 # Vitesse du Fade
        btnState = False

        #~ Boucle infinie (ctrl+C pour arreter)
        while True:
            btnState = pi.read(SWITCH)
            if (btnState):
                prendrePhoto()
                
                # Setting LEDs back to ready mode
                r = 255
                g = 0
                b = 0

            else:
                # Etat d'attente d'une action utilisateur quand tout va bien
                # On fait un fade sur la led verte
                b = 0
                if r>0:
                    r = -abs(speed)

                g += speed
                if g>=255:
                    g = 255
                    speed = -abs(speed)
                elif g<=0:
                    g = 0
                    speed = abs(speed)


                # PWM
                pi.set_PWM_dutycycle(GREEN, min(255,max(g,0)))
                pi.set_PWM_dutycycle(RED,   min(255,max(r,0)))
                pi.set_PWM_dutycycle(BLUE,  min(255,max(b,0)))

                time.sleep(0.1)


def exitLoop():
    print("Goodbye")
    # Switch off LEDs
    pi.set_PWM_dutycycle(GREEN, 0) # PWM off
    pi.set_PWM_dutycycle(RED,   0) # PWM off
    pi.set_PWM_dutycycle(BLUE,  0) # PWM off
    pi.write(HIGH3V, 0)
    
    # GPIO object stop
    pi.stop()
    #sys.exit(0)

if __name__ == '__main__':
    # Clean "lock" file on startup
    if os.path.exists("/home/pi/lock"):
        os.remove("/home/pi/lock")
    if os.path.exists("/home/pi/NoCamera"):
        os.remove("/home/pi/NoCamera")

    print("Appuyer sur echap pour fermer l'application")
    GPIO_setup()
    #signal.signal(signal.SIGINT, exitLoop)

    # Creation des 2 threads
    hardLoop = gestionHardware()
    mySlide = sl.Slideshow(imgDir)

    # Démarre les threads
    hardLoop.start()
    mySlide.start()

    # Attend la fin du Slideshow
    mySlide.join()

    exitLoop()

