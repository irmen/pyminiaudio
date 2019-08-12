import subprocess
import shlex
import pytest
import miniaudio

from os import environ
from time import sleep


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


@pytest.fixture(scope="session")
def jackd_server():
    if environ.get("TRAVIS"):
        cmdstr = 'jackd -n{} -r -m -ddummy -r48000 -p1024'.format(JACK_SERVER_NAME)
        proc = subprocess.Popen(shlex.split(cmdstr))
        sleep(1)
        yield
        proc.kill()
    else:
        yield
