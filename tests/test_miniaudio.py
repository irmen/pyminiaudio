import miniaudio
from unittest import mock


def dummy_generator():
    while True:
        yield


def test_devices():
    devs = miniaudio.Devices()
    devs.get_playbacks()
    devs.get_captures()


def test_stop_callback_capture(backends):
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


def test_stop_callback_playback(backends):
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


def test_stop_callback_duplex(backends):
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
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_wav_stream():
    frames_to_read = 256
    stream = miniaudio.wav_stream_file("examples/samples/music.wav", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_flac_stream():
    frames_to_read = 256
    stream = miniaudio.flac_stream_file("examples/samples/music.flac", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_oggvorbis_stream():
    frames_to_read = 256
    stream = miniaudio.vorbis_stream_file("examples/samples/music.ogg", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
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


def test_version():
    ver = miniaudio.lib_version()
    assert len(ver) > 3
    assert '.' in ver


def test_is_backend_enabled():
    assert miniaudio.is_backend_enabled(miniaudio.Backend.NULL)
    assert not miniaudio.is_backend_enabled(miniaudio.Backend.AAUDIO)


def test_enabled_backends():
    enabled = miniaudio.get_enabled_backends()
    assert len(enabled) > 0
    assert miniaudio.Backend.NULL in enabled


def test_is_loopback_supported():
    assert not miniaudio.is_loopback_supported(miniaudio.Backend.NULL)
    assert not miniaudio.is_loopback_supported(miniaudio.Backend.JACK)


def test_stream_any_unknown(streamable_unknown_source):
    miniaudio.stream_any(streamable_unknown_source, miniaudio.FileFormat.UNKNOWN)


def test_stream_any_mp3(streamable_mp3_source):
    miniaudio.stream_any(streamable_mp3_source, miniaudio.FileFormat.MP3)


def test_stream_any_wav(streamable_wav_source):
    miniaudio.stream_any(streamable_wav_source, miniaudio.FileFormat.WAV)


def test_stream_any_flac(streamable_flac_source):
    miniaudio.stream_any(streamable_flac_source, miniaudio.FileFormat.FLAC)


def test_stream_any_vorbis(streamable_vorbis_source):
    miniaudio.stream_any(streamable_vorbis_source, miniaudio.FileFormat.VORBIS)
