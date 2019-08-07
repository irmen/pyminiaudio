import unittest
import miniaudio
from unittest import mock
from os import environ
import pytest
import subprocess
from time import sleep
import pytest
import shlex


JACK_SERVER_NAME = 'test'


@pytest.fixture()
def backends():
    if environ.get("TRAVIS"):
        environ['JACK_DEFAULT_SERVER'] = JACK_SERVER_NAME
        environ['JACK_NO_START_SERVER'] = '1'
        backends = [miniaudio.Backend.JACK]
        return backends
    else:
        return []

@pytest.fixture()
def jackd_server():
    if environ.get("TRAVIS"):
        cmdstr = f'jackd -n{JACK_SERVER_NAME} -ddummy -r48000 -p1024'
        proc = subprocess.Popen(shlex.split(cmdstr))
        sleep(1)
        yield
        proc.kill()
    else:
        yield