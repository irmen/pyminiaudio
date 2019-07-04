import os
import array
import miniaudio


def mod_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mods', filename)


modplayer = miniaudio.ModPlayer()
modplayer.set_config(44100)
modplayer.load(mod_path("cndmcrrp.mod"))
print("~~~~~~~", modplayer.name, "~~~~~~~")

num_frames = modplayer.sample_rate * 10
print("Rendering", num_frames, "sample frames of the mod...", modplayer.BUFFER_SIZE)
samples = array.array('h')
for _ in range(num_frames//modplayer.BUFFER_SIZE):
    modplayer.fill_buffer()
    samples.extend(modplayer.get_buffer())

modplayer.close()

miniaudio.wav_write_file("modsample.wav",
                         miniaudio.DecodedSoundFile("mod", 2 if modplayer.stereo else 1,
                                                    modplayer.sample_rate,
                                                    miniaudio.SampleFormat.SIGNED16,
                                                    samples))

print("converted module written to ./modsample.wav")
