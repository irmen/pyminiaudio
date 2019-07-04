import os
import miniaudio


def mod_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mods', filename)


def stream_pcm(modplayer: miniaudio.ModPlayer):
    required_frames = yield b""  # generator initialization
    while True:
        modplayer.fill_buffer(required_frames)
        required_frames = yield modplayer.get_buffer(required_frames)


modplayer = miniaudio.ModPlayer()
modplayer.load(mod_path("cndmcrrp.mod"))
print("~~~~~~~", modplayer.name, "~~~~~~~")
for i in modplayer.instruments:
    print(repr(i))

device = miniaudio.PlaybackDevice(sample_rate=modplayer.sample_rate)
stream = stream_pcm(modplayer)
next(stream)  # start the generator
device.start(stream)
input("Tracker is playing in the background. Enter to stop playback: ")
modplayer.close()
device.close()
