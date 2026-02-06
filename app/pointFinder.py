import cv2
import numpy as np
import logging
from trackedPoint import trackedPoint, getContourXY, getBufferLength
from math import isclose


logger = logging.getLogger(__name__)
logger_led = logging.getLogger(name=f"{__name__}.LED-Tracking")
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
active_track_keepalive = 45 # Amount of missed frames till we assume search track is dead
fps = 120


def findLED(frame, threshold, fps):

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

    logger.debug("Processed frames and feteched contours")


    #Search mode for leds we already IDed by frequency, we assume these are our LEDs
    #We try to match contours to our stored LED tracks
    if len(tracked_leds) is not 0:
        unmatched_contours = []
        for led in tracked_leds.values():
            matched = False

            for cont in contours:

                cont_xy = getContourXY(cont)

                if cont_xy is not None:
                
                    distance = led.getDistance(cont_xy)

                    if distance is not None:
                        # If distance is below threshold we assume the contour belongs to atracked led
                        if distance < match_distance:
                            led.updateTrack(cont_xy)

                            matched = True

                #We remember contours that are unmatched
                if not matched:
                    unmatched_contours.append(cont)

            #If we didn't match tracked led we missed a frame and count up
            if not matched:
                led.missedFrame()

        contours = unmatched_contours

    logger.debug("Matched contours to tracked LEDs")


    #If tracked led missed too many frames it is dead and we dont remember it
    alive_leds = {}
    for key in tracked_leds:
        led = tracked_leds.get(key)
        
        #We remember alive leds
        if not led.missedFrames >= tracked_led_keepalive:
            alive_leds.update(key = led)
            search_mode = True
    
        #Dead LED
        else:
            logger.debug("Dead LED track")
    
    tracked_leds = alive_leds
    

    #Search mode for unindentified tracks
    if search_mode:

        # We want to compare each track to each other if they are close to each other and remove one of them if they are very close
        # Preferably the one with the smaller buffer
        # Remember everything -> only forget if the distance is close and the buffer is smaller
        if len(active_tracks) is not 0:
            compare_track : trackedPoint

            active_tracks.sort(key=getBufferLength, reverse=True)

            # Use a set as it cant contain duplicates
            real_tracks = []
            duplicate_tracks = set()

            for track_idx in range(len(active_tracks)):
                
                # When track is already marked as duplicate we continue with next element
                if track_idx in duplicate_tracks:
                    continue
                
                for compare_idx in range(track_idx + 1, len(active_tracks)):

                    # When compare track is already marked as duplicate we continue with next element
                    if compare_idx in duplicate_tracks:
                        continue
                    
                    track = active_tracks[track_idx]
                    compare_track = active_tracks[compare_idx]
                    
                    # Compared track is a duplicate
                    if track.getDistance(compare_track.pos) < match_distance:

                        #Since we sorted for buffer length we know track has larger one
                        duplicate_tracks.add(track_idx)

            for track in range(len(active_tracks)):
                if track not in duplicate_tracks:
                    real_tracks.append(active_tracks[track])

            active_tracks = real_tracks
            
        logger.debug("Checked active tracks for duplicates")


        #Match contours to active tracks 
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
                                    
                                    #We are updating the track frames more than once so we check if already matched to one
                                    if not track_matched:
                                        track.updateTrack(cont_xy)
                                        track_matched = True
                                    
                                    matched = True

                    #We only remember the contours which haven't been matched to a track
                    if not matched:
                        unmatched_contours.append(cont) 
                        #track = trackedPoint(cont)
                        #active_tracks.append(track)

            contours = unmatched_contours

            if not track_matched:
                track.missedFrame()

        logger.debug("Matched contours to active_tracks")

        for cont in contours:
            if getContourXY(cont) is not None:
                track = trackedPoint(cont)
                active_tracks.append(track)
        logger.debug("Loaded unmatched contours in active_tracks")

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

        logger.debug("Rolling buffer")

        #If LED is not matching its IDd frequency we dont remember it
        alive_leds = {}
        for key in tracked_leds:
            led = tracked_leds.get(key)

            if led.checkFrequency(fps, .1):
                led.trimBuffer(150)
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
                    track.trimBuffer(150)
                    track.getFrequency(fps)

                    #If the track is close to a target frequency we give it an ID with the value of target frequency
                    if isclose(track.frequency, led1_frequency, rel_tol=.1) and led1_frequency not in tracked_leds:
                        track.setID(led1_frequency)
                        tracked_leds.update({track.id : track})
                        logger.debug(f"Matched {track.pos} with {track.frequency} to {led1_frequency}HZ-LED")

                        #We dont need to remember matched tracks
                        matched = True

                    if isclose(track.frequency, led2_frequency, rel_tol=.1) and led2_frequency not in tracked_leds:
                        track.setID(led2_frequency)
                        tracked_leds.update({track.id : track})
                        logger.debug(f"Matched {track.pos} with {track.frequency} to {led2_frequency}HZ-LED")


                        #We dont need to remember matched tracks
                        matched = True

                    if isclose(track.frequency, led3_frequency, rel_tol=.1) and led3_frequency not in tracked_leds:
                        track.setID(led3_frequency)
                        tracked_leds.update({track.id : track})
                        logger.debug(f"Matched {track.pos} with {track.frequency} to {led3_frequency}HZ-LED")

                        #We dont need to remember matched tracks
                        matched = True

                #We only need to remember unmatched tracks
                if not matched:
                    unmatched_tracks.append(track)

            active_tracks = unmatched_tracks

        buffer_timing = 0
        logger.debug("Reset buffer timing")

    return processed_frame, active_tracks, tracked_leds
