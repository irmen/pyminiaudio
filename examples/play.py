"""
This example loads an audio file (in a format supported by miniaudio),
prints some information about it, and plays it without any sample rate/format conversion
in the application, if possible.  (conversion may still occur in the backend audio api)
"""

import sys
import miniaudio


def show_info(info):
    print("file:", info.name)
    print("format: {}, {} channels, {} khz, {:.1f} seconds".format(
        info.file_format, info.nchannels, info.sample_rate, info.duration))
    print("{} bytes per sample: {}".format(info.sample_width, info.sample_format_name))


def stream_file(info, filename):
    def progress_stream_wrapper(stream) -> miniaudio.PlaybackCallbackGeneratorType:
        framecount = yield(b"")
        try:
            while True:
                framecount = yield stream.send(framecount)
                print(".", end="", flush=True)
        except StopIteration:
            return

    output_format = info.sample_format
    try:
        filestream = miniaudio.stream_file(filename, output_format=output_format, sample_rate=info.sample_rate)
    except miniaudio.MiniaudioError as x:
        print("Cannot create optimal stream:", x)
        print("Creating stream with different sample format!")
        output_format = miniaudio.SampleFormat.SIGNED16
        filestream = miniaudio.stream_file(filename, output_format=output_format, sample_rate=info.sample_rate,
                                           dither=miniaudio.DitherMode.TRIANGLE)

    stream = progress_stream_wrapper(filestream)
    next(stream)   # start the generator
    device = miniaudio.PlaybackDevice(output_format=output_format, sample_rate=info.sample_rate)
    print("playback device backend:", device.backend, device.format.name, device.sample_rate, "hz")
    device.start(stream)
    input("Audio file playing in the background. Enter to stop playback: ")
    device.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("use one argument: filename")
    info = miniaudio.get_file_info(sys.argv[1])
    show_info(info)
    stream_file(info, sys.argv[1])
