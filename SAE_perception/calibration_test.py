import numpy as np
import cv2 as cv
import glob
import os

SHOW_CORNERS = True  # set True to preview detected corners (press a key to advance)

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
objp = np.zeros((6*9, 3), np.float32)
objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

script_dir = os.path.dirname(os.path.abspath(__file__))
images = sorted(glob.glob(os.path.join(script_dir, 'imgs/*.png')))

if not images:
    raise RuntimeError("No .png files found in imgs/")

image_size = None  # (width, height)

for fname in images:
    img = cv.imread(fname)
    if img is None:
        print("Could not read image: {}".format(fname))
        continue

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    image_size = gray.shape[::-1]

    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (9, 6), None)

    # If found, add object points, image points (after refining them)
    if ret:
        objpoints.append(objp)
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        if SHOW_CORNERS:
            cv.drawChessboardCorners(img, (9, 6), corners2, ret)
            cv.imshow('img', img)
            cv.waitKey(0)
    else:
        print("Chessboard corners not found in image: {}".format(fname))

cv.destroyAllWindows()

if len(objpoints) == 0:
    raise RuntimeError("No chessboard corners were found in any image")

print("Using {} of {} images for calibration".format(len(objpoints), len(images)))

# Calibrate the camera
_, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, image_size, None, None)

# Save calibration to disk
out_path = os.path.join(script_dir, 'calibration.npz')
np.savez(out_path, mtx=mtx, dist=dist, image_size=np.array(image_size))
print("Saved calibration to {}".format(out_path))
