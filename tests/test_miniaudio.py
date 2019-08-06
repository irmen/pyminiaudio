import unittest
import miniaudio
from multiprocessing import Process
from threading import Thread
from unittest import  mock
from time import sleep


def dummy_generator():
    yield


class MiniaudioTests(unittest.TestCase):

    def test_devices(self):
        devs = miniaudio.Devices()
        devs.get_playbacks()
        devs.get_captures()

    def test_stop_callback_capture(self):
        stop_callback = mock.Mock()

        capture = miniaudio.CaptureDevice()
        gen = dummy_generator()
        next(gen)
        capture.start(gen, stop_callback)

        # Force a stop.
        miniaudio.lib.ma_device_stop(capture._device)

        stop_callback.assert_called_once()

    def test_stop_callback_playback(self):
        stop_callback = mock.Mock()

        capture = miniaudio.PlaybackDevice()
        gen = dummy_generator()
        next(gen)
        capture.start(gen, stop_callback)

        # Force a stop.
        miniaudio.lib.ma_device_stop(capture._device)

        stop_callback.assert_called_once()

    def test_stop_callback_duplex(self):
        stop_callback = mock.Mock()

        capture = miniaudio.DuplexStream()
        gen = dummy_generator()
        next(gen)
        capture.start(gen, stop_callback)

        # Force a stop.
        miniaudio.lib.ma_device_stop(capture._device)

        stop_callback.assert_called_once()