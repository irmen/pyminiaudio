"""
Convert samples in another format, in streaming fashion rather than all at once.
"""

import os
import array
import io
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


# for demonstration purposes, just use a fully decoded file as a simulated streaming data source
decoded = miniaudio.decode_file(samples_path("music.ogg"), dither=miniaudio.DitherMode.TRIANGLE)
print("source:", decoded)
src = io.BytesIO(decoded.samples.tobytes())


# streaming conversion to other sound format frames

def produce_data(src: io.BytesIO, nchannels: int, samplewidth: int) -> miniaudio.PlaybackCallbackGeneratorType:
    desired_frames = yield b""  # generator initialization
    while True:
        desired_bytes = desired_frames * nchannels * samplewidth
        data = src.read(desired_bytes)
        if not data:
            break
        print(".", end="", flush=True)
        desired_frames = yield data


producer = produce_data(src, decoded.nchannels, decoded.sample_width)
next(producer)    # start the generator

dsp = miniaudio.StreamingConverter(decoded.sample_format, decoded.nchannels, decoded.sample_rate,
                                   miniaudio.SampleFormat.UNSIGNED8, 1, 12000, producer,
                                   miniaudio.DitherMode.TRIANGLE)

print("Stream format conversion of source:")
framechunks = []
while True:
    framedata = dsp.convert(4000)
    if not framedata:
        break
    print("got chunk of size", len(framedata))
    framechunks.append(framedata)

print("\nGot", len(framechunks), "total frame chunks")

# convert the frames to bytes and write it to a file
samples = array.array('B')
for f in framechunks:
    samples.extend(f)
outputfile = miniaudio.DecodedSoundFile("converted", dsp.out_channels, dsp.out_samplerate, dsp.out_format, samples)
miniaudio.wav_write_file("converted.wav", outputfile)

print("\nConverted sound written to ./converted.wav")
output_info = miniaudio.get_file_info("converted.wav")
print(output_info)
