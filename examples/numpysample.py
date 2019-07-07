"""
Shows the support for numpy arrays as pcm sample data.
"""

import os
import numpy
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


def memory_stream(npa: numpy.ndarray) -> miniaudio.PlaybackCallbackGeneratorType:
    required_frames = yield b""  # generator initialization
    frames = 0
    while frames < len(npa):
        print(".", end="", flush=True)
        frames_end = frames + required_frames
        required_frames = yield npa[frames:frames_end]
        frames = frames_end


device = miniaudio.PlaybackDevice()
decoded = miniaudio.decode_file(samples_path("music.wav"))

# convert the sample data into a numpy array with shape (numframes, numchannels):
npa = numpy.array(decoded.samples, dtype=numpy.int16).reshape((-1, decoded.nchannels))

stream = memory_stream(npa)
next(stream)  # start the generator
device.start(stream)
input("Audio file playing in the background. Enter to stop playback: ")
device.close()
