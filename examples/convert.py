import os
import array
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


src = miniaudio.decode_file(samples_path("music.ogg"))
print("Source: {src.nchannels} ch, {src.sample_rate} hz, {src.sample_format_name}, {src.num_frames} frames"
      .format(src=src))

result = miniaudio.DecodedSoundFile("result", 2, 12000, 1, miniaudio.SampleFormat.UNSIGNED8, array.array('b'))
converted_frames = miniaudio.convert_frames(src.sample_format, src.nchannels, src.sample_rate, src.samples.tobytes(),
                                            result.sample_format, result.nchannels, result.sample_rate)

result.num_frames = int(len(converted_frames) / result.nchannels / result.sample_width)
result.samples.frombytes(converted_frames)


miniaudio.wav_write_file("converted.wav", result)
print("Converted sound written to ./converted.wav")
