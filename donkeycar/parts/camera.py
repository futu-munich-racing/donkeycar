from pathlib import Path
import os
import time
import numpy as np
from PIL import Image
import glob

import cv2


DEFAULT_DIM = (341, 256)
DEFAULT_K = np.array([[88.68579615592131, 0.0, 168.71152971640518],
                      [0.0, 89.15882834964788, 129.37399022937905],
                      [0.0, 0.0, 1.0]]).reshape(3, 3)
DEFAULT_D = np.array([[-0.0427328117588215], [0.09259025148682316], [-0.12141271631637485], [0.04770722474030203]]).reshape(4)

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
    def __init__(self, resolution=DEFAULT_DIM, framerate=20):

        print('PiCamera should init shortly after this msg')
        super().__init__(resolution=resolution, framerate=framerate)
        print('PiCamerea should be initialised')

        # Camera calibration parameters
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        if False: #(current_dir / 'K.npy').exists() and (current_dir / 'D.npy').exists():
            self.K = np.load(current_dir / 'K.npy')
            self.D = np.load(current_dir / 'D.npy')
        else:
            self.K = DEFAULT_K
            self.D = DEFAULT_D

        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(self.K,
                                                                   self.D,
                                                                   np.eye(3),
                                                                   self.K,
                                                                   resolution,
                                                                   cv2.CV_16SC2)

        print('Calibrated camera initialised. Resolution: %dx%d' % self.camera.resolution)
        
    def undistort(self, img):
        undistorted_img = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def run(self):
        f = next(self.stream)
        frame = f.array
        print(frame.shape)
        frame = self.undistort(frame)
        self.rawCapture.truncate(0)
        
        return frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            frame = f.array
            frame = self.undistort(frame)
            self.frame = frame
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            if not self.on:
                break
