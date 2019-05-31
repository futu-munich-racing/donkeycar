"""
CAR CONFIG
This file is read by your car application's manage.py script to change the car
performance.
EXMAPLE
-----------
import dk
cfg = dk.load_config(config_path='~/mycar/config.py')
print(cfg.CAMERA_RESOLUTION)
"""


import os

#PATHS
CAR_PATH = PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(CAR_PATH, 'data')
MODELS_PATH = os.path.join(CAR_PATH, 'models')

#VEHICLE
DRIVE_LOOP_HZ = 20
MAX_LOOPS = 100000

#CAMERA
CAMERA_RESOLUTION = (256, 341) #(240, 360) #(height, width)
CAMERA_FRAMERATE = DRIVE_LOOP_HZ
ENABLE_UNDISTORT = True

#STEERING
STEERING_CHANNEL = 0
STEERING_LEFT_PWM = 300 #30
STEERING_RIGHT_PWM = 500 #150

#THROTTLE
THROTTLE_CHANNEL = 1
THROTTLE_FORWARD_PWM = 200 #1200
THROTTLE_STOPPED_PWM = 390 #1500
THROTTLE_REVERSE_PWM = 500 #1800

#TRAINING
BATCH_SIZE = 128
TRAIN_TEST_SPLIT = 0.8


#JOYSTICK
USE_JOYSTICK_AS_DEFAULT = False #True #False
JOYSTICK_MAX_THROTTLE = 0.50
JOYSTICK_STEERING_SCALE = 1.0
AUTO_RECORD_ON_THROTTLE = True


TUB_PATH = os.path.join(CAR_PATH, 'tub') # if using a single tub

#ROPE.DONKEYCAR.COM
ROPE_TOKEN="9272347da7b0b39c8398547263f58e3adbeb35a7"
