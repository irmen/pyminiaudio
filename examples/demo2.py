"""
Example of decoding a stream of input data.
(in this case, just reading from an audio file)
"""

import os
import miniaudio
from miniaudio import SeekOrigin


class FileSource(miniaudio.StreamableSource):
    def __init__(self, filename: str) -> None:
        filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'samples', filename)
        self.file = open(filename, "rb")

    def read(self, num_bytes: int) -> bytes:
        print("reading from stream:", num_bytes)
        return self.file.read(num_bytes)

    def seek(self, offset: int, origin: SeekOrigin) -> bool:
        # note: seek support is usually not needed if you provide the file format to the decoder upfront
        # this is necessary if dealing with a network stream for instance
        whence = 0
        if origin == SeekOrigin.START:
            whence = 0
        elif origin == SeekOrigin.CURRENT:
            whence = 1
        self.file.seek(offset, whence)
        return True


print("Audio file playing in the background. Press enter to stop playback. ")
source = FileSource("music.ogg")
stream = miniaudio.stream_any(source)
device = miniaudio.PlaybackDevice()
device.start(stream)

input()
device.close()
