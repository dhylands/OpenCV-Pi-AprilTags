# import the necessary packages
from picamera2 import Picamera2
from threading import Event, Thread

class Pi2VideoStream:
    def __init__(self, resolution=(640, 480), framerate=32, **kwargs):
        # initialize the camera
        self.camera = Picamera2()
        #self.camera.video_configuration.controls.FrameRate = framerate
        config = self.camera.create_video_configuration(main={"format": 'XRGB8888', "size": resolution})
        self.camera.configure(config)

        self.frame_available_event = Event()

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        self.camera.start()
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            self.frame = self.camera.capture_array(wait=True)
            self.frame_available_event.set()
            #print(f'{time.time():.3f}')
            if self.stopped:
                self.camera.stop()
                return

    def read(self):
        # return the frame most recently read
        self.frame_available_event.wait()
        self.frame_available_event.clear()
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
