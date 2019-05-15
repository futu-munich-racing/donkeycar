import argparse
import os
import glob
import time

import numpy as np

import cv2

def undistort(img, K, D):
    h, w = img.shape[:2]

    t0 = time.time()
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, (w, h), cv2.CV_16SC2)
    t1 = time.time()

    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    t2 = time.time()

    print(t1-t0, t2-t1, t2-t0)
    
    return undistorted_img

def main():
    
    # Parse input arguments e.g. folder containing the images
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image')
    parser.add_argument('-K', default='K.npy')
    parser.add_argument('-D', default='D.npy')
    parser.add_argument('-x', '--newx', default=0, type=int)
    parser.add_argument('-y', '--newy', default=0, type=int)
    args = parser.parse_args()
    
    K = np.load(args.K)
    D = np.load(args.D)

    img = cv2.imread(args.image)

    if args.newx > 0 and args.newy > 0:
        img = cv2.resize(img, (args.newy, args.newx))

    img_u = undistort(img, K, D)
    cv2.imshow('original image', img)
    cv2.imshow('undistorted image', img_u)
    key = ''
    print("Press ESC to exit.")
    while key != 27:
        key = cv2.waitKey(100)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()