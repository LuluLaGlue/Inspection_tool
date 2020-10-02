# Inspection_tool
Python script to compare a video feed/file frame by frame with an image reference.
When a difference is detected, the algorithm outlines the difference, creates a grayscale histogram of the frame 
and saves the resulting .pngs in a folder.

Use <code>python temp_test.py -h</code> for help

e.g:
<code>python temp_test.py -f tmp_img  -d 900,741 -p './imag.png' -v rtsp://80.60.167.150:554/video -s 60</code>

will launch the script for a 900 by 741px image named imag.png located in the current directory, the video feed is located at rtsp://80.60.167.150:554/video, the production line goes at 60m/min and the resulting images and histograms will be saved to the tmp_img directory.

If you wish to use several video feeds/file use the same -v option and separate the path to the videos with "," : <code>rtsp://80.60.167.150:554/video,/this/is/another/path</code>
