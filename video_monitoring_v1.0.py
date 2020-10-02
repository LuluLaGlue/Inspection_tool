#!/usr/bin/env python
# coding: utf-8
# Comparaison de flux video avec une image de reference
# Par Lucien Sigayret
# 30 - 09 - 2020
# Version @1.0

import os
import sys
import cv2
import time
import imutils
import argparse
import numpy as np
import multiprocessing
from datetime import datetime
from matplotlib import pyplot as plt
from skimage.metrics import structural_similarity

def arg_parser():
    parser = argparse.ArgumentParser(description='Monitor camera feed')
    
    parser.add_argument('-p', '--path', 
                        required=True, 
                        help='Path to reference image')
    parser.add_argument('-v', '--video',
                        required=True,
                        help="Path to video feed, if -m is set to true separate the different feeds with a \',\' : feed1,feed2,feed3")
    parser.add_argument('-d', '--dimension',
                        required=True,
                        help="dimensions of the reference image or video feed: width,height")
    parser.add_argument('-f', '--folder',
                       required=True,
                       help="Path to the folder in which to save resulting images")
    parser.add_argument('-s', '--speed', type=int,
                       required=True,
                       help="Production line speed in m/min. Integer.")
    parser.add_argument('-m', '--multi',
                       default=False, help="If more than one camera feed is used, must be set to True. Boolean, Default=False")

    argv = vars(parser.parse_args())
    argv["width"] = int(argv["dimension"].split(',')[0])
    argv["height"] = int(argv["dimension"].split(',')[1])
    argv.pop('dimension')
    argv["speed"] = argv["speed"]/60
    if not os.path.exists(argv["folder"]) or not os.path.isdir(argv["folder"]):
        print("Repository {} does not exist/is not valid.".format(argv["folder"]))
        create = input("Do you wish to create it ? (yes/no)\n").lower()
        if create != "yes" and create != "no" and create != "y" and create != "n":
            create = input("Please enter yes or no: ").lower()
        if create == "yes" or create == "y":
            try:
                os.mkdir(argv["folder"])
                print("Repository created.")
            except FileNotFoundError:
                print('# ------------- ERROR ------------- #')
                print("Repository name {} is not valid.".format(argv["folder"]))
                print('# --------- SCRIPT STOPPED --------- #')
                tz_end = datetime.now()
                print("Script stopped: {}".format(str(tz_end)))
                sys.exit(1)
                
        else:
            print("# --------- SCRIPT STOPPED --------- #")
            tz_end = datetime.now()
            print("Script stopped: {}".format(str(tz_end)))
            sys.exit(0)
    print("Images will be saved in the "+argv["folder"]+" folder.")
    return argv

def video_comp(cam_num):
    print("Connecting to camera feed {}...".format(cam_num))
    capture = cv2.VideoCapture(cam_num)
    if capture is None or not capture.isOpened():
        print('# ------------- ERROR ------------- #')
        print("Unable to capture video feed/read video file: {}.".format(str(cam_num)))
        print("Please check the -v argument")
        print('# --------- SCRIPT STOPPED --------- #')
        tz_end = datetime.now()
        print("Script stopped: {}".format(str(tz_end)))
        sys.exit(1)
    try:
        print("Connection to {} ok.".format(cam_num))
        print("# -------------------------------- #")
        ref_frame_tmp = cv2.imread(argv["path"])
        ref_frame_tmp = cv2.resize(ref_frame_tmp, (argv["width"], argv["height"]), interpolation = cv2.INTER_AREA)
        ref_frame = cv2.cvtColor(ref_frame_tmp, cv2.COLOR_BGR2GRAY)
        ref_smooth = cv2.bilateralFilter(ref_frame, 9, 75, 75)
        del(ref_frame_tmp, ref_frame)
        argv.pop("video")
        while(True):
            sleep_start = datetime.now()
            contours_circles = []
            ret, frame = capture.read()
            frame = cv2.resize(frame, (argv["width"], argv["height"]), interpolation = cv2.INTER_AREA)
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_smooth = cv2.bilateralFilter(frame_gray, 9, 75, 75)
            (score, diff) = structural_similarity(ref_smooth, frame_smooth, full=True)
            diff = (diff * 255).astype("uint8")
            del(frame_gray)

            if score < 0.9:
                print("Flaw detected with a score of: {}".format(round(score, 5)))
                thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)

                for i in cnts:
                    (x, y, w, h) = cv2.boundingRect(i)
                    aspect_ratio = float(w)/h
                    area = cv2.contourArea(i)
    #                 if (area < 18000) & (aspect_ratio < 3.5):
                    contours_circles.append(i)
                    counting = len(contours_circles)
            
                tmp_hist = plt.hist(frame_smooth.ravel(), 256, [0, 256], color='red', histtype='step')
                plt.title('Grayscale Histogram')
                plt.ylabel('Intensity')
                plt.grid(True, which='both', axis='both', linestyle='--')
                axes = plt.gca()
                axes.set_xlim([0, 250])
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                draw = cv2.drawContours(frame, contours_circles, -1, (0, 255, 0), 2)
                cv2.putText(draw, "Number of defects: " + str(counting), (10, 450), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
                
                date = datetime.now()
                os.mkdir(argv["folder"] + "/Flaw_"+str(date))
                cv2.imwrite(argv["folder"]+"/Flaw_"+str(date)+"/Photo_"+str(date)+".png", draw)
                plt.savefig(argv["folder"]+"/Flaw_"+str(date)+"/Hist_"+str(date)+".png")
                print("Image and histogram saved in " + argv["folder"])
                print("# -------------------------------- #")
                sleep_end = datetime.now()
                sleep_time = (3/argv["speed"]) - (sleep_end - sleep_start).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)#3 is the filmed distance of the monitored line
#             cv2.imshow("Video Feed", draw)

        capture.release()
        cv2.destroyAllWindows()

    except KeyboardInterrupt:
        capture.release()
        cv2.destroyAllWindows()
        raise
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback_details = {'lineno': exc_traceback.tb_lineno,
                            'name': exc_type.__name__,
                            }
        del(exc_type, exc_value, exc_traceback)
        print('# ------------- ERROR ------------- #')
        print('Something went wrong on line {}.'.format(str(traceback_details["lineno"])))
        print("Error type: {}".format(traceback_details["name"]))
        print('# --------- SCRIPT STOPPED --------- #')
        tz_end = datetime.now()
        capture.release()
        cv2.destroyAllWindows()
        print("Script stopped: {}".format(str(tz_end)))
        sys.exit(1)
try:
    tz_start = datetime.now()
    print("Script started: {}".format(str(tz_start)))
    print('# --------------- PRESS CONTROL + C TO STOP SCRIPT --------------- #')
    argv = arg_parser()
    
    if argv["multi"] == "True":
        argv["video"] = argv["video"].split(',')
        p = multiprocessing.Pool()
        p.map(video_comp,argv["video"])
    else:
        video_comp(argv["video"])

    sys.exit(0)
except KeyboardInterrupt:
    try:
        print('\n# ------------- STOP ------------- #')
        print('Script succesfully terminated by user. \nResulting images (if existing) can be found in the {} folder.'.format(argv["folder"]))
        tz_end = datetime.now()
        print("Script ended: {}".format(str(tz_end)))
        sys.exit(0)
    except NameError:
        print('\n# ------------- STOP ------------- #')
        print('Script succesfully terminated by user. \nResulting images (if existing) can be found in the {} folder.'.format("destination"))
        tz_end = datetime.now()
        print("Script ended: {}".format(str(tz_end)))
        sys.exit(0)
