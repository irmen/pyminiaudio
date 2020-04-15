"""
Convert audio data samples to another format.
"""

import os
import array
import miniaudio


def samples_path(filename):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)


info = miniaudio.get_file_info(samples_path("music.ogg"))
source_stream = miniaudio.vorbis_stream_file(samples_path("music.ogg"))

converter = miniaudio.DataConverter(info.sample_format, info.nchannels, info.sample_rate,
                                    miniaudio.SampleFormat.UNSIGNED8, 1, 11025, miniaudio.DitherMode.NONE)

print("Chunkwise format conversion of source...")
# for simplicity of storing the output, just append every converted output chunk
converted = array.array('B')
for frames in source_stream:
    result = converter.convert(frames)
    converted.extend(result)

outputfile = miniaudio.DecodedSoundFile("converted.wav", converter.out_channels, converter.out_samplerate, converter.out_format, converted)
miniaudio.wav_write_file("converted.wav", outputfile)
print("\nConverted sound written to ./converted.wav")
output_info = miniaudio.get_file_info("converted.wav")
print(output_info)
