#!/usr/bin/env python
"""
A pygame program to show a slideshow of all images buried in a given directory.

Originally Released: 2007.10.31 (Happy halloween!)

Modified by Giloop for Raspberry Pi Carnaval photobooth: 2015.03.06
"""
from __future__ import division
import argparse
import os
import subprocess
import stat
import sys
import time
import exifread

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

title = "Anniv Fred !"  # caption of the window...
waittime = 0   # default time to wait between images (in seconds)

def get_exif(fn):
    # Open image file for reading (binary mode)
    f = open(fn, 'rb')
    # Return Exif tags
    tags = exifread.process_file(f, details=False)
    f.close()
    return tags

def listImageFiles(top, extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
    fileList = []
    for f in os.listdir(top):
        name = os.path.join(top, f)
        mode = os.stat(name)[stat.ST_MODE]
        creation = os.stat(name)[stat.ST_CTIME]
        if stat.S_ISREG(mode):
            # Chech if it's a image file
            filename, ext = os.path.splitext(name)
            e = ext.lower()
            # Only add common image types to the list.
            if e in extensions:
                fileList.append((creation,name))

    # Sort list
    fileList = sorted(fileList)

    # Debug print
    #for (creation,name) in fileList:
    #    print 'Adding to list: ', name, 'date :', time.ctime(creation)

    # Return sorted list
    return fileList

def listImageFilesAndDate(topDir, extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
    # List directory content with pathname and stats
    fileList = (os.path.join(topDir, fn) for fn in os.listdir(topDir))
    fileList = ((os.stat(path), path) for path in fileList)
    # Keep regular files and add creation date
    fileList = ((stat[ST_CTIME], path)
           for stat, path in fileList if S_ISREG(stat[ST_MODE]))
    # TODO : filter images with extension

    # Sort by creation date
    fileList = sorted(fileList)
    
    return fileList

def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

# Catch ESC key to quit slideshow
def input(events):
    """A function to handle keyboard/mouse/device input events. """
    for event in events:  # Hit the ESC key to quit the slideshow.
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key == K_ESCAPE)):
            pygame.quit()
            sys.exit(0)


# Main function
def main(startdir="."):
    global title, waittime
    
    # setup mixer to avoid sound lag
    pygame.mixer.pre_init(44100, -16, 2, 2048) 
    pygame.init()

    # Test for image support
    if not pygame.image.get_extended():
        print "Your Pygame isn't built with extended image support."
        print "It's likely this isn't going to work."
        sys.exit(1)

    fileList = listImageFiles(startdir)  # this may take a while...
    if len(fileList) == 0:
        print "Sorry. No image found. Exiting."
        sys.exit(1)

    modes = pygame.display.list_modes()
    # print modes : [(1280, 800)]

    pygame.display.set_mode(max(modes))
    maxMode = max(modes)

    screen = pygame.display.get_surface()
    pygame.display.set_caption(title)
    #pygame.display.toggle_fullscreen()

    current = 0
    num_files = len(fileList)
    while(True):
        try:
            # Search for new images if not locked
            if (os.path.exists("/home/pi/lock")):
                bNew = False
            else:
                newList = listImageFiles(startdir)
                if (num_files == len(newList)):
                    bNew = False

                else:         
                    bNew = True
                    # Refresh list
                    del fileList
                    fileList = list(newList)
                    del newList
                    num_files = len(fileList)

	    # Choose file to load
            if (bNew):
                # If there's a new image, show it
                imgName = fileList[num_files-1][1]

            else:
                # No new image, get back to current
                imgName = fileList[current][1]
                # Increment counter
                current = (current + 1) % num_files;

            # Load image
            img = pygame.image.load(imgName)
            # check if associated sound exists
            sndName, ext = os.path.splitext(imgName)
            sndName += '.wav'
            if os.path.isfile(sndName):
                pygame.mixer.unpause()
                snd = pygame.mixer.Sound(sndName)  #load sound
            else:
                pygame.mixer.pause()
                snd = 0
                
            imgSize = img.get_rect().size
            img = img.convert()
            print "Size :", imgSize
            
            #Get exit rotation info
            tags = get_exif(imgName)
            rotation = 0.
            if 'Image Orientation' in tags.keys():
                if str(tags['Image Orientation']).lower() == 'Rotated 90 CW'.lower():
                    rotation = -90.
                    imgSize = (imgSize[1],imgSize[0])
                elif str(tags['Image Orientation']).lower() == 'Rotated 180'.lower():
                    rotation = 180.
                elif str(tags['Image Orientation']).lower() in ('Rotated 90 CCW'.lower(), 'Rotated 90'.lower()):
                    rotation = 90.
                    imgSize = (imgSize[1],imgSize[0])                            

            # Show it
            scales = (maxMode[0]/imgSize[0], maxMode[1]/imgSize[1])
            
            # rotate & rescale the image to fit the current display
            #img = pygame.transform.scale(img, max(modes))
            print "Image ",imgName, ", rotation ", rotation, ", scale ", min(scales)
            img = pygame.transform.rotozoom(img, rotation, min(scales))

            screen.fill((0,0,0))
            screen.blit(img, ((maxMode[0]-imgSize[0]*min(scales))/2, 0))
            pygame.display.flip()

            input(pygame.event.get())

            # Play sound or simply wait
            if snd==0:
                time.sleep(waittime)
            else:
                snd.play()
                time.sleep(snd.get_length())

        except pygame.error as err:
            print "Failed to display %s: %s" % (fileList[current], err)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Recursively loads images '
        'from a directory, then displays them in a Slidshow.'
    )

    parser.add_argument(
        'path',
        metavar='ImagePath',
        type=str,
        default='/home/pi/PhotoBooth',
        nargs="?",
        help='Path to a directory that contains images'
    )
    parser.add_argument(
        '--waittime',
        type=int,
        dest='waittime',
        action='store',
        default=2,
        help='Amount of time to wait before showing the next image.'
    )
    parser.add_argument(
        '--title',
        type=str,
        dest='title',
        action='store',
        default="Diaporama !",
        help='Set the title for the display window.'
    )
    args = parser.parse_args()
    waittime = args.waittime
    title = args.title
    main(startdir=args.path)
