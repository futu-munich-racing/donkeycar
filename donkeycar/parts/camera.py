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
    def __init__(self, resolution=(120, 160), framerate=20, n_history=1):
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
        #self.frame = None
        self.on = True

        self.frame_history = [None] * n_history
        self.last_frame_update = time.time()
        self.history_size = n_history

        print('PiCamera loaded.. .warming camera')
        time.sleep(2)


    def run(self):
        f = next(self.stream)
        frame = f.array
        self.rawCapture.truncate(0)
        return [frame] * self.history_size

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            _frame = f.array
            self.rawCapture.truncate(0)

            if time.time() > self.last_frame_update + 1 / self.camera.framerate:
                # We need to make sure make sure that we have atomic operation that the 
                # vehicle does not try to read when we are updating the history

                # Add new frame to the 
                _frame_history = self.frame_history.append(_frame)
                # Remove the oldest item
                _ = _frame_history.pop(0)
                # Update the history
                self.frame_history = _frame_history

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

    def run_threaded(self):
        return self.frame_history

class CalibratedPiCamera(PiCamera):
    def __init__(self, resolution=DEFAULT_DIM, framerate=20):

        print('PiCamera should init shortly after this msg')
        super().__init__(resolution=resolution, framerate=framerate)
        print('PiCamera should be initialised')

        # Camera calibration parameters
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        w, h = self.camera.resolution
        print(w,h)
        K_name = 'K_{w}_{h}.npy'.format(w=w, h=h)
        D_name = 'D_{w}_{h}.npy'.format(w=w, h=h)
        if (current_dir / K_name).exists() and (current_dir / D_name).exists():
            self.K = np.load(current_dir / 'K.npy')
            self.D = np.load(current_dir / 'D.npy')
        else:
            self.K = DEFAULT_K
            self.D = DEFAULT_D

        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(self.K,
                                                                   self.D,
                                                                   np.eye(3),
                                                                   self.K,
                                                                   resolution[::-1],
                                                                   cv2.CV_16SC2)


        time.sleep(2)
        print('Calibrated camera initialised. Resolution: %dx%d' % self.camera.resolution)

    def undistort(self, img):
        undistorted_img = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def run(self):
        frame = super().run()
        frame = self.undistort(frame)
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
