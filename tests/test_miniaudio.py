import miniaudio
from unittest import mock


def dummy_generator():
    yield


def test_devices():
    devs = miniaudio.Devices()
    devs.get_playbacks()
    devs.get_captures()

def test_stop_callback_capture(backends, jackd_server):
    stop_callback = mock.Mock()

    capture = miniaudio.CaptureDevice(backends=backends)
    gen = dummy_generator()
    next(gen)
    capture.start(gen, stop_callback)

    assert capture.running is True
    # Force a stop.
    miniaudio.lib.ma_device_stop(capture._device)

    stop_callback.assert_called_once()
    assert capture.running is False

def test_stop_callback_playback(backends, jackd_server):
    stop_callback = mock.Mock()

    playback = miniaudio.PlaybackDevice(backends=backends)
    gen = dummy_generator()
    next(gen)
    playback.start(gen, stop_callback)

    assert playback.running is True
    # Force a stop.
    miniaudio.lib.ma_device_stop(playback._device)

    stop_callback.assert_called_once()
    assert playback.running is False

def test_stop_callback_duplex(backends, jackd_server):
    stop_callback = mock.Mock()

    duplex = miniaudio.DuplexStream(backends=backends)
    gen = dummy_generator()
    next(gen)
    duplex.start(gen, stop_callback)

    assert duplex.running is True
    # Force a stop.
    miniaudio.lib.ma_device_stop(duplex._device)

    stop_callback.assert_called_once()
    assert duplex.running is False
