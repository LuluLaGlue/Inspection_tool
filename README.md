# Inspection_tool
Python script to compare a video feed/file frame by frame with an image reference.
When a difference is detected, the algorithm outlines the difference, creates a grayscale histogram of the frame 
and saves the resulting .pngs in a folder.

Use python temp_test.py -h for help

e.g:
python temp_test.py -d tmp_img  -s 900,741 -p './imag.png' -v rtsp://80.60.167.150:554/video -m 60

will launch the script for a 900 by 741px image named imag.png located in the current directory, the video feed is located at rtsp://80.60.167.150:554/video, the production line goes at 60m/min and the resulting images and histograms will be saved to the tmp_img directory.
