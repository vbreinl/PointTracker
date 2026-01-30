import cv2
import numpy as np

class trackedPoint():
    def __init__(self, id, contour):

        self.id = id
        self.buffer = [1]
        self.missedFrames = 0
        self.pos = getContourXY(contour)
        self.X = self.pos[0]
        self.Y = self.pos[1]
        self.frequency = None


    # Remember new position and save that LED was on
    def updateTrack(self, pos : tuple):

        self.pos = pos
        self.buffer.append(1)
        self.missedFrames = 0

    #Tracked point missed a frame, we append a 0 to buffer and count up missed frames
    def missedFrame(self):

        self.buffer.append(0)
        self.missedFrames += 1

    #Get own distance from a point
    def getDistance(self, pos : tuple):

        distance = np.linalg.norm(np.array(self.pos) - np.array(pos))

        return distance 

    #Calculate Frequency in HZ of trackedPoint with fast fourier transform given provided fps
    def getFrequency(self, fps : int):

        signal = np.array(self.buffer) - np.mean(self.buffer)
        ftt_result = np.fft.fft(signal)
        magnitudes = np.abs(ftt_result)

        half_n = len(magnitudes) // 2
        relevant_magnitudes = magnitudes[:half_n]
        peak_bin = np.argmax(relevant_magnitudes)
        hz = peak_bin * (fps / len(self.buffer))
        self.frequency = hz
        print(f"ID: {self.id}, Pos {self.pos}, Buffered state: {self.buffer} Frequency: {hz}")

        return hz

    def trimBuffer(self, size):
        self.buffer = self.buffer[:size]

    # def X(self):
        # return self.pos[0]

    # def Y(self):
        # return self.pos[1]

#Helper Functions

#Get XY coordinates from a contour
@staticmethod
def getContourXY(contour):
    moments = cv2.moments(contour)
    #OpenCV bug sometimes returns 0 in moments in that case return None
    if not moments['m10'] == 0:
        contour_xy = (int(moments['m10']/moments['m00']), int(moments['m01']/moments['m00']))
        return contour_xy
    else:
        return None
