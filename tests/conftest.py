import pytest
import miniaudio


@pytest.fixture()
def backends():
    return [miniaudio.Backend.NULL]
