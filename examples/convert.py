"""
Convert an audio file to WAV and different sample formats.
"""

import os
import array
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


src = miniaudio.decode_file(samples_path("music.ogg"), dither=miniaudio.DitherMode.TRIANGLE)
print("Source: ", src)

result = miniaudio.DecodedSoundFile("result", 1, 11025, miniaudio.SampleFormat.UNSIGNED8, array.array('b'))
converted_frames = miniaudio.convert_frames(src.sample_format, src.nchannels, src.sample_rate, src.samples.tobytes(),
                                            result.sample_format, result.nchannels, result.sample_rate)
# note: currently it is not possible to provide a dithermode to convert_frames()

result.num_frames = int(len(converted_frames) / result.nchannels / result.sample_width)
result.samples.frombytes(converted_frames)


miniaudio.wav_write_file("converted.wav", result)
print("Converted sound written to ./converted.wav")

output_info = miniaudio.get_file_info("converted.wav")
print(output_info)
