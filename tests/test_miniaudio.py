import pytest

import miniaudio
from unittest import mock


def dummy_generator():
    while True:
        yield


def test_devices():
    devs = miniaudio.Devices()
    devs.get_playbacks()
    devs.get_captures()


# The device stop callback doesn't work consistently,
# so for now I've decided to not provide this functionality any longer.
# Also see https://github.com/mackron/miniaudio/issues/341#issuecomment-879716338
#
# def test_stop_callback_capture(backends):
#     stop_callback = mock.Mock()
#
#     try:
#         capture = miniaudio.CaptureDevice(backends=backends, stop_callback=stop_callback)
#     except miniaudio.MiniaudioError as me:
#         if me.args[0] != "failed to init device":
#             raise
#         else:
#             print("SKIPPING CAPTURE DEVICE INIT ERROR", me)
#     else:
#         gen = dummy_generator()
#         next(gen)
#         capture.start(gen)
#
#         assert capture.running is True
#         # Simulate an unexpected stop.
#         miniaudio.lib.ma_device_stop(capture._device)
#
#         stop_callback.assert_called_once()
#         assert capture.running is False
#
#
# def test_stop_callback_playback(backends):
#     stop_callback = mock.Mock()
#
#     playback = miniaudio.PlaybackDevice(backends=backends, stop_callback=stop_callback)
#     gen = dummy_generator()
#     next(gen)
#     playback.start(gen)
#
#     assert playback.running is True
#     # Simulate an unexpected stop.
#     miniaudio.lib.ma_device_stop(playback._device)
#
#     stop_callback.assert_called_once()
#     assert playback.running is False
#
#
# def test_stop_callback_duplex(backends):
#     stop_callback = mock.Mock()
#
#     try:
#         duplex = miniaudio.DuplexStream(backends=backends, stop_callback=stop_callback)
#     except miniaudio.MiniaudioError as me:
#         if me.args[0] != "failed to init device":
#             raise
#         else:
#             print("SKIPPING DUPLEX DEVICE INIT ERROR", me)
#     else:
#         gen = dummy_generator()
#         next(gen)
#         duplex.start(gen)
#
#         assert duplex.running is True
#         # Simulate an unexpected stop.
#         miniaudio.lib.ma_device_stop(duplex._device)
#
#         stop_callback.assert_called_once()
#         assert duplex.running is False


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
                        errors.append(
                            AttributeError(
                                "calling undefined cffi function: lib.{}  at line {} col {} of {}".format(
                                    node.func.attr, lineno, column, cffi_module.__file__
                                )
                            )
                        )
                    else:
                        ftype = cffi_module.ffi.typeof(cffi_func)
                        if len(node.args) != len(ftype.args):
                            errors.append(
                                TypeError(
                                    "cffi function lib.{} expected {} args, called with {} args  at line {} col {} of {}".format(
                                        node.func.attr,
                                        len(ftype.args),
                                        len(node.args),
                                        lineno,
                                        column,
                                        cffi_module.__file__,
                                    )
                                )
                            )
    if errors:
        raise TypeError(errors)


def load_sample(name):
    with open("tests/audio/" + name, "rb") as f:
        return f.read()


def test_file_info():
    info = miniaudio.get_file_info("tests/audio/test.ogg")
    assert info.file_format == miniaudio.FileFormat.VORBIS
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_vorbis_info():
    data = load_sample("test.ogg")
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
    data = load_sample("test.flac")
    info = miniaudio.flac_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 0.9
    assert info.file_format == miniaudio.FileFormat.FLAC
    assert info.num_frames > 20000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_wav_info():
    data = load_sample("test.wav")
    info = miniaudio.wav_get_info(data)
    assert info.name == "<memory>"
    assert info.nchannels == 2
    assert info.sample_width == 2
    assert info.duration > 0.9
    assert info.file_format == miniaudio.FileFormat.WAV
    assert info.num_frames > 20000
    assert info.sample_rate == 22050
    assert info.sample_format == miniaudio.SampleFormat.SIGNED16


def test_mp3_info():
    data = load_sample("test.mp3")
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
    data = load_sample("test.mp3")
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
    stream = miniaudio.mp3_stream_file("tests/audio/test.mp3", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_wav_stream():
    frames_to_read = 256
    stream = miniaudio.wav_stream_file("tests/audio/test.wav", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_flac_stream():
    frames_to_read = 256
    stream = miniaudio.flac_stream_file("tests/audio/test.flac", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_oggvorbis_stream():
    frames_to_read = 256
    stream = miniaudio.vorbis_stream_file("tests/audio/test.ogg", frames_to_read)
    assert len(next(stream)) >= 512
    assert len(next(stream)) >= 512
    stream.close()


def test_flac_read():
    data = load_sample("test.flac")
    sound = miniaudio.flac_read_s32(data)
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32
    assert sound.sample_rate == 22050


def test_vorbis_read():
    data = load_sample("test.ogg")
    sound = miniaudio.vorbis_read(data)
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16
    assert sound.sample_rate == 22050


def test_wav_read():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_f32(data)
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32
    assert sound.sample_rate == 22050


def test_decode():
    data = load_sample("test.ogg")
    decoded = miniaudio.decode(
        data,
        miniaudio.SampleFormat.FLOAT32,
        sample_rate=32000,
        dither=miniaudio.DitherMode.TRIANGLE,
    )
    assert decoded.sample_format == miniaudio.SampleFormat.FLOAT32
    assert decoded.sample_rate == 32000
    assert decoded.num_frames > 200000


def test_version():
    ver = miniaudio.lib_version()
    assert len(ver) > 3
    assert "." in ver


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


def test_icecastclient_metadata_parsing():
    ic = miniaudio.IceCastClient
    meta = ic.parse_metadata("")
    assert meta == {}
    meta = ic.parse_metadata("bogus")
    assert meta == {"bogus": ""}
    meta = ic.parse_metadata("bogus=")
    assert meta == {"bogus": ""}
    meta = ic.parse_metadata("StreamTitle=title")
    assert meta == {"StreamTitle": "title"}
    meta = ic.parse_metadata("StreamTitle='title'")
    assert meta == {"StreamTitle": "title"}
    meta = ic.parse_metadata("StreamTitle='title';")
    assert meta == {"StreamTitle": "title"}
    meta = ic.parse_metadata("StreamTitle='title';StreamUrl='http://something.url'")
    assert meta == {"StreamTitle": "title", "StreamUrl": "http://something.url"}
    meta = ic.parse_metadata("StreamTitle='title';StreamUrl='http://something.url';")
    assert meta == {"StreamTitle": "title", "StreamUrl": "http://something.url"}
    meta = ic.parse_metadata(
        "StreamTitle='title'with'quotes';StreamUrl='http://something.url';"
    )
    assert meta == {
        "StreamTitle": "title'with'quotes",
        "StreamUrl": "http://something.url",
    }
    meta = ic.parse_metadata(
        "StreamTitle=TitlewithHTMLcodes&#39;and&#39;stuff;StreamUrl='http://something.url';"
    )
    assert meta == {
        "StreamTitle": "TitlewithHTMLcodes'and'stuff",
        "StreamUrl": "http://something.url",
    }


def test_flac_read_file_s16():
    sound = miniaudio.flac_read_file_s16("tests/audio/test.flac")
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_flac_read_file_s32():
    sound = miniaudio.flac_read_file_s32("tests/audio/test.flac")
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32


def test_mp3_read_file_s16():
    sound = miniaudio.mp3_read_file_s16("tests/audio/test.mp3")
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_wav_read_file_s16():
    sound = miniaudio.wav_read_file_s16("tests/audio/test.wav")
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_wav_read_file_s32():
    sound = miniaudio.wav_read_file_s32("tests/audio/test.wav")
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32


def test_flac_read_memory():
    data = load_sample("test.flac")
    sound = miniaudio.flac_read_f32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32


def test_mp3_read_memory():
    data = load_sample("test.mp3")
    sound = miniaudio.mp3_read_f32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32


def test_wav_read_memory():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_f32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32


def test_vorbis_read_memory():
    data = load_sample("test.ogg")
    sound = miniaudio.vorbis_read(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_convert_frames():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_f32(data)
    converted = miniaudio.convert_frames(
        miniaudio.SampleFormat.FLOAT32,
        sound.nchannels,
        sound.sample_rate,
        bytes(sound.samples),
        miniaudio.SampleFormat.SIGNED16,
        sound.nchannels,
        sound.sample_rate,
    )
    assert isinstance(converted, (bytes, bytearray))
    assert len(converted) == sound.num_frames * sound.nchannels * 2


def test_decode_file():
    sound = miniaudio.decode_file(
        "tests/audio/test.mp3", miniaudio.SampleFormat.FLOAT32
    )
    assert sound.nchannels == 2
    assert sound.sample_rate == 44100
    assert sound.num_frames > 400000
    assert sound.sample_format == miniaudio.SampleFormat.FLOAT32


def test_wav_write_file(tmp_path):
    sound = miniaudio.wav_read_file_f32("tests/audio/test.wav")
    output_file = tmp_path / "output.wav"
    miniaudio.wav_write_file(str(output_file), sound)
    assert output_file.exists()
    reloaded = miniaudio.wav_read_file_f32(str(output_file))
    assert reloaded.nchannels == sound.nchannels
    assert reloaded.sample_rate == sound.sample_rate
    assert reloaded.num_frames == sound.num_frames


def test_wav_read_memory_s16():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_s16(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_wav_read_memory_s32():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_s32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32


def test_mp3_read_memory_s16():
    data = load_sample("test.mp3")
    sound = miniaudio.mp3_read_s16(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 200000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_flac_read_memory_s16():
    data = load_sample("test.flac")
    sound = miniaudio.flac_read_s16(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED16


def test_flac_read_memory_s32():
    data = load_sample("test.flac")
    sound = miniaudio.flac_read_s32(data)
    assert sound.nchannels == 2
    assert sound.sample_rate == 22050
    assert sound.num_frames > 20000
    assert sound.sample_format == miniaudio.SampleFormat.SIGNED32


def test_wav_get_file_info():
    info = miniaudio.wav_get_file_info("tests/audio/test.wav")
    assert info.file_format == miniaudio.FileFormat.WAV
    assert info.sample_rate == 22050
    assert info.num_frames > 20000


def test_mp3_get_file_info():
    info = miniaudio.mp3_get_file_info("tests/audio/test.mp3")
    assert info.file_format == miniaudio.FileFormat.MP3
    assert info.sample_rate == 22050
    assert info.num_frames > 200000


def test_flac_get_file_info():
    info = miniaudio.flac_get_file_info("tests/audio/test.flac")
    assert info.file_format == miniaudio.FileFormat.FLAC
    assert info.sample_rate == 22050
    assert info.num_frames > 20000


def test_vorbis_get_file_info():
    info = miniaudio.vorbis_get_file_info("tests/audio/test.ogg")
    assert info.file_format == miniaudio.FileFormat.VORBIS
    assert info.sample_rate == 22050
    assert info.num_frames > 200000


def test_get_file_info():
    info = miniaudio.get_file_info("tests/audio/test.wav")
    assert info.file_format == miniaudio.FileFormat.WAV


def test_convert_sample_format():
    data = load_sample("test.wav")
    sound = miniaudio.wav_read_f32(data)
    converted = miniaudio.convert_sample_format(
        miniaudio.SampleFormat.FLOAT32,
        bytes(sound.samples),
        miniaudio.SampleFormat.SIGNED16,
        miniaudio.DitherMode.NONE,
    )
    assert isinstance(converted, (bytes, bytearray))
    assert len(converted) == sound.num_frames * sound.nchannels * 2


def test_wavfilereadstream(tmp_path):
    import array

    output_file = tmp_path / "output.wav"

    def sample_generator():
        for _ in range(1024):
            yield array.array("h", [0, 0])

    with open(str(output_file), "wb") as f:
        stream = miniaudio.WavFileReadStream(
            sample_generator(), 44100, 2, miniaudio.SampleFormat.SIGNED16
        )
        f.write(stream.read())
        stream.close()

    assert output_file.exists()
    info = miniaudio.wav_get_file_info(str(output_file))
    assert info.sample_rate == 44100
    assert info.nchannels == 2


def test_convert_frames_trims_padding_on_resampling():
    """
    Verify that convert_frames() correctly trims the output buffer
    to the actual number of frames written by ma_convert_frames.
    When downsampling 44100 -> 22050, ma_calculate_frame_count_after_resampling
    may overestimate - the returned buffer should be trimmed accordingly.
    """
    import math
    import array

    src_rate = 44100
    dst_rate = 22050
    nchannels = 2
    num_frames = 200

    samples = array.array("h", [0]) * (num_frames * nchannels)
    for i in range(num_frames):
        val = int(math.sin(2 * math.pi * 440 * i / src_rate) * 30000)
        for ch in range(nchannels):
            samples[i * nchannels + ch] = val

    converted = miniaudio.convert_frames(
        miniaudio.SampleFormat.SIGNED16,
        nchannels,
        src_rate,
        bytes(samples),
        miniaudio.SampleFormat.SIGNED16,
        nchannels,
        dst_rate,
    )

    to_width = miniaudio.width_from_format(miniaudio.SampleFormat.SIGNED16)
    allocated = miniaudio.lib.ma_calculate_frame_count_after_resampling(
        dst_rate, src_rate, num_frames
    )
    buffer = bytearray(allocated * to_width * nchannels)
    actual = miniaudio.lib.ma_convert_frames(
        miniaudio.ffi.from_buffer(buffer),
        allocated,
        miniaudio.SampleFormat.SIGNED16.value,
        nchannels,
        dst_rate,
        bytes(samples),
        num_frames,
        miniaudio.SampleFormat.SIGNED16.value,
        nchannels,
        src_rate,
    )

    expected_size = actual * to_width * nchannels
    assert len(converted) == expected_size, (
        f"convert_frames returned {len(converted)} bytes, "
        f"expected {expected_size} bytes (actual frames from ma_convert_frames). "
        f"Buffer was allocated for {allocated} frames, "
        f"but ma_convert_frames wrote only {actual} frames."
    )


def test_stream_raw_pcm_memory_memoryview_correct_size():
    import array

    nchannels = 2
    sample_width = 2  # 16-bit signed
    frames_to_read = 50
    total_frames = 200

    samples = array.array("h", [0]) * (total_frames * nchannels)
    for i in range(total_frames * nchannels):
        samples[i] = (i * 1000) & 0x7FFF

    pcmdata = memoryview(samples)
    gen = miniaudio.stream_raw_pcm_memory(
        pcmdata, nchannels, sample_width, frames_to_read
    )

    chunks = list(gen)
    for i, chunk in enumerate(chunks[:-1]):
        expected = frames_to_read * nchannels * sample_width
        assert len(chunk) == expected, (
            f"Chunk {i}: expected {expected} bytes, got {len(chunk)} bytes"
        )
    # Last chunk may be partial
    assert len(chunks) > 1
    assert sum(len(c) for c in chunks) == total_frames * nchannels * sample_width


def test_device_start_guard_running_state():
    device = miniaudio.PlaybackDevice(backends=[miniaudio.Backend.NULL])
    device.running = True
    device.callback_generator = None
    gen = dummy_generator()
    next(gen)
    with pytest.raises(miniaudio.MiniaudioError):
        device.start(gen)
    device.close()

def test_stop_callback_updates_state_without_user_callback():
    # Bug: AbstractDevice._stop_callback only updates state if self.stop_callback is set.
    device = miniaudio.PlaybackDevice(backends=[miniaudio.Backend.NULL])
    device.running = True
    device.callback_generator = mock_generator()
    
    # Manually trigger stop callback
    device._stop_callback(device._device)
    
    # These should be updated even if no user stop_callback was provided
    assert device.running is False, "device.running should be False after stop callback"
    assert device.callback_generator is None, "device.callback_generator should be None after stop callback"
    device.close()

def mock_generator():
    while True:
        yield b"\0" * 400

def test_duplex_stream_buffer_overflow_check():
    # Bug: DuplexStream doesn't check if the returned data exceeds the buffer size.
    device = miniaudio.DuplexStream(backends=[miniaudio.Backend.NULL])
    
    def naughty_generator():
        while True:
            # Return way too much data (more than what framecount*width*channels would be)
            yield b"\0" * 1000000 
    
    gen = naughty_generator()
    next(gen)  # start/prime the generator
    device.callback_generator = gen
    device.running = True
    
    # This should raise MiniaudioError instead of overflowing (via ffi.memmove)
    with pytest.raises(miniaudio.MiniaudioError, match="number of frames from callback exceeds maximum"):
        # We need a dummy framecount. The _data_callback uses framecount from miniaudio.
        framecount = 100
        dummy_input = bytes(device.capture_sample_width * device.capture_channels * framecount)
        device._data_callback(device._device, miniaudio.ffi.NULL, dummy_input, framecount)
    
    device.close()

def test_duplex_stream_mismatched_widths():
    # Bug: DuplexStream assumes capture and playback widths are same (stores only one self.sample_width)
    # capture is 16-bit (2 bytes), playback is 32-bit (4 bytes)
    device = miniaudio.DuplexStream(
        capture_format=miniaudio.SampleFormat.SIGNED16,
        playback_format=miniaudio.SampleFormat.SIGNED32,
        backends=[miniaudio.Backend.NULL]
    )
    
    assert device.sample_width == 2 # from capture
    # If playback uses 4 bytes, then a framecount of 100 needs 100 * 2 * 4 = 800 bytes for output
    # But if we use device.sample_width (2), we might think it only needs 400 bytes.
    
    # We should have separate widths for capture and playback.
    assert hasattr(device, "playback_sample_width"), "DuplexStream should have playback_sample_width"
    assert device.playback_sample_width == 4
    
    device.close()
