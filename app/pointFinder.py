import cv2
import numpy as np
import logging
from trackedPoint import trackedPoint, getContourXY
from math import isclose


logger = logging.getLogger(__name__)
logging.basicConfig(filename="/dev/stdout", level=logging.DEBUG)

active_tracks = []
tracked_leds = {}

match_distance = 5 # Distance at which a new contour is correlated with an active track of the previous frame, i.e. new contour is close to where led was in last frame -> our led

buffer_timing = 0
buffer_size = 60
search_mode = True

led1_frequency = 10
led2_frequency = 15
led3_frequency = 20

tracked_led_keepalive = 60  # Amount of missed frames till we assume led track is dead
active_track_keepalive = 30 # Amount of missed frames till we assume search track is dead
fps = 60


def findLED(frame, threshold):

    global search_mode
    global buffer_timing
    global active_tracks
    global tracked_leds

    track : trackedPoint
    led : trackedPoint
    contours : list


    _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_TOZERO) #Apply threshold to frame

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #Convert to grayscale

    contours, hierarchy = cv2.findContours(frame,
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

    colored_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    processed_frame = cv2.drawContours(image=colored_frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=3, hierarchy=hierarchy)

#    contours = list(contours)


    #If buffer timing started fill buffer with contours
    # if buffer_timing == 0:
        # logger.debug("Buffer init")

        # if search_mode:

            # for cont in contours:
                # matched = False
                # cont_xy = getContourXY(cont)
                # if cont_xy is not None:
                    # if len(active_tracks) > 0:
                        # for track in active_tracks:
                                # distance = track.getDistance(cont_xy)

                                # if distance is not None:
                                    # # If distance is below threshold we assume the contour belongs to an active track
                                    # if distance < match_distance:
                                        # track.updateTrack(cont_xy)

                                        # matched = True

                    # if not matched: 
                        # track = trackedPoint(cont)
                        # active_tracks.append(track)

                # # if getContourXY(cont) is not None:
                # # # Create a track from contour
                    # # track = trackedPoint(cont)
                    # # active_tracks.append(track)
            
            # #Check if contour is new or already exisits as track
            

    # # If buffer has ran first frame and has content
    # else:
        

    #Search mode for leds we already IDed by frequency, we assume these are our LEDs
    unmatched_contours = []
    for led in tracked_leds.values():
        matched = False


        for cont in contours:
            #So we can pop items while in loop
            # NEVER POP ITEMS WHILE ITERATING OVER IT AGAIN!!!

            cont_xy = getContourXY(cont)
            
            if cont_xy is not None:
            
                distance = led.getDistance(cont_xy)

                if distance is not None:
                    # If distance is below threshold we assume the contour belongs to atracked led
                    if distance < match_distance:
                        led.updateTrack(cont_xy)
                        #We dont remember matched contours

                        matched = True
                        #break
            
            #We remember contours that are unmatched
            if not matched:
                unmatched_contours.append(cont)

        contours = unmatched_contours

        #If we didn't match tracked led we missed a frame and count up
        if not matched:
            led.missedFrame()

    #If tracked led missed too many frames it is dead and we dont remember it
    alive_leds = {}
    for key in tracked_leds:
        led = tracked_leds.get(key)
        
        #We remember alive leds
        if not led.missedFrames >= tracked_led_keepalive:
            alive_leds.update(key = led)
            search_mode = True
        else:
            # Dead LED
            logger.debug("Dead LED track")
    
    tracked_leds = alive_leds

    #Search mode for unindentified tracks
    if search_mode:
        
        for track in active_tracks:
            track_matched = False
            
            unmatched_contours = []
            for cont in contours:
                matched = False
                cont_xy = getContourXY(cont)

                if cont_xy is not None:
                    if len(active_tracks) > 0:
                        #for track in active_tracks:
                            
                            distance = track.getDistance(cont_xy)

                            if distance is not None:
                                # If distance is below threshold we assume the contour belongs to an active track
                                if distance < match_distance:
                                    #TODO:  ISSUE
                                    # We are updating the track mutliple times per frame because multiple contours are being matched
                                    if not track_matched:
                                        track.updateTrack(cont_xy)
                                        track_matched = True
                                    
                                    matched = True

                    if not matched:
                        unmatched_contours.append(cont) 
                        #track = trackedPoint(cont)
                        #active_tracks.append(track)

            contours = unmatched_contours

            if not track_matched:
                track.missedFrame()

        for cont in contours:
            if getContourXY(cont) is not None:
                track = trackedPoint(cont)
                active_tracks.append(track)

        # # Get all stored active tracks 
        # for track in active_tracks:

            # #Get all contours from current frame
            # for cont in contours:

                # cont_xy = getContourXY(cont)
                # if cont_xy is not None:
                
                    # distance = track.getDistance(cont_xy)

                    # if distance is not None:
                        # # If distance is below threshold we assume the contour belongs to an active track
                        # if distance < match_distance:

                            # track.updateTrack(cont_xy)

                            # matched = True
                            # #break

            # # If we didn't match the track to any new contour we count up missed frames
            # if not matched:
                    # track.missedFrame()

        # If a track exceeds a threshold of missed_frames assume the track was noise and dont remember it
        alive_tracks = []
        for track in active_tracks:

            #We only remember our alive tracks
            if not track.missedFrames >= active_track_keepalive:
                alive_tracks.append(track)
            #And forget the dead ones
            else:
                logger.debug("Dead track")

        active_tracks = alive_tracks

    #Count up for buffer
    buffer_timing +=1

    # If buffer has reached desired size we calc frequency and try to ID
    if buffer_timing == buffer_size:
        
        other_track : trackedPoint
        tmp_tracks = active_tracks
        unmatched_tracks = []
        
        #TODO
        # We want to compare each track to each other if they are close to each other and remove one of them if they are very close
        # Preferably the one with the smaller buffer
        for track in active_tracks:
            for other_track in tmp_tracks:
                if not track.getDistance(other_track.pos) < match_distance:
                    unmatched_tracks.append(track)

        logger.debug("Rolling buffer")

        #If LED is not matching its IDd frequency we dont remember it
        alive_leds = {}
        for key in tracked_leds:
            led = tracked_leds.get(key)

            if led.checkFrequency(fps, .1):
                led.trimBuffer(300)
                alive_leds.update(key = led)
                continue
            else:
                logger.debug(f"LED {led.id} lost its frequency")

        tracked_leds = alive_leds

        # When we have all 3 LEDs tracked we skip searching unidentified contours
        #if tracked_leds.__len__ == 3:
        #    search_mode = False

        #If we are searching we try to ID tracks
        if search_mode:
            unmatched_tracks = []

            for track in active_tracks:
                
                matched = False

                logger.debug(f"ID: {track.id}, Pos {track.pos}, Buffered state: {track.buffer} Frequency: {track.frequency}")

                #Check if the track has age
                if len(track.buffer) > 180:
                    track.trimBuffer(300)
                    track.getFrequency(fps)

                    #If the track is close to a target frequency we give it an ID with the value of target frequency
                    if isclose(track.frequency, led1_frequency, rel_tol=.1):
                        track.setID(led1_frequency)
                        tracked_leds.update({track.id : track})

                        #We dont need to remember matched tracks
                        matched = True

                    if isclose(track.frequency, led2_frequency, rel_tol=.1):
                        track.setID(led2_frequency)
                        tracked_leds.update({track.id : track})

                        #We dont need to remember matched tracks
                        matched = True

                    if isclose(track.frequency, led3_frequency, rel_tol=.1):
                        track.setID(led3_frequency)
                        tracked_leds.update({track.id : track})

                        #We dont need to remember matched tracks
                        matched = True

                #We only need to remember unmatched tracks
                if not matched:
                    unmatched_tracks.append(track)
            
            active_tracks = unmatched_tracks

        buffer_timing = 0

    return processed_frame, active_tracks, tracked_leds
