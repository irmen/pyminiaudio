import miniaudio
from unittest import mock
import sys
from os import environ
import pytest

# Skip tests on 3.5 travis for now, due to not enough locked memory being available on travis CI.
py35skip = pytest.mark.skipif(
    environ.get("TRAVIS") and sys.version_info[0] == 3 and sys.version_info[1] == 5,
    reason="Skipping python 3.5 on travis"
)


def dummy_generator():
    while True:
        yield


def test_devices():
    devs = miniaudio.Devices()
    devs.get_playbacks()
    devs.get_captures()


@py35skip
def test_stop_callback_capture(backends, jackd_server):
    stop_callback = mock.Mock()

    try:
        capture = miniaudio.CaptureDevice(backends=backends)
    except miniaudio.MiniaudioError as me:
        if me.args[0] != "failed to init device":
            raise
        else:
            print("SKIPPING CAPTURE DEVICE INIT ERROR", me)
    else:
        gen = dummy_generator()
        next(gen)
        capture.start(gen, stop_callback)

        assert capture.running is True
        # Simulate an unexpected stop.
        miniaudio.lib.ma_device_stop(capture._device)

        stop_callback.assert_called_once()
        assert capture.running is False


@py35skip
def test_stop_callback_playback(backends, jackd_server):
    stop_callback = mock.Mock()

    playback = miniaudio.PlaybackDevice(backends=backends)
    gen = dummy_generator()
    next(gen)
    playback.start(gen, stop_callback)

    assert playback.running is True
    # Simulate an unexpected stop.
    miniaudio.lib.ma_device_stop(playback._device)

    stop_callback.assert_called_once()
    assert playback.running is False


@py35skip
def test_stop_callback_duplex(backends, jackd_server):
    stop_callback = mock.Mock()

    try:
        duplex = miniaudio.DuplexStream(backends=backends)
    except miniaudio.MiniaudioError as me:
        if me.args[0] != "failed to init device":
            raise
        else:
            print("SKIPPING DUPLEX DEVICE INIT ERROR", me)
    else:
        gen = dummy_generator()
        next(gen)
        duplex.start(gen, stop_callback)

        assert duplex.running is True
        # Simulate an unexpected stop.
        miniaudio.lib.ma_device_stop(duplex._device)

        stop_callback.assert_called_once()
        assert duplex.running is False


def test_cffi_api_calls_parameters_correct():
    import ast
    import inspect
    cffi_module = miniaudio
    tree = ast.parse(inspect.getsource(cffi_module))
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == "lib":
                    lineno = node.func.value.lineno
                    column = node.func.value.col_offset
                    try:
                        cffi_func = getattr(cffi_module.lib, node.func.attr)
                    except AttributeError:
                        errors.append(AttributeError("calling undefined cffi function: lib.{}  at line {} col {} of {}"
                                                     .format(node.func.attr, lineno, column, cffi_module.__file__)))
                    else:
                        ftype = cffi_module.ffi.typeof(cffi_func)
                        if len(node.args) != len(ftype.args):
                            errors.append(TypeError("cffi function lib.{} expected {} args, called with {} args  at line {} col {} of {}"
                                            .format(node.func.attr, len(ftype.args), len(node.args), lineno, column, cffi_module.__file__)))
            elif isinstance(node.func.value, ast.Subscript):
                if node.func.value.value.func.value.value.id == "lib":
                    raise NotImplementedError("failed to check subscript Ast node")
    if errors:
        raise TypeError(errors)


def load_sample(name):
    with open("examples/samples/"+name, "rb") as f:
        return f.read()


def test_file_info():
    info = miniaudio.get_file_info("examples/samples/music.ogg")
    assert info.file_format == miniaudio.FileFormat.VORBIS
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_vorbis_info():
    data = load_sample("music.ogg")
    info = miniaudio.vorbis_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 10.0
    assert info.file_format == miniaudio.FileFormat.VORBIS
    assert info.num_frames > 200000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_flac_info():
    data = load_sample("music.flac")
    info = miniaudio.flac_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 10.0
    assert info.file_format == miniaudio.FileFormat.FLAC
    assert info.num_frames > 200000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_wav_info():
    data = load_sample("music.wav")
    info = miniaudio.wav_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 10.0
    assert info.file_format == miniaudio.FileFormat.WAV
    assert info.num_frames > 200000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_mp3_info():
    data = load_sample("music.mp3")
    info = miniaudio.mp3_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 10.0
    assert info.file_format == miniaudio.FileFormat.MP3
    assert info.num_frames > 200000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_mp3_read():
    data = load_sample("music.mp3")
    sound = miniaudio.mp3_read_f32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32
    sound = miniaudio.mp3_read_s16(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_mp3_stream():
    frames_to_read = 256
    stream = miniaudio.mp3_stream_file("examples/samples/music.mp3", frames_to_read)
    assert len(next(stream)) == 512
    assert len(next(stream)) == 512
    assert len(next(stream)) == 512
    assert len(next(stream)) == 512
    stream.close()


def test_flac_read():
    data = load_sample("music.flac")
    sound = miniaudio.flac_read_s32(data)
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32
    assert sound.sample_rate == 22050


def test_vorbis_read():
    data = load_sample("music.ogg")
    sound = miniaudio.vorbis_read(data)
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16
    assert sound.sample_rate == 22050


def test_wav_read():
    data = load_sample("music.wav")
    sound = miniaudio.wav_read_f32(data)
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32
    assert sound.sample_rate == 22050


def test_decode():
    data = load_sample("music.ogg")
    decoded = miniaudio.decode(data, miniaudio.SampleFormat.FLOAT32, sample_rate=32000, dither=miniaudio.DitherMode.TRIANGLE)
    assert decoded.sample_format == miniaudio.SampleFormat.FLOAT32
    assert decoded.sample_rate == 32000
    assert decoded.num_frames > 200000
