#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Test de la mesure de l'espace utilisé par un dossier
et de l'espace disque dispo USB
"""

import os
import subprocess

usbRoot = "/media/pi/"
imgDir = "/home/pi/public_html/PhotoBooth/images/PhotosNiort"
#imgDir = "/home/pi/PhotoBooth"

    
def testUSBKey(imgDir):
    """testUSBKey
       Description :
       Teste la présence d'une clef USB et vérifie si l'espace disponible
       sur la clef est suffisant pour recopier les photos du dossier du photobooth
       Usage :
         bUSB, bOK = testUSBKey(imgDir)
    """
    # List des Media USB branchés
    usbList = os.listdir("/media/pi")
    if (len(usbList)>0):
        bUSB = True
        print "USB detected: "+usbList[0]
        usbDir = "/media/pi/"+usbList[0]
        try:
            # Espace dispo sur la celf USB
            out_df = subprocess.check_output(["df","--output=avail",usbDir])
            tailleDispo = float(out_df.split("\n")[1])
            
            # Espace occupé par les photos
            out_du = subprocess.check_output(["du", "--summarize", imgDir])
            tailleDir = float(out_du.split("\t")[0])

        except subprocess.CalledProcessError:
            print "Erreur a l'appel de 'df {}' ou 'du --summarize {}".format(usbDir, imgDir)
            bUSB = False
            tailleDispo = 0.0
            tailleDir = 0.0

    else:
        print("Pas d'USB")
        bUSB = False
        tailleDispo = 0.0
        tailleDir = 0.0
        

    print "Taille du dossier de photos {}ko".format(tailleDir)
    if (bUSB):
        print "Taille dispo sur la clef USB {}ko".format(tailleDispo)

    return bUSB, (tailleDispo>tailleDir)

if __name__ == '__main__':
    bUSB, bOK = testUSBKey(imgDir)
    print "USB:{}, espace suffisant:{}".format(bUSB, bOK)
    

