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
