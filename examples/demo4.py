"""
Listing and Choosing the audio device to play on.
"""

import os
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


def choose_device():
    devices = miniaudio.Devices()
    print("Available playback devices:")
    playbacks = devices.get_playbacks()
    for d in enumerate(playbacks, 1):
        print("{num} = {name}".format(num=d[0], name=d[1]['name']))
    choice = int(input("play on which device? "))
    return playbacks[choice-1]


if __name__ == "__main__":
    selected_device = choose_device()
    stream = miniaudio.stream_file(samples_path("music.mp3"))
    with miniaudio.PlaybackDevice(device_id=selected_device["id"]) as device:
        device.start(stream)
        input("Audio file playing in the background. Enter to stop playback: ")
