import cv2
import pointFinder
import numpy as np
import time
import logging
from trackedPoint import trackedPoint
#import matplotlib.pyplot as plt

cap = cv2.VideoCapture(4)
cap.set(cv2.CAP_PROP_FPS, 60)
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/dev/stdout", level=logging.DEBUG)


last_frame = None
processing = True
threshold = 200
prev_frame_time = 0
search_mode = True



def __init__():

    return

if not cap.isOpened():

    logger.error("Cloud not open camera")
    exit()


while True:

    reading, frame = cap.read()

    # If no frames being read break
    if not reading:
        break

    if processing:
        frame, active_tracks, tracked_leds = pointFinder.findLED(frame, threshold) #Apply given threshold to frame and find contours

    #Calculate and show FPS counter
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time)
    prev_frame_time = new_frame_time
    fps = str(int(fps))
    cv2.putText(frame, fps, (7, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))

    track : trackedPoint
    for track in active_tracks:
        if len(track.buffer) > 60:
            #Paint cross over active track
            cv2.line(frame, (track.X, track.Y - 5), (track.X, track.Y +5), (0, 0, 255), 1)
            cv2.line(frame, (track.X - 5, track.Y), (track.X + 5, track.Y), (0, 0, 255), 1)
            #Write track ID next to cross
            cv2.putText(frame, str(active_tracks.index(track)), track.pos, cv2.FONT_HERSHEY_PLAIN, 1, (255, 0 ,0))
    
    led : trackedPoint
    for led in tracked_leds.values():
        #Paint cross over tracked led
        cv2.line(frame, (led.X, led.Y - 5), (led.X, led.Y +5), (0, 0, 255), 2)
        cv2.line(frame, (led.X - 5, led.Y), (led.X + 5, led.Y), (0, 0, 255), 2)
        
        #Write LED ID next to cross
        cv2.putText(frame, str(led.id) + " HZ", track.pos, cv2.FONT_HERSHEY_PLAIN, 2, (255, 0 ,0))

    #Display frame
    cv2.imshow("Video", frame)

    #Watch for client keypress
    key = cv2.waitKey(10)
    if key == ord('q'):     #If pressed 'Q' quit
        break
    elif key == ord('p'):   #If pressed 'P' disable processing
        
        if processing:
            processing = False
            print("Enabled post")
        else:
            print("Disabled post")
            processing = True
    elif key == ord('o'): # Increase threshold
        threshold += 5
    elif key == ord('l'): # Decrease threshold
        threshold -=5

cap.release()
cv2.destroyAllWindows()
