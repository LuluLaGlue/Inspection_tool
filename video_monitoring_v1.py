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
import pandas as pd
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
    parser.add_argument('-m', '--multi', default=False, help="If more than one camera feed is used, must be set to True. Boolean, Default=False")
    parser.add_argument('-b', "--best_score", type=float, default=-1, help="Define the threshold at which you want to detect flaws, Integer, Default=1")
    parser.add_argument('-a', '--area', type=float, default=-1, help="Define the maximum flaw area to detect, all area defects bigger than this value will not be detected. Integer")
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

    print("Images will be saved in the {} folder.".format(argv["folder"]))
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
            if score > argv["best_score"]:
                print("Flaw detected with a score of: {}".format(round(score, 5)))
                thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
#                 print("Flaw area: ", end='', flush=True)
                idx = 0
                for i in cnts:
                    idx += 1
                    x, y, w, h = cv2.boundingRect(i)
                    roi = frame_smooth[y:y + h, x:x + w]
                    area = cv2.contourArea(i)
#                     print("Area surface: {} ".format(area), end='\r', flush=True)
                    if (argv["area"]):
                        if (area < argv["area"]):
                            contours_circles.append(i)
                            counting = len(contours_circles)
                            cv2.imwrite(argv["folder"]+str(idx) + '.png', roi) # save each defects
                            im_rect = cv2.rectangle(frame_smooth, (x, y), (x + w, y + h), (200, 0, 0), 2) # draw rectangle for each defects
                            cv2.imwrite(argv["folder"]+str(idx) + '.png', im_rect) # save frames witch rectangles for each defects

                    elif not argv["area"]:
                        contours_circles.append(i)
                        counting = len(contours_circles)
            
                tmp_hist = plt.hist(frame_smooth.ravel(), 256, [0, 256], color='red', histtype='step')
         
                time_flaw = datetime.now()
                x_width = str(capture.get(3))
                y_height = str(capture.get(4))
                plt.grid(True, which='both', axis='both', linestyle='--')
                axes = plt.gca()
                axes.set_xlim([0, 275])
                font = cv2.FONT_HERSHEY_SIMPLEX
                draw = cv2.drawContours(frame, contours_circles, -1, (0, 255, 0), 2)
                cv2.putText(draw, "Number of defects: {}. Time: {}. Width: {}. Height: {}.".format(str(counting), time_flaw, x_width, y_height), (10, 50), font, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
                date = datetime.now()
                year = datetime.today().year
                month = datetime.today().month
                day = datetime.today().day + 1
                date_folder = str(year) + '-' + str(month) + '-' + str(day)
                if not os.path.exists("{}/{}-{}-{}".format(argv["folder"], str(year), str(month), str(day))) or not os.path.isdir("{}/{}-{}-{}".format(argv["folder"], str(year), str(month), str(day))):
                    os.mkdir("{}/{}-{}-{}".format(argv["folder"], str(year), str(month), str(day)))
                
#                 df.to_csv("{0}/{1}/Data_{1}.csv".format(argv["folder"], str(date)), index=False, sep=',', float_format='%.0f')
                cv2.imwrite("{0}/{1}/Photo_{2}.png".format(argv["folder"], date_folder, str(date)), draw)
#                 test = date.now()
                plt.savefig("{0}/{1}/Hist_{2}.png".format(argv["folder"], date_folder, str(date)))
                plt.close()
#                 test_2 = date.now()
#                 print('TIME TO SAVE: {}'.format((test_2 - test).total_seconds()))
                print("\nImage and histogram saved in {}.".format(argv["folder"]))
                print("# -------------------------------- #")
                sleep_end = datetime.now()
                sleep_time = (3/argv["speed"]) - (sleep_end - sleep_start).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)#3 is the filmed distance of the monitored line
#             cv2.imshow("Video Feed", draw)

        capture.release()
        cv2.destroyAllWindows()
        plt.close()
    except KeyboardInterrupt:
        capture.release()
        cv2.destroyAllWindows()
        plt.close()
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
        plt.close()
        print("Script stopped: {}".format(str(tz_end)))
        sys.exit(1)

try:
    tz_start = datetime.now()
    print("Script started: {}".format(str(tz_start)))
    print('# --------------- PRESS CONTROL + C TO STOP SCRIPT --------------- #')
    argv = arg_parser()
    print("Max area detected: {}".format(argv["area"]))
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
