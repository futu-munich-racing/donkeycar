import os
import time
import numpy as np
from PIL import Image
import glob

import cv2

class BaseCamera:

    def run_threaded(self):
        return self.frame

class PiCamera(BaseCamera):
    def __init__(self, resolution=(120, 160), framerate=20):
        from picamera.array import PiRGBArray
        from picamera import PiCamera
        resolution = (resolution[1], resolution[0])
        # initialize the camera and stream
        self.camera = PiCamera()  # PiCamera gets resolution (height, width)
        self.camera.resolution = resolution
        self.enable_undistort = enable_undistort
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="rgb",
                                                     use_video_port=True)
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('PiCamera loaded.. .warming camera')
        time.sleep(5)

    def run(self):
        f = next(self.stream)
        frame = f.array
        self.rawCapture.truncate(0)
        return frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            if not self.on:
                break

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('Stopping PiCamera...', end="")
        time.sleep(.1)
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()
        print('done.')

class CalibratedPiCamera(PiCamera):
    def __init__(self, resolution=(120, 160), framerate=20):

        super.__init__(self, resolution=resolution, framerate=framerate)

        # Camera calibration parameters
        self.K = np.load(os.path.dirname(os.path.abspath(__file__))+'/K.npy')
        self.D = np.load(os.path.dirname(os.path.abspath(__file__))+'/D.npy')
        #self.K = np.array([[479.8318979408517, 0.0, 954.2149111061347], [0.0, 479.85715507348357, 539.5262623708809], [0.0, 0.0, 1.0]])
        #self.D = np.array([[0.01742013226378499], [-0.07783488206037675], [0.10561876029481891], [-0.05533474379824904]])
        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(self.K, self.D, np.eye(3), self.K, resolution, cv2.CV_16SC2)
    
    def undistort(self, img):
        undistorted_img = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def run(self):
        f = next(self.stream)
        frame = self.undistort(f.array)
        self.rawCapture.truncate(0)
        
        return frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = self.undistort(f.array)
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            if not self.on:
                break