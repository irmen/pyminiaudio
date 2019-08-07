import unittest
import miniaudio
from unittest import mock
from os import environ


backends = [miniaudio.Backend.JACK]

def dummy_generator():
    yield


class MiniaudioTests(unittest.TestCase):

    def test_devices(self):
        devs = miniaudio.Devices()
        devs.get_playbacks()
        devs.get_captures()

    def test_stop_callback_capture(self):
        stop_callback = mock.Mock()

        capture = miniaudio.CaptureDevice(backends=backends)
        gen = dummy_generator()
        next(gen)
        capture.start(gen, stop_callback)

        self.assertTrue(capture.running)
        # Force a stop.
        miniaudio.lib.ma_device_stop(capture._device)

        stop_callback.assert_called_once()
        self.assertFalse(capture.running)

    def test_stop_callback_playback(self):
        stop_callback = mock.Mock()

        playback = miniaudio.PlaybackDevice(backends=backends)
        gen = dummy_generator()
        next(gen)
        playback.start(gen, stop_callback)

        self.assertTrue(playback.running)
        # Force a stop.
        miniaudio.lib.ma_device_stop(playback._device)

        stop_callback.assert_called_once()
        self.assertFalse(playback.running)

    def test_stop_callback_duplex(self):
        stop_callback = mock.Mock()

        duplex = miniaudio.DuplexStream(backends=backends)
        gen = dummy_generator()
        next(gen)
        duplex.start(gen, stop_callback)

        self.assertTrue(duplex.running)
        # Force a stop.
        miniaudio.lib.ma_device_stop(duplex._device)

        stop_callback.assert_called_once()
        self.assertFalse(duplex.running)
