import cv2
import numpy as np
from trackedPoint import trackedPoint, getContourXY
from math import isclose

last_contours = []
active_tracks = list()
tracked_leds = list()

match_distance = 5 # Distance at which a new contour is correlated with an active track of the previous frame, i.e. new contour is close to where led was in last frame -> our led

buffer_timing = 0
buffer_size = 60
search_mode = True

led1_frequency = 10


def findLED(frame, threshold):

    global search_mode
    global buffer_timing

    track : trackedPoint


    _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_TOZERO) #Apply threshold to frame

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #Convert to grayscale

    contours, hierarchy = cv2.findContours(frame,
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

    colored_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    processed_frame = cv2.drawContours(image=colored_frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=3, hierarchy=hierarchy)

    
    
    # Frequency detection testing
    #while search_mode:

    #If buffer timing started fill buffer with contours
    if buffer_timing == 0:
        print("Buffer init")

        id = 0
        for cont in contours:

            if getContourXY(cont) is not None:
            # Create a track from contour
                track = trackedPoint(id, cont)
                active_tracks.append(track)
                id += 1

    # If buffer has ran first frame and has content
    else:

        matched = False
        # Get all stored active tracks 
        for track in active_tracks:

            #Get all contours from current frame
            for cont in contours:
                
                cont_xy = getContourXY(cont)
                if cont_xy is not None:
                
                    distance = track.getDistance(cont_xy)

                    if distance is not None:
                        # If distance is below threshold we assume the contour belongs to an active track
                        if distance < match_distance:

                            track.updateTrack(cont_xy)

                            matched = True
                            break

            # If we didn't match the track to any new contour we count up missed frames
            if not matched:
                    track.missedFrame()

    # If a track exceeds a threshold of missed_frames assume the track was noise and remove the dead track
    i = 0
    for track in active_tracks:
        if track.missedFrames >= 17:
            print("Dead track")
            active_tracks.pop(active_tracks.index(track))
        i+=1
    #Count up for buffer
    buffer_timing +=1
    
    if buffer_timing == buffer_size:
        print("Rolling buffer")
        for track in active_tracks:
            track.getFrequency(60)
            print(f"ID: {track.id}, Pos {track.pos}, Buffered state: {track.buffer} Frequency: {track.frequency}")
            track.trimBuffer(300)
            
            #Check if the track has age
            if track.buffer.__len__ > 180:
                #If the tracks frequency is close to one of our LEDs we assign it 
                if isclose(track.frequency, led1_frequency, rel_tol=1):
                    
                    return
                
        buffer_timing = 0

    return processed_frame, active_tracks
