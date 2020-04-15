"""
Simple audio streaming from a file using the basic blahblah_stream_file functions

NOTE: Don't actually use this in real code. It requires some awkward array streaming wrapper
code (see playback_stream). It is much easier and faster to use the stream_file function.
"""

import sys
import array
from typing import Generator
import miniaudio


def playback_stream(stream: Generator[array.array, None, None], num_channels: int) -> miniaudio.PlaybackCallbackGeneratorType:
    # awkward buffering and generator stream wrapping to make it suitable for async playback
    # note: stream_file() does this transparently for you and should be used instead in real code.
    buffer = array.array('h')
    num_frames = yield buffer
    chunksize = num_frames * num_channels
    while True:
        try:
            while len(buffer) < chunksize:
                buffer += next(stream)  # fill the buffer
        except StopIteration:
            break
        chunk = buffer[:chunksize]
        buffer = buffer[chunksize:]
        chunksize = (yield chunk) * num_channels


def stream_file(info, filename):
    if info.file_format == miniaudio.FileFormat.FLAC:
        fstream = miniaudio.flac_stream_file(filename)
    elif info.file_format == miniaudio.FileFormat.MP3:
        fstream = miniaudio.mp3_stream_file(filename)
    elif info.file_format == miniaudio.FileFormat.VORBIS:
        fstream = miniaudio.vorbis_stream_file(filename)
    elif info.file_format == miniaudio.FileFormat.WAV:
        fstream = miniaudio.wav_stream_file(filename)
    else:
        raise IOError("unsupported audio file format")

    stream = playback_stream(fstream, info.nchannels)
    next(stream)  # start the generator
    with miniaudio.PlaybackDevice(output_format=info.sample_format, sample_rate=info.sample_rate, nchannels=info.nchannels) as play:
        play.start(stream)
        input("Audio file playing in the background. Enter to stop playback: ")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("use one argument: filename")
    info = miniaudio.get_file_info(sys.argv[1])
    stream_file(info, sys.argv[1])
