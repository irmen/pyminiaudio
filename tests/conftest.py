import pytest
import miniaudio


@pytest.fixture()
def backends():
    return [miniaudio.Backend.NULL]


class FileSource(miniaudio.StreamableSource):
    def __init__(self, filename: str) -> None:
        self.file = open(filename, "rb")

    def read(self, num_bytes: int) -> bytes:
        print("reading from stream:", num_bytes)
        return self.file.read(num_bytes)

    def seek(self, offset: int, origin: miniaudio.SeekOrigin) -> bool:
        whence = 0
        if origin == miniaudio.SeekOrigin.START:
            whence = 0
        elif origin == miniaudio.SeekOrigin.CURRENT:
            whence = 1
        self.file.seek(offset, whence)
        return True


@pytest.fixture()
def streamable_wav_source():
    return FileSource("examples/samples/music.wav")


@pytest.fixture()
def streamable_mp3_source():
    return FileSource("examples/samples/music.mp3")


@pytest.fixture()
def streamable_flac_source():
    return FileSource("examples/samples/music.flac")


@pytest.fixture()
def streamable_vorbis_source():
    return FileSource("examples/samples/music.ogg")


@pytest.fixture()
def streamable_unknown_source():
    return FileSource("examples/samples/music.mp3")

