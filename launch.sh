#!/bin/sh
module load python-3.7.3
python video_monitoring_v1.0.py -p './imag.png' -f tmp_img -d 900,741 -m False -v rtsp://80.60.167.150:554/video -s 500
