# import the necessary packages

import time

class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self.timestamps = []

    def start(self):
        # start the timer
        self.timestamps.append(time.monotonic_ns())
        return self

    def stop(self):
        # stop the timer
        pass

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self.timestamps.append(time.monotonic_ns())
        self.timestamps = self.timestamps[-10:]

    def elapsed(self) -> float:
        # return the total number of seconds between the start and
        # end interval
        if len(self.timestamps) > 1:
            return (self.timestamps[-1] - self.timestamps[0]) / 1000000000
        return 0.0

    def fps(self):
        # compute the (approximate) frames per second
        if len(self.timestamps) > 1:
            return (len(self.timestamps) - 1) / self.elapsed()
        return 0
