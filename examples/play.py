"""
This example loads an audio file (in a format supported by miniaudio),
prints some information about it, and plays it without any sample rate/format conversion if possible.

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

    stream = progress_stream_wrapper(miniaudio.stream_file(
        filename, output_format=info.sample_format, sample_rate=info.sample_rate))
    next(stream)   # start the generator
    device = miniaudio.PlaybackDevice(output_format=info.sample_format, sample_rate=info.sample_rate)
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
