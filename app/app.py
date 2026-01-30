import cv2
import pointFinder
import numpy as np
import time
from trackedPoint import trackedPoint
#import matplotlib.pyplot as plt

cap = cv2.VideoCapture(4)
cap.set(cv2.CAP_PROP_FPS, 60)
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
last_frame = None
processing = True
threshold = 100
prev_frame_time = 0
search_mode = True



def __init__():

    return

if not cap.isOpened():

    print("Error: Could not open cam")
    exit()


while True:

    reading, frame = cap.read()

    # If no frames being read break
    if not reading:
        break

    if processing:

        while search_mode:
            frame, active_tracks = pointFinder.findLED(frame, threshold) #Apply given threshold to frame and find contours

    #Calculate and show FPS counter
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time)
    prev_frame_time = new_frame_time
    fps = str(int(fps))
    cv2.putText(frame, fps, (7, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
    
    track : trackedPoint
    for track in active_tracks:
        if len(track.buffer) > 60:
            cv2.line(frame, (track.X, track.Y - 5), (track.X, track.Y +5), (0, 0, 255), 1)
            cv2.line(frame, (track.X - 5, track.Y), (track.X + 5, track.Y), (0, 0, 255), 1)
            cv2.putText(frame, str(track.id), track.pos, cv2.FONT_HERSHEY_PLAIN, 1, (255, 0 ,0))

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
