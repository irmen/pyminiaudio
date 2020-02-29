"""
Simplest example of decoding and playing an audio file
"""

import os
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


stream = miniaudio.stream_file(samples_path("music.mp3"), dither=miniaudio.DitherMode.TRIANGLE)
with miniaudio.PlaybackDevice() as device:
    device.start(stream)
    input("Audio file playing in the background. Enter to stop playback: ")
