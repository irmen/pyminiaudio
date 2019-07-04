import unittest
import miniaudio


class MiniaudioTests(unittest.TestCase):

    def test_devices(self):
        devs = miniaudio.Devices()
        devs.get_playbacks()
        devs.get_captures()
