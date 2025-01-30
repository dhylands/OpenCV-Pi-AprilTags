# import the necessary packages
from fps import FPS
#from pivideostream import Pi2VideoStream
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import time
import cv2

#from picamera2 import Picamera2

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()
frame_available_event = threading.Event()

# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to
# warmup
vs = VideoStream(src=2)

#cam = cv2.VideoCapture(0)
#cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

vs.start()
#vs.stream = cv2.VideoCapture(0, cv2.CAP_OPENCV_MJPEG)
#vs = Pi2VideoStream().start()
time.sleep(2.0)

fps = FPS().start()

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

def detect_tags():
    # grab global references to the video stream, output frame, and
    # lock variables
    global outputFrame, lock

    arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    arucoParams = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

    # loop over frames from the video stream
    while True:
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        #_, frame = cam.read()
        frame = vs.read()
        if frame is None:
            continue

        fps.update()

        (corners, ids, rejected) = detector.detectMarkers(frame)

        if len(corners) > 0:
            # flatten the ArUco IDs list
            ids = ids.flatten()

            # loop over the detected ArUCo corners
            for (markerCorner, markerID) in zip(corners, ids):
                # extract the marker corners (which are always returned in
                # top-left, top-right, bottom-right, and bottom-left order)
                corners = markerCorner.reshape((4, 2))
                (topLeft, topRight, bottomRight, bottomLeft) = corners

                # convert each of the (x, y)-coordinate pairs to integers
                topRight = (int(topRight[0]), int(topRight[1]))
                bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
                topLeft = (int(topLeft[0]), int(topLeft[1]))

                # draw the bounding box of the ArUCo detection
                line_color = (0, 0, 255)
                cv2.line(frame, topLeft, topRight, line_color, 2)
                cv2.line(frame, topRight, bottomRight, line_color, 2)
                cv2.line(frame, bottomRight, bottomLeft, line_color, 2)
                cv2.line(frame, bottomLeft, topLeft, line_color, 2)

                # compute the center (x, y)-coordinates of the ArUco marker
                cX = int((topLeft[0] + bottomRight[0]) / 2.0)
                cY = int((topLeft[1] + bottomRight[1]) / 2.0)

                # draw the ArUco marker ID on the image
                text = str(markerID)
                fontFace = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                thickness = 2
                sz = cv2.getTextSize(text, fontFace, fontScale, thickness)
                tx = sz[0][0]
                ty = sz[0][1]
                ctx = cX - tx // 2
                cty = cY + ty // 2

                cv2.rectangle(frame, (ctx - 1, cty + 3), (ctx + tx, cty - ty - 2), (255, 255, 255), cv2.FILLED)

                cv2.putText(frame, text, (ctx, cty), fontFace,
                    fontScale, line_color, thickness)

        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        text = timestamp.strftime("%A %d %B %Y %I:%M:%S%p") + f' FPS:{fps.fps():5.1f}     '
        cv2.putText(frame, text, (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
        help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
        help="ephemeral port number of the server (1024 to 65535)")
    args = vars(ap.parse_args())

    # start a thread that will perform motion detection
    #t = threading.Thread(target=detect_motion, args=(args["frame_count"],))
    t = threading.Thread(target=detect_tags)
    t.daemon = True
    t.start()

    # start the flask app
    app.run(host=args["ip"], port=args["port"], debug=True,
        threaded=True, use_reloader=False)

# release the video stream pointer
vs.stop()
fps.stop()
