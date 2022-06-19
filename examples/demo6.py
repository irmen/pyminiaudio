"""
Example of playing raw pcm audio data in memory.
Starts by reading and decoding an audio file into memory fully. Then playing that.
"""

import os
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


sounddata = miniaudio.decode_file(samples_path("music.ogg"))
print("Got raw pcm in memory.")

stream = miniaudio.stream_raw_pcm_memory(sounddata.samples, sounddata.nchannels, sounddata.sample_width)

with miniaudio.PlaybackDevice(output_format=sounddata.sample_format,
                              nchannels=sounddata.nchannels,
                              sample_rate=sounddata.sample_rate) as device:
    device.start(stream)
    input("Playing in the background. Enter to stop: ")
