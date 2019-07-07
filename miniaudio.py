"""
Python interface to the miniaudio library (https://github.com/dr-soft/miniaudio)

Author: Irmen de Jong (irmen@razorvine.net)
Software license: "MIT software license". See http://opensource.org/licenses/MIT
"""

__version__ = "1.6"


import abc
import sys
import os
import io
import array
import struct
import inspect
from enum import Enum
from typing import Generator, List, Dict, Optional, Union, Any, Callable
from _miniaudio import ffi, lib
try:
    import numpy
except ImportError:
    numpy = None

lib.init_miniaudio()


class FileFormat(Enum):
    """Audio file format"""
    UNKNOWN = 0
    WAV = 1
    FLAC = 2
    VORBIS = 3
    MP3 = 4


class SampleFormat(Enum):
    """Sample format in memory"""
    UNKNOWN = lib.ma_format_unknown
    UNSIGNED8 = lib.ma_format_u8
    SIGNED16 = lib.ma_format_s16
    SIGNED24 = lib.ma_format_s24
    SIGNED32 = lib.ma_format_s32
    FLOAT32 = lib.ma_format_f32


class DeviceType(Enum):
    """Type of audio device"""
    PLAYBACK = lib.ma_device_type_playback
    CAPTURE = lib.ma_device_type_capture
    DUPLEX = lib.ma_device_type_duplex


class DitherMode(Enum):
    """How to dither when converting"""
    NONE = lib.ma_dither_mode_none
    RECTANGLE = lib.ma_dither_mode_rectangle
    TRIANGLE = lib.ma_dither_mode_triangle


class ChannelMixMode(Enum):
    """How to mix channels when converting"""
    RECTANGULAR = lib.ma_channel_mix_mode_rectangular
    SIMPLE = lib.ma_channel_mix_mode_simple
    CUSTOMWEIGHTS = lib.ma_channel_mix_mode_custom_weights
    PLANARBLEND = lib.ma_channel_mix_mode_planar_blend
    DEFAULT = lib.ma_channel_mix_mode_default


class Backend(Enum):
    """Operating system audio backend to use (only a subset will be available)"""
    WASAPI = lib.ma_backend_wasapi
    DSOUND = lib.ma_backend_dsound
    WINMM = lib.ma_backend_winmm
    COREAUDIO = lib.ma_backend_coreaudio
    SNDIO = lib.ma_backend_sndio
    AUDIO4 = lib.ma_backend_audio4
    OSS = lib.ma_backend_oss
    PULSEAUDIO = lib.ma_backend_pulseaudio
    ALSA = lib.ma_backend_alsa
    JACK = lib.ma_backend_jack
    AAUDIO = lib.ma_backend_aaudio
    OPENSL = lib.ma_backend_opensl
    WEBAUDIO = lib.ma_backend_webaudio
    NULL = lib.ma_backend_null


class ThreadPriority(Enum):
    """The priority of the worker thread (default=HIGHEST)"""
    IDLE = lib.ma_thread_priority_idle
    LOWEST = lib.ma_thread_priority_lowest
    LOW = lib.ma_thread_priority_low
    NORMAL = lib.ma_thread_priority_normal
    HIGH = lib.ma_thread_priority_high
    HIGHEST = lib.ma_thread_priority_highest
    REALTIME = lib.ma_thread_priority_realtime
    DEFAULT = lib.ma_thread_priority_default


class SeekOrigin(Enum):
    """How to seek() in a source"""
    START = lib.ma_seek_origin_start
    CURRENT = lib.ma_seek_origin_current


PlaybackCallbackGeneratorType = Generator[Union[bytes, array.array], int, None]
CaptureCallbackGeneratorType = Generator[None, Union[bytes, array.array], None]
DuplexCallbackGeneratorType = Generator[Union[bytes, array.array], Union[bytes, array.array], None]
GeneratorTypes = Union[PlaybackCallbackGeneratorType, CaptureCallbackGeneratorType, DuplexCallbackGeneratorType]


class SoundFileInfo:
    """Contains various properties of an audio file."""
    def __init__(self, name: str, file_format: FileFormat, nchannels: int, sample_rate: int,
                 sample_format: SampleFormat, duration: float, num_frames: int) -> None:
        self.name = name
        self.nchannels = nchannels
        self.sample_rate = sample_rate
        self.sample_format = sample_format
        self.sample_format_name = ffi.string(lib.ma_get_format_name(sample_format.value)).decode()
        self.sample_width = _width_from_format(sample_format)
        self.num_frames = num_frames
        self.duration = duration
        self.file_format = file_format

    def __str__(self) -> str:
        return "<{clazz}: '{name}' {nchannels} ch, {sample_rate} hz, {sample_format.name}, " \
               "{num_frames} frames={duration:.2f} sec.>".format(clazz=self.__class__.__name__, **(vars(self)))

    def __repr__(self) -> str:
        return str(self)


class DecodedSoundFile(SoundFileInfo):
    """Contains various properties and also the PCM frames of a fully decoded audio file."""
    def __init__(self, name: str, nchannels: int, sample_rate: int,
                 sample_format: SampleFormat, samples: array.array) -> None:
        num_frames = len(samples) // nchannels
        duration = num_frames / sample_rate
        super().__init__(name, FileFormat.UNKNOWN, nchannels, sample_rate, sample_format, duration, num_frames)
        self.samples = samples


class MiniaudioError(Exception):
    """When a miniaudio specific error occurs."""
    pass


class DecodeError(MiniaudioError):
    """When something went wrong during decoding an audio file."""
    pass


def get_file_info(filename: str) -> SoundFileInfo:
    """Fetch some information about the audio file."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".ogg", ".vorbis"):
        return vorbis_get_file_info(filename)
    elif ext == ".mp3":
        return mp3_get_file_info(filename)
    elif ext == ".flac":
        return flac_get_file_info(filename)
    elif ext == ".wav":
        return wav_get_file_info(filename)
    raise DecodeError("unsupported file format")


def read_file(filename: str, convert_to_16bit: bool = False) -> DecodedSoundFile:
    """Reads and decodes the whole audio file.
    Miniaudio will attempt to return the sound data in exactly the same format as in the file.
    Unless you set convert_convert_to_16bit to True, then the result is always a 16 bit sample format.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext in (".ogg", ".vorbis"):
        if convert_to_16bit:
            return vorbis_read_file(filename)
        else:
            vorbis = vorbis_get_file_info(filename)
            if vorbis.sample_format == SampleFormat.SIGNED16:
                return vorbis_read_file(filename)
            else:
                raise MiniaudioError("file has sample format that must be converted")
    elif ext == ".mp3":
        if convert_to_16bit:
            return mp3_read_file_s16(filename)
        else:
            mp3 = mp3_get_file_info(filename)
            if mp3.sample_format == SampleFormat.SIGNED16:
                return mp3_read_file_s16(filename)
            elif mp3.sample_format == SampleFormat.FLOAT32:
                return mp3_read_file_f32(filename)
            else:
                raise MiniaudioError("file has sample format that must be converted")
    elif ext == ".flac":
        if convert_to_16bit:
            return flac_read_file_s16(filename)
        else:
            flac = flac_get_file_info(filename)
            if flac.sample_format == SampleFormat.SIGNED16:
                return flac_read_file_s16(filename)
            elif flac.sample_format == SampleFormat.SIGNED32:
                return flac_read_file_s32(filename)
            elif flac.sample_format == SampleFormat.FLOAT32:
                return flac_read_file_f32(filename)
            else:
                raise MiniaudioError("file has sample format that must be converted")
    elif ext == ".wav":
        if convert_to_16bit:
            return wav_read_file_s16(filename)
        else:
            wav = wav_get_file_info(filename)
            if wav.sample_format == SampleFormat.SIGNED16:
                return wav_read_file_s16(filename)
            elif wav.sample_format == SampleFormat.SIGNED32:
                return wav_read_file_s32(filename)
            elif wav.sample_format == SampleFormat.FLOAT32:
                return wav_read_file_f32(filename)
            else:
                raise MiniaudioError("file has sample format that must be converted")
    raise DecodeError("unsupported file format")


def vorbis_get_file_info(filename: str) -> SoundFileInfo:
    """Fetch some information about the audio file (vorbis format)."""
    filenamebytes = _get_filename_bytes(filename)
    error = ffi.new("int *")
    vorbis = lib.stb_vorbis_open_filename(filenamebytes, error, ffi.NULL)
    if not vorbis:
        raise DecodeError("could not open/decode file")
    try:
        info = lib.stb_vorbis_get_info(vorbis)
        duration = lib.stb_vorbis_stream_length_in_seconds(vorbis)
        num_frames = lib.stb_vorbis_stream_length_in_samples(vorbis)
        return SoundFileInfo(filename, FileFormat.VORBIS, info.channels, info.sample_rate,
                             SampleFormat.SIGNED16, duration, num_frames)
    finally:
        lib.stb_vorbis_close(vorbis)


def vorbis_get_info(data: bytes) -> SoundFileInfo:
    """Fetch some information about the audio data (vorbis format)."""
    error = ffi.new("int *")
    vorbis = lib.stb_vorbis_open_memory(data, len(data), error, ffi.NULL)
    if not vorbis:
        raise DecodeError("could not open/decode data")
    try:
        info = lib.stb_vorbis_get_info(vorbis)
        duration = lib.stb_vorbis_stream_length_in_seconds(vorbis)
        num_frames = lib.stb_vorbis_stream_length_in_samples(vorbis)
        return SoundFileInfo("<memory>", FileFormat.VORBIS, info.channels, info.sample_rate,
                             SampleFormat.SIGNED16, duration, num_frames)
    finally:
        lib.stb_vorbis_close(vorbis)


def vorbis_read_file(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole vorbis audio file. Resulting sample format is 16 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("int *")
    sample_rate = ffi.new("int *")
    output = ffi.new("short **")
    num_frames = lib.stb_vorbis_decode_filename(filenamebytes, channels, sample_rate, output)
    if num_frames <= 0:
        raise DecodeError("cannot load/decode file")
    try:
        buffer = ffi.buffer(output[0], num_frames * channels[0] * 2)
        samples = _create_int_array(2)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.free(output[0])


def vorbis_read(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole vorbis audio data. Resulting sample format is 16 bits signed integer."""
    channels = ffi.new("int *")
    sample_rate = ffi.new("int *")
    output = ffi.new("short **")
    num_samples = lib.stb_vorbis_decode_memory(data, len(data), channels, sample_rate, output)
    if num_samples <= 0:
        raise DecodeError("cannot load/decode data")
    try:
        buffer = ffi.buffer(output[0], num_samples * channels[0] * 2)
        samples = _create_int_array(2)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.free(output[0])


def vorbis_stream_file(filename: str) -> Generator[array.array, None, None]:
    """Streams the ogg vorbis audio file as interleaved 16 bit signed integer sample arrays segments."""
    filenamebytes = _get_filename_bytes(filename)
    error = ffi.new("int *")
    vorbis = lib.stb_vorbis_open_filename(filenamebytes, error, ffi.NULL)
    if not vorbis:
        raise DecodeError("could not open/decode file")
    try:
        info = lib.stb_vorbis_get_info(vorbis)
        decode_buffer1 = ffi.new("short[]", 4096 * info.channels)
        decodebuf_ptr1 = ffi.cast("short *", decode_buffer1)
        decode_buffer2 = ffi.new("short[]", 4096 * info.channels)
        decodebuf_ptr2 = ffi.cast("short *", decode_buffer2)
        # note: we decode several frames to reduce the overhead of very small sample sizes a little
        while True:
            num_samples1 = lib.stb_vorbis_get_frame_short_interleaved(vorbis, info.channels, decodebuf_ptr1,
                                                                      4096 * info.channels)
            num_samples2 = lib.stb_vorbis_get_frame_short_interleaved(vorbis, info.channels, decodebuf_ptr2,
                                                                      4096 * info.channels)
            if num_samples1 + num_samples2 <= 0:
                break
            buffer = ffi.buffer(decode_buffer1, num_samples1 * 2 * info.channels)
            samples = _create_int_array(2)
            samples.frombytes(buffer)
            if num_samples2 > 0:
                buffer = ffi.buffer(decode_buffer2, num_samples2 * 2 * info.channels)
                samples.frombytes(buffer)
            yield samples
    finally:
        lib.stb_vorbis_close(vorbis)


def flac_get_file_info(filename: str) -> SoundFileInfo:
    """Fetch some information about the audio file (flac format)."""
    filenamebytes = _get_filename_bytes(filename)
    flac = lib.drflac_open_file(filenamebytes)
    if not flac:
        raise DecodeError("could not open/decode file")
    try:
        duration = flac.totalPCMFrameCount / flac.sampleRate
        sample_width = flac.bitsPerSample // 8
        return SoundFileInfo(filename, FileFormat.FLAC, flac.channels, flac.sampleRate,
                             _format_from_width(sample_width), duration, flac.totalPCMFrameCount)
    finally:
        lib.drflac_close(flac)


def flac_get_info(data: bytes) -> SoundFileInfo:
    """Fetch some information about the audio data (flac format)."""
    flac = lib.drflac_open_memory(data, len(data))
    if not flac:
        raise DecodeError("could not open/decode data")
    try:
        duration = flac.totalPCMFrameCount / flac.sampleRate
        sample_width = flac.bitsPerSample // 8
        return SoundFileInfo("<memory>", FileFormat.FLAC, flac.channels, flac.sampleRate,
                             _format_from_width(sample_width), duration, flac.totalPCMFrameCount)
    finally:
        lib.drflac_close(flac)


def flac_read_file_s32(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio file. Resulting sample format is 32 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_file_and_read_pcm_frames_s32(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = _create_int_array(4)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.SIGNED32, samples)
    finally:
        lib.drflac_free(memory)


def flac_read_file_s16(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio file. Resulting sample format is 16 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_file_and_read_pcm_frames_s16(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.drflac_free(memory)


def flac_read_file_f32(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio file. Resulting sample format is 32 bits float."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_file_and_read_pcm_frames_f32(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.FLOAT32, samples)
    finally:
        lib.drflac_free(memory)


def flac_read_s32(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio data. Resulting sample format is 32 bits signed integer."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_memory_and_read_pcm_frames_s32(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = _create_int_array(4)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.SIGNED32, samples)
    finally:
        lib.drflac_free(memory)


def flac_read_s16(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio data. Resulting sample format is 16 bits signed integer."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_memory_and_read_pcm_frames_s16(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.drflac_free(memory)


def flac_read_f32(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole flac audio file. Resulting sample format is 32 bits float."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drflac_uint64 *")
    memory = lib.drflac_open_memory_and_read_pcm_frames_f32(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.FLOAT32, samples)
    finally:
        lib.drflac_free(memory)


def flac_stream_file(filename: str, frames_to_read: int = 1024) -> Generator[array.array, None, None]:
    """Streams the flac audio file as interleaved 16 bit signed integer sample arrays segments."""
    filenamebytes = _get_filename_bytes(filename)
    flac = lib.drflac_open_file(filenamebytes)
    if not flac:
        raise DecodeError("could not open/decode file")
    try:
        decodebuffer = ffi.new("drflac_int16[]", frames_to_read * flac.channels)
        buf_ptr = ffi.cast("drflac_int16 *", decodebuffer)
        while True:
            num_samples = lib.drflac_read_pcm_frames_s16(flac, frames_to_read, buf_ptr)
            if num_samples <= 0:
                break
            buffer = ffi.buffer(decodebuffer, num_samples * 2 * flac.channels)
            samples = _create_int_array(2)
            samples.frombytes(buffer)
            yield samples
    finally:
        lib.drflac_close(flac)


def mp3_get_file_info(filename: str) -> SoundFileInfo:
    """Fetch some information about the audio file (mp3 format)."""
    filenamebytes = _get_filename_bytes(filename)
    config = ffi.new("drmp3_config *")
    config.outputChannels = 0
    config.outputSampleRate = 0
    mp3 = ffi.new("drmp3 *")
    if not lib.drmp3_init_file(mp3, filenamebytes, config):
        raise DecodeError("could not open/decode file")
    try:
        num_frames = lib.drmp3_get_pcm_frame_count(mp3)
        duration = num_frames / mp3.sampleRate
        return SoundFileInfo(filename, FileFormat.MP3, mp3.channels, mp3.sampleRate,
                             SampleFormat.SIGNED16, duration, num_frames)
    finally:
        lib.drmp3_uninit(mp3)


def mp3_get_info(data: bytes) -> SoundFileInfo:
    """Fetch some information about the audio data (mp3 format)."""
    config = ffi.new("drmp3_config *")
    config.outputChannels = 0
    config.outputSampleRate = 0
    mp3 = ffi.new("drmp3 *")
    if not lib.drmp3_init_memory(mp3, data, len(data), config):
        raise DecodeError("could not open/decode data")
    try:
        num_frames = lib.drmp3_get_pcm_frame_count(mp3)
        duration = num_frames / mp3.sampleRate
        return SoundFileInfo("<memory>", FileFormat.MP3, mp3.channels, mp3.sampleRate,
                             SampleFormat.SIGNED16, duration, num_frames)
    finally:
        lib.drmp3_uninit(mp3)


def mp3_read_file_f32(filename: str, want_nchannels: int = 0, want_sample_rate: int = 0) -> DecodedSoundFile:
    """Reads and decodes the whole mp3 audio file. Resulting sample format is 32 bits float."""
    filenamebytes = _get_filename_bytes(filename)
    config = ffi.new("drmp3_config *")
    config.outputChannels = want_nchannels
    config.outputSampleRate = want_sample_rate
    num_frames = ffi.new("drmp3_uint64 *")
    memory = lib.drmp3_open_file_and_read_f32(filenamebytes, config, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * config.outputChannels * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, config.outputChannels, config.outputSampleRate,
                                SampleFormat.FLOAT32, samples)
    finally:
        lib.drmp3_free(memory)


def mp3_read_file_s16(filename: str, want_nchannels: int = 0, want_sample_rate: int = 0) -> DecodedSoundFile:
    """Reads and decodes the whole mp3 audio file. Resulting sample format is 16 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    config = ffi.new("drmp3_config *")
    config.outputChannels = want_nchannels
    config.outputSampleRate = want_sample_rate
    num_frames = ffi.new("drmp3_uint64 *")
    memory = lib.drmp3_open_file_and_read_s16(filenamebytes, config, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * config.outputChannels * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, config.outputChannels, config.outputSampleRate,
                                SampleFormat.SIGNED16, samples)
    finally:
        lib.drmp3_free(memory)


def mp3_read_f32(data: bytes, want_nchannels: int = 0, want_sample_rate: int = 0) -> DecodedSoundFile:
    """Reads and decodes the whole mp3 audio data. Resulting sample format is 32 bits float."""
    config = ffi.new("drmp3_config *")
    config.outputChannels = want_nchannels
    config.outputSampleRate = want_sample_rate
    num_frames = ffi.new("drmp3_uint64 *")
    memory = lib.drmp3_open_memory_and_read_f32(data, len(data), config, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * config.outputChannels * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", config.outputChannels, config.outputSampleRate,
                                SampleFormat.FLOAT32, samples)
    finally:
        lib.drmp3_free(memory)


def mp3_read_s16(data: bytes, want_nchannels: int = 0, want_sample_rate: int = 0) -> DecodedSoundFile:
    """Reads and decodes the whole mp3 audio data. Resulting sample format is 16 bits signed integer."""
    config = ffi.new("drmp3_config *")
    config.outputChannels = want_nchannels
    config.outputSampleRate = want_sample_rate
    num_frames = ffi.new("drmp3_uint64 *")
    memory = lib.drmp3_open_memory_and_read_s16(data, len(data), config, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * config.outputChannels * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", config.outputChannels, config.outputSampleRate,
                                SampleFormat.SIGNED16, samples)
    finally:
        lib.drmp3_free(memory)


def mp3_stream_file(filename: str, frames_to_read: int = 1024,
                    want_nchannels: int = 0, want_sample_rate: int = 0) -> Generator[array.array, None, None]:
    """Streams the mp3 audio file as interleaved 16 bit signed integer sample arrays segments."""
    filenamebytes = _get_filename_bytes(filename)
    config = ffi.new("drmp3_config *")
    config.outputChannels = want_nchannels
    config.outputSampleRate = want_sample_rate
    mp3 = ffi.new("drmp3 *")
    if not lib.drmp3_init_file(mp3, filenamebytes, config):
        raise DecodeError("could not open/decode file")
    try:
        decodebuffer = ffi.new("drmp3_int16[]", frames_to_read * mp3.channels)
        buf_ptr = ffi.cast("drmp3_int16 *", decodebuffer)
        while True:
            num_samples = lib.drmp3_read_pcm_frames_s16(mp3, frames_to_read, buf_ptr)
            if num_samples <= 0:
                break
            buffer = ffi.buffer(decodebuffer, num_samples * 2 * mp3.channels)
            samples = _create_int_array(2)
            samples.frombytes(buffer)
            yield samples
    finally:
        lib.drmp3_uninit(mp3)


def wav_get_file_info(filename: str) -> SoundFileInfo:
    """Fetch some information about the audio file (wav format)."""
    filenamebytes = _get_filename_bytes(filename)
    wav = lib.drwav_open_file(filenamebytes)
    if not wav:
        raise DecodeError("could not open/decode file")
    try:
        duration = wav.totalPCMFrameCount / wav.sampleRate
        sample_width = wav.bitsPerSample // 8
        is_float = wav.translatedFormatTag == lib.DR_WAVE_FORMAT_IEEE_FLOAT
        return SoundFileInfo(filename, FileFormat.WAV, wav.channels, wav.sampleRate,
                             _format_from_width(sample_width, is_float), duration, wav.totalPCMFrameCount)
    finally:
        lib.drwav_close(wav)


def wav_get_info(data: bytes) -> SoundFileInfo:
    """Fetch some information about the audio data (wav format)."""
    wav = lib.drwav_open_memory(data, len(data))
    if not wav:
        raise DecodeError("could not open/decode data")
    try:
        duration = wav.totalPCMFrameCount / wav.sampleRate
        sample_width = wav.bitsPerSample // 8
        is_float = wav.translatedFormatTag == lib.DR_WAVE_FORMAT_IEEE_FLOAT
        return SoundFileInfo("<memory>", FileFormat.WAV, wav.channels, wav.sampleRate,
                             _format_from_width(sample_width, is_float), duration, wav.totalPCMFrameCount)
    finally:
        lib.drwav_close(wav)


def wav_read_file_s32(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio file. Resulting sample format is 32 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_file_and_read_pcm_frames_s32(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = _create_int_array(4)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.SIGNED32, samples)
    finally:
        lib.drwav_free(memory)


def wav_read_file_s16(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio file. Resulting sample format is 16 bits signed integer."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_file_and_read_pcm_frames_s16(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.drwav_free(memory)


def wav_read_file_f32(filename: str) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio file. Resulting sample format is 32 bits float."""
    filenamebytes = _get_filename_bytes(filename)
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_file_and_read_pcm_frames_f32(filenamebytes, channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode file")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile(filename, channels[0], sample_rate[0], SampleFormat.FLOAT32, samples)
    finally:
        lib.drwav_free(memory)


def wav_read_s32(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio data. Resulting sample format is 32 bits signed integer."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_memory_and_read_pcm_frames_s32(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = _create_int_array(4)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.SIGNED32, samples)
    finally:
        lib.drwav_free(memory)


def wav_read_s16(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio data. Resulting sample format is 16 bits signed integer."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_memory_and_read_pcm_frames_s16(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = _create_int_array(2)
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 2)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.SIGNED16, samples)
    finally:
        lib.drwav_free(memory)


def wav_read_f32(data: bytes) -> DecodedSoundFile:
    """Reads and decodes the whole wav audio data. Resulting sample format is 32 bits float."""
    channels = ffi.new("unsigned int *")
    sample_rate = ffi.new("unsigned int *")
    num_frames = ffi.new("drwav_uint64 *")
    memory = lib.drwav_open_memory_and_read_pcm_frames_f32(data, len(data), channels, sample_rate, num_frames)
    if not memory:
        raise DecodeError("cannot load/decode data")
    try:
        samples = array.array('f')
        buffer = ffi.buffer(memory, num_frames[0] * channels[0] * 4)
        samples.frombytes(buffer)
        return DecodedSoundFile("<memory>", channels[0], sample_rate[0], SampleFormat.FLOAT32, samples)
    finally:
        lib.drwav_free(memory)


def wav_stream_file(filename: str, frames_to_read: int = 1024) -> Generator[array.array, None, None]:
    """Streams the WAV audio file as interleaved 16 bit signed integer sample arrays segments."""
    filenamebytes = _get_filename_bytes(filename)
    wav = lib.drwav_open_file(filenamebytes)
    if not wav:
        raise DecodeError("could not open/decode file")
    try:
        decodebuffer = ffi.new("drwav_int16[]", frames_to_read * wav.channels)
        buf_ptr = ffi.cast("drwav_int16 *", decodebuffer)
        while True:
            num_samples = lib.drwav_read_pcm_frames_s16(wav, frames_to_read, buf_ptr)
            if num_samples <= 0:
                break
            buffer = ffi.buffer(decodebuffer, num_samples * 2 * wav.channels)
            samples = _create_int_array(2)
            samples.frombytes(buffer)
            yield samples
    finally:
        lib.drwav_close(wav)


def wav_write_file(filename: str, sound: DecodedSoundFile) -> None:
    """Writes the pcm sound to a WAV file"""
    fmt = ffi.new("drwav_data_format*")
    fmt.container = lib.drwav_container_riff
    fmt.format = lib.DR_WAVE_FORMAT_PCM
    fmt.channels = sound.nchannels
    fmt.sampleRate = sound.sample_rate
    fmt.bitsPerSample = sound.sample_width * 8
    # what about floating point format?
    filename_bytes = filename.encode(sys.getfilesystemencoding())
    pwav = lib.drwav_open_file_write_sequential(filename_bytes, fmt, sound.num_frames * sound.nchannels)
    if pwav == ffi.NULL:
        raise IOError("can't open file for writing")
    try:
        lib.drwav_write_pcm_frames(pwav, sound.num_frames, sound.samples.tobytes())
    finally:
        lib.drwav_close(pwav)


def _create_int_array(itemsize: int) -> array.array:
    for typecode in "Bhilq":
        a = array.array(typecode)
        if a.itemsize == itemsize:
            return a
    raise ValueError("cannot create array")


def _get_filename_bytes(filename: str) -> bytes:
    filename2 = os.path.expanduser(filename)
    if not os.path.isfile(filename2):
        raise FileNotFoundError(filename)
    return filename2.encode(sys.getfilesystemencoding())


class Devices:
    """Query the audio playback and record devices that miniaudio provides"""
    def __init__(self, backends: Optional[List[Backend]] = None) -> None:
        self._context = ffi.NULL
        context = ffi.new("ma_context*")
        if backends:
            backends_mem = ffi.new("ma_backend[]", len(backends))
            for i, b in enumerate(backends):
                backends_mem[i] = b.value
            result = lib.ma_context_init(backends_mem, len(backends), ffi.NULL, context)
        else:
            result = lib.ma_context_init(ffi.NULL, 0, ffi.NULL, context)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("cannot init context", result)
        self._context = context
        self.backend = ffi.string(lib.ma_get_backend_name(self._context[0].backend)).decode()

    def get_playbacks(self) -> List[Dict[str, Any]]:
        """Get a list of playback devices and some details about them"""
        playback_infos = ffi.new("ma_device_info**")
        playback_count = ffi.new("ma_uint32*")
        result = lib.ma_context_get_devices(self._context, playback_infos, playback_count, ffi.NULL,  ffi.NULL)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("cannot get device infos", result)
        devs = []
        for i in range(playback_count[0]):
            ma_device_info = playback_infos[0][i]
            dev_id = ffi.new("ma_device_id *", ma_device_info.id)  # copy the id memory
            info = {
                "name": ffi.string(ma_device_info.name).decode(),
                "type": DeviceType.PLAYBACK,
                "id": dev_id
            }
            info.update(self._get_info(DeviceType.PLAYBACK, ma_device_info))
            devs.append(info)
        return devs

    def get_captures(self) -> List[Dict[str, Any]]:
        """Get a list of capture devices and some details about them"""
        capture_infos = ffi.new("ma_device_info**")
        capture_count = ffi.new("ma_uint32*")
        result = lib.ma_context_get_devices(self._context, ffi.NULL,  ffi.NULL, capture_infos, capture_count)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("cannot get device infos", result)
        devs = []
        for i in range(capture_count[0]):
            ma_device_info = capture_infos[0][i]
            dev_id = ffi.new("ma_device_id *", ma_device_info.id)  # copy the id memory
            info = {
                "name": ffi.string(ma_device_info.name).decode(),
                "type": DeviceType.CAPTURE,
                "id": dev_id
            }
            info.update(self._get_info(DeviceType.CAPTURE, ma_device_info))
            devs.append(info)
        return devs

    def _get_info(self, device_type: DeviceType, device_info: ffi.CData) -> Dict[str, Any]:
        # obtain detailed info about the device
        lib.ma_context_get_device_info(self._context, device_type.value, ffi.addressof(device_info.id),
                                       0, ffi.addressof(device_info))
        formats = set(device_info.formats[0:device_info.formatCount])
        return {
            "formats": {f: ffi.string(lib.ma_get_format_name(f)).decode() for f in formats},
            "minChannels": device_info.minChannels,
            "maxChannels": device_info.maxChannels,
            "minSampleRate": device_info.minSampleRate,
            "maxSampleRate": device_info.maxSampleRate
        }

    def __del__(self):
        lib.ma_context_uninit(self._context)


def _width_from_format(sampleformat: SampleFormat) -> int:
    widths = {
        SampleFormat.UNSIGNED8: 1,
        SampleFormat.SIGNED16: 2,
        SampleFormat.SIGNED24: 3,
        SampleFormat.SIGNED32: 4,
        SampleFormat.FLOAT32: 4
    }
    if sampleformat in widths:
        return widths[sampleformat]
    raise MiniaudioError("unsupported sample format", sampleformat)


def _array_proto_from_format(sampleformat: SampleFormat) -> array.array:
    arrays = {
        SampleFormat.UNSIGNED8: _create_int_array(1),
        SampleFormat.SIGNED16: _create_int_array(2),
        SampleFormat.SIGNED32: _create_int_array(4),
        SampleFormat.FLOAT32: array.array('f')
    }
    if sampleformat in arrays:
        return arrays[sampleformat]
    raise MiniaudioError("the requested sample format can not be used directly: "
                         + sampleformat.name + " (convert it first)")


def _format_from_width(sample_width: int, is_float: bool = False) -> SampleFormat:
    if is_float:
        return SampleFormat.FLOAT32
    elif sample_width == 1:
        return SampleFormat.UNSIGNED8
    elif sample_width == 2:
        return SampleFormat.SIGNED16
    elif sample_width == 3:
        return SampleFormat.SIGNED24
    elif sample_width == 4:
        return SampleFormat.SIGNED32
    else:
        raise MiniaudioError("unsupported sample width", sample_width)


def decode_file(filename: str, output_format: SampleFormat = SampleFormat.SIGNED16,
                nchannels: int = 2, sample_rate: int = 44100, dither: DitherMode = DitherMode.NONE) -> DecodedSoundFile:
    """Convenience function to decode any supported audio file to raw PCM samples in your chosen format."""
    sample_width = _width_from_format(output_format)
    samples = _array_proto_from_format(output_format)
    filenamebytes = _get_filename_bytes(filename)
    frames = ffi.new("ma_uint64 *")
    data = ffi.new("void **")
    decoder_config = lib.ma_decoder_config_init(output_format.value, nchannels, sample_rate)
    decoder_config.ditherMode = dither.value
    result = lib.ma_decode_file(filenamebytes, ffi.addressof(decoder_config), frames, data)
    if result != lib.MA_SUCCESS:
        raise DecodeError("failed to decode file", result)
    buffer = ffi.buffer(data[0], frames[0] * nchannels * sample_width)
    samples.frombytes(buffer)
    return DecodedSoundFile(filename, nchannels, sample_rate, output_format, samples)


def decode(data: bytes, output_format: SampleFormat = SampleFormat.SIGNED16,
           nchannels: int = 2, sample_rate: int = 44100, dither: DitherMode = DitherMode.NONE) -> DecodedSoundFile:
    """Convenience function to decode any supported audio file in memory to raw PCM samples in your chosen format."""
    sample_width = _width_from_format(output_format)
    samples = _array_proto_from_format(output_format)
    frames = ffi.new("ma_uint64 *")
    memory = ffi.new("void **")
    decoder_config = lib.ma_decoder_config_init(output_format.value, nchannels, sample_rate)
    decoder_config.ditherMode = dither.value
    result = lib.ma_decode_memory(data, len(data), ffi.addressof(decoder_config), frames, memory)
    if result != lib.MA_SUCCESS:
        raise DecodeError("failed to decode data", result)
    buffer = ffi.buffer(memory[0], frames[0] * nchannels * sample_width)
    samples.frombytes(buffer)
    return DecodedSoundFile("<memory>", nchannels, sample_rate, output_format, samples)


def _samples_stream_generator(frames_to_read: int, nchannels: int, output_format: SampleFormat,
                              decoder: ffi.CData, data: Any,
                              on_close: Optional[Callable] = None) -> Generator[array.array, int, None]:
    _reference = data    # make sure any data passed in is not garbage collected
    sample_width = _width_from_format(output_format)
    samples_proto = _array_proto_from_format(output_format)
    allocated_buffer_frames = max(frames_to_read, 16384)
    try:
        decodebuffer = ffi.new("int8_t[]", allocated_buffer_frames * nchannels * sample_width)
        buf_ptr = ffi.cast("void *", decodebuffer)
        want_frames = (yield samples_proto) or frames_to_read
        while True:
            if want_frames > allocated_buffer_frames:
                raise MiniaudioError("wanted to read more frames than storage was allocated for ({} vs {})"
                                     .format(want_frames, allocated_buffer_frames))
            num_frames = lib.ma_decoder_read_pcm_frames(decoder, buf_ptr, want_frames)
            if num_frames <= 0:
                break
            buffer = ffi.buffer(decodebuffer, num_frames * sample_width * nchannels)
            samples = array.array(samples_proto.typecode)
            samples.frombytes(buffer)
            want_frames = (yield samples) or frames_to_read
    finally:
        if on_close:
            on_close()
        lib.ma_decoder_uninit(decoder)


def stream_file(filename: str, output_format: SampleFormat = SampleFormat.SIGNED16, nchannels: int = 2,
                sample_rate: int = 44100, frames_to_read: int = 1024,
                dither: DitherMode = DitherMode.NONE) -> Generator[array.array, int, None]:
    """
    Convenience generator function to decode and stream any supported audio file
    as chunks of raw PCM samples in the chosen format.
    If you send() a number into the generator rather than just using next() on it,
    you'll get that given number of frames, instead of the default configured amount.
    This is particularly useful to plug this stream into an audio device callback that
    wants a variable number of frames per call.
    """
    filenamebytes = _get_filename_bytes(filename)
    decoder = ffi.new("ma_decoder *")
    decoder_config = lib.ma_decoder_config_init(output_format.value, nchannels, sample_rate)
    decoder_config.ditherMode = dither.value
    result = lib.ma_decoder_init_file(filenamebytes, ffi.addressof(decoder_config), decoder)
    if result != lib.MA_SUCCESS:
        raise DecodeError("failed to init decoder", result)
    g = _samples_stream_generator(frames_to_read, nchannels, output_format, decoder, None)
    dummy = next(g)
    assert len(dummy) == 0
    return g


def stream_memory(data: bytes, output_format: SampleFormat = SampleFormat.SIGNED16, nchannels: int = 2,
                  sample_rate: int = 44100, frames_to_read: int = 1024,
                  dither: DitherMode = DitherMode.NONE) -> Generator[array.array, int, None]:
    """
    Convenience generator function to decode and stream any supported audio file in memory
    as chunks of raw PCM samples in the chosen format.
    If you send() a number into the generator rather than just using next() on it,
    you'll get that given number of frames, instead of the default configured amount.
    This is particularly useful to plug this stream into an audio device callback that
    wants a variable number of frames per call.
    """
    decoder = ffi.new("ma_decoder *")
    decoder_config = lib.ma_decoder_config_init(output_format.value, nchannels, sample_rate)
    decoder_config.ditherMode = dither.value
    result = lib.ma_decoder_init_memory(data, len(data), ffi.addressof(decoder_config), decoder)
    if result != lib.MA_SUCCESS:
        raise DecodeError("failed to init decoder", result)
    g = _samples_stream_generator(frames_to_read, nchannels, output_format, decoder, data)
    dummy = next(g)
    assert len(dummy) == 0
    return g


class StreamableSource(abc.ABC):
    """Represents a source of data bytes."""
    userdata_ptr = ffi.NULL         # is set later

    @abc.abstractmethod
    def read(self, num_bytes: int) -> Union[bytes, memoryview]:
        pass

    def seek(self, offset: int, origin: SeekOrigin) -> bool:
        # Note: seek support is usually not needed if you give the file type
        # to the decoder upfront. You can ignore this method then.
        return False


def stream_any(source: StreamableSource, source_format: FileFormat = FileFormat.UNKNOWN,
               output_format: SampleFormat = SampleFormat.SIGNED16, nchannels: int = 2,
               sample_rate: int = 44100, frames_to_read: int = 1024,
               dither: DitherMode = DitherMode.NONE) -> Generator[array.array, int, None]:
    """
    Convenience generator function to decode and stream any source of encoded audio data
    (such as a network stream). Stream result is chunks of raw PCM samples in the chosen format.
    If you send() a number into the generator rather than just using next() on it,
    you'll get that given number of frames, instead of the default configured amount.
    This is particularly useful to plug this stream into an audio device callback that
    wants a variable number of frames per call.
    """
    decoder = ffi.new("ma_decoder *")
    decoder_config = lib.ma_decoder_config_init(output_format.value, nchannels, sample_rate)
    decoder_config.ditherMode = dither.value
    _callback_decoder_sources[id(source)] = source
    source.userdata_ptr = ffi.new("char[]", struct.pack('q', id(source)))
    decoder_init = {
        FileFormat.UNKNOWN: lib.ma_decoder_init,
        FileFormat.VORBIS: lib.ma_decoder_init_vorbis,
        FileFormat.WAV: lib.ma_decoder_init_wav,
        FileFormat.FLAC: lib.ma_decoder_init_flac,
        FileFormat.MP3: lib.ma_decoder_init_mp3
    }[source_format]
    result = decoder_init(lib._internal_decoder_read_callback, lib._internal_decoder_seek_callback,
                          source.userdata_ptr, ffi.addressof(decoder_config), decoder)
    if result != lib.MA_SUCCESS:
        raise DecodeError("failed to init decoder", result)

    def on_close() -> None:
        if id(source) in _callback_decoder_sources:
            del _callback_decoder_sources[id(source)]

    g = _samples_stream_generator(frames_to_read, nchannels, output_format, decoder, None, on_close)
    dummy = next(g)
    assert len(dummy) == 0
    return g


_callback_decoder_sources = {}     # type: Dict[int, StreamableSource]

# this lowlevel callback function is used in stream_any to provide encoded input audio data.
# There is some trickery going on with the userdata that contains an id into the dictionary
# to link back to the Python object that the callback belongs to.
@ffi.def_extern()
def _internal_decoder_read_callback(decoder: ffi.CData, output: ffi.CData, num_bytes: int) -> int:
    if num_bytes <= 0 or not decoder.pUserData:
        return 0
    userdata_id = struct.unpack('q', ffi.unpack(ffi.cast("char *", decoder.pUserData), struct.calcsize('q')))[0]
    source = _callback_decoder_sources[userdata_id]
    data = source.read(num_bytes)
    ffi.memmove(output, data, len(data))
    return len(data)


@ffi.def_extern()
def _internal_decoder_seek_callback(decoder: ffi.CData, offset: int, seek_origin: int) -> int:
    if not decoder.pUserData:
        return False
    if offset == 0 and seek_origin == lib.ma_seek_origin_current:
        return True
    userdata_id = struct.unpack('q', ffi.unpack(ffi.cast("char *", decoder.pUserData), struct.calcsize('q')))[0]
    source = _callback_decoder_sources[userdata_id]
    return int(source.seek(offset, SeekOrigin(seek_origin)))


def convert_sample_format(from_fmt: SampleFormat, sourcedata: bytes, to_fmt: SampleFormat,
                          dither: DitherMode = DitherMode.NONE) -> bytearray:
    """Convert a raw buffer of pcm samples to another sample format.
    The result is returned as another raw pcm sample buffer"""
    sample_width = _width_from_format(from_fmt)
    num_samples = len(sourcedata) // sample_width
    sample_width = _width_from_format(to_fmt)
    buffer = bytearray(sample_width * num_samples)
    lib.ma_pcm_convert(ffi.from_buffer(buffer), to_fmt.value, sourcedata, from_fmt.value, num_samples, dither.value)
    return buffer


def convert_frames(from_fmt: SampleFormat, from_numchannels: int, from_samplerate: int, sourcedata: bytes,
                   to_fmt: SampleFormat, to_numchannels: int, to_samplerate: int) -> bytearray:
    """Convert audio frames in source sample format with a certain number of channels,
    to another sample format and possibly down/upmixing the number of channels as well."""
    sample_width = _width_from_format(from_fmt)
    num_frames = int(len(sourcedata) / from_numchannels / sample_width)
    sample_width = _width_from_format(to_fmt)
    output_frame_count = lib.ma_calculate_frame_count_after_src(to_samplerate, from_samplerate, num_frames)
    buffer = bytearray(output_frame_count * sample_width * to_numchannels)
    # note: the API doesn't have an option here to specify the dither mode.
    lib.ma_convert_frames(ffi.from_buffer(buffer), to_fmt.value, to_numchannels, to_samplerate,
                          sourcedata, from_fmt.value, from_numchannels, from_samplerate, num_frames)
    return buffer


_callback_data = {}     # type: Dict[int, Union[PlaybackDevice, CaptureDevice, DuplexStream]]

# this lowlevel callback function is used in the Plaback/Capture/Duplex devices,
# to process the data that is flowing. There is some trickery going on with the
# userdata that contains an id into the dictionary to link back to the Python object
# that the callback originates from
@ffi.def_extern()
def _internal_data_callback(device: ffi.CData, output: ffi.CData, input: ffi.CData, framecount: int) -> None:
    if framecount <= 0 or not device.pUserData:
        return
    userdata_id = struct.unpack('q', ffi.unpack(ffi.cast("char *", device.pUserData), struct.calcsize('q')))[0]
    callback_device = _callback_data[userdata_id]  # type: Union[PlaybackDevice, CaptureDevice, DuplexStream]
    callback_device._data_callback(device, output, input, framecount)


class AbstractDevice:
    def __init__(self):
        self.callback_generator = None          # type: Optional[GeneratorTypes]
        self._device = ffi.new("ma_device *")

    def __del__(self) -> None:
        self.close()

    def start(self, callback_generator: GeneratorTypes) -> None:
        """Start playback or capture, using the given callback generator (should already been started)"""
        if self.callback_generator:
            raise MiniaudioError("can't start an already started device")
        if not inspect.isgenerator(callback_generator):
            raise TypeError("callback must be a generator", type(callback_generator))
        self.callback_generator = callback_generator
        result = lib.ma_device_start(self._device)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to start audio device", result)

    def stop(self) -> None:
        """Halt playback or capture."""
        self.callback_generator = None
        result = lib.ma_device_stop(self._device)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to stop audio device", result)

    def close(self) -> None:
        """Halt playback or capture and close down the device."""
        self.callback_generator = None
        if self._device is not None:
            lib.ma_device_uninit(self._device)
            self._device = None
        if id(self) in _callback_data:
            del _callback_data[id(self)]

    def _make_context(self, backends: List[Backend], thread_prio: ThreadPriority = ThreadPriority.HIGHEST,
                      app_name: str = "") -> ffi.CData:
        context_config = lib.ma_context_config_init()
        context_config.threadPriority = thread_prio.value
        context = ffi.new("ma_context*")
        if app_name:
            self._context_app_name = app_name.encode()
            context_config.pulse.pApplicationName = ffi.from_buffer(self._context_app_name)
            context_config.jack.pClientName = ffi.from_buffer(self._context_app_name)
        if backends:
            # use a context to supply a preferred backend list
            backends_mem = ffi.new("ma_backend[]", len(backends))
            for i, b in enumerate(backends):
                backends_mem[i] = b.value
            result = lib.ma_context_init(backends_mem, len(backends), ffi.addressof(context_config), context)
            if result != lib.MA_SUCCESS:
                raise MiniaudioError("cannot init context", result)
        else:
            result = lib.ma_context_init(ffi.NULL, 0, ffi.addressof(context_config), context)
            if result != lib.MA_SUCCESS:
                raise MiniaudioError("cannot init context", result)
        return context


class CaptureDevice(AbstractDevice):
    """An audio device provided by miniaudio, for audio capture (recording)."""
    def __init__(self, input_format: SampleFormat = SampleFormat.SIGNED16, nchannels: int = 2,
                 sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Union[ffi.CData, None] = None,
                 callback_periods: int = 0, backends: Optional[List[Backend]] = None,
                 thread_prio: ThreadPriority = ThreadPriority.HIGHEST, app_name: str = "") -> None:
        super().__init__()
        self.format = input_format
        self.sample_width = _width_from_format(input_format)
        self.nchannels = nchannels
        self.sample_rate = sample_rate
        self.buffersize_msec = buffersize_msec
        _callback_data[id(self)] = self
        self.userdata_ptr = ffi.new("char[]", struct.pack('q', id(self)))
        self._devconfig = lib.ma_device_config_init(lib.ma_device_type_capture)
        self._devconfig.sampleRate = self.sample_rate
        self._devconfig.capture.channels = self.nchannels
        self._devconfig.capture.format = self.format.value
        self._devconfig.capture.pDeviceID = device_id or ffi.NULL
        self._devconfig.bufferSizeInMilliseconds = self.buffersize_msec
        self._devconfig.pUserData = self.userdata_ptr
        self._devconfig.dataCallback = lib._internal_data_callback
        self._devconfig.periods = callback_periods
        self.callback_generator = None  # type: Optional[CaptureCallbackGeneratorType]
        self._context = self._make_context(backends or [], thread_prio, app_name)
        result = lib.ma_device_init(self._context, ffi.addressof(self._devconfig), self._device)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to init device", result)
        if self._device.pContext.backend == lib.ma_backend_null:
            raise MiniaudioError("no suitable audio backend found")
        self.backend = ffi.string(lib.ma_get_backend_name(self._device.pContext.backend)).decode()

    def start(self, callback_generator: CaptureCallbackGeneratorType) -> None:      # type: ignore
        """Start the audio device: capture (recording) begins.
        The recorded audio data is sent to the given callback generator as raw bytes.
        (it should already be started before)"""
        return super().start(callback_generator)

    def _data_callback(self, device: ffi.CData, output: ffi.CData, input: ffi.CData, framecount: int) -> None:
        if self.callback_generator:
            buffer_size = self.sample_width * self.nchannels * framecount
            data = bytearray(buffer_size)
            ffi.memmove(data, input, buffer_size)
            try:
                self.callback_generator.send(data)
            except StopIteration:
                self.callback_generator = None
                return
            except Exception:
                self.callback_generator = None
                raise


class PlaybackDevice(AbstractDevice):
    """An audio device provided by miniaudio, for audio playback."""
    def __init__(self, output_format: SampleFormat = SampleFormat.SIGNED16, nchannels: int = 2,
                 sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Union[ffi.CData, None] = None,
                 callback_periods: int = 0, backends: Optional[List[Backend]] = None,
                 thread_prio: ThreadPriority = ThreadPriority.HIGHEST, app_name: str = "") -> None:
        super().__init__()
        self.format = output_format
        self.sample_width = _width_from_format(output_format)
        self.nchannels = nchannels
        self.sample_rate = sample_rate
        self.buffersize_msec = buffersize_msec
        _callback_data[id(self)] = self
        self.userdata_ptr = ffi.new("char[]", struct.pack('q', id(self)))
        self._devconfig = lib.ma_device_config_init(lib.ma_device_type_playback)
        self._devconfig.sampleRate = self.sample_rate
        self._devconfig.playback.channels = self.nchannels
        self._devconfig.playback.format = self.format.value
        self._devconfig.playback.pDeviceID = device_id or ffi.NULL
        self._devconfig.bufferSizeInMilliseconds = self.buffersize_msec
        self._devconfig.pUserData = self.userdata_ptr
        self._devconfig.dataCallback = lib._internal_data_callback
        self._devconfig.periods = callback_periods
        self.callback_generator = None   # type: Optional[PlaybackCallbackGeneratorType]

        self._context = self._make_context(backends or [], thread_prio, app_name)
        result = lib.ma_device_init(self._context, ffi.addressof(self._devconfig), self._device)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to init device", result)
        if self._device.pContext.backend == lib.ma_backend_null:
            raise MiniaudioError("no suitable audio backend found")
        self.backend = ffi.string(lib.ma_get_backend_name(self._device.pContext.backend)).decode()

    def start(self, callback_generator: PlaybackCallbackGeneratorType) -> None:     # type: ignore
        """Start the audio device: playback begins. The audio data is provided by the given callback generator.
        The generator gets sent the required number of frames and should yield the sample data
        as raw bytes, a memoryview, an array.array, or as a numpy array with shape (numframes, numchannels).
        The generator should already be started before passing it in."""
        return super().start(callback_generator)

    def _data_callback(self, device: ffi.CData, output: ffi.CData, input: ffi.CData, framecount: int) -> None:
        if self.callback_generator:
            try:
                samples = self.callback_generator.send(framecount)
            except StopIteration:
                self.callback_generator = None
                return
            except Exception:
                self.callback_generator = None
                raise
            samples_bytes = _bytes_from_generator_samples(samples)
            if samples_bytes:
                if len(samples_bytes) > framecount * self.sample_width * self.nchannels:
                    self.callback_generator = None
                    raise MiniaudioError("number of frames from callback exceeds maximum")
                ffi.memmove(output, samples_bytes, len(samples_bytes))


class DuplexStream(AbstractDevice):
    """Joins a capture device and a playback device."""
    def __init__(self, playback_format: SampleFormat = SampleFormat.SIGNED16,
                 playback_channels: int = 2, capture_format: SampleFormat = SampleFormat.SIGNED16,
                 capture_channels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200,
                 playback_device_id: Union[ffi.CData, None] = None, capture_device_id: Union[ffi.CData, None] = None,
                 callback_periods: int = 0, backends: Optional[List[Backend]] = None,
                 thread_prio: ThreadPriority = ThreadPriority.HIGHEST, app_name: str = "") -> None:
        super().__init__()
        self.capture_format = capture_format
        self.playback_format = playback_format
        self.sample_width = _width_from_format(capture_format)
        self.capture_channels = capture_channels
        self.playback_channels = playback_channels
        self.sample_rate = sample_rate
        self.buffersize_msec = buffersize_msec
        _callback_data[id(self)] = self
        self.userdata_ptr = ffi.new("char[]", struct.pack('q', id(self)))
        self._devconfig = lib.ma_device_config_init(lib.ma_device_type_duplex)
        self._devconfig.sampleRate = self.sample_rate
        self._devconfig.playback.channels = self.playback_channels
        self._devconfig.playback.format = self.playback_format.value
        self._devconfig.playback.pDeviceID = playback_device_id or ffi.NULL
        self._devconfig.capture.channels = self.capture_channels
        self._devconfig.capture.format = self.capture_format.value
        self._devconfig.capture.pDeviceID = capture_device_id or ffi.NULL
        self._devconfig.bufferSizeInMilliseconds = self.buffersize_msec
        self._devconfig.pUserData = self.userdata_ptr
        self._devconfig.dataCallback = lib._internal_data_callback
        self._devconfig.periods = callback_periods
        self.callback_generator = None  # type: Optional[DuplexCallbackGeneratorType]
        self._context = self._make_context(backends or [], thread_prio, app_name)
        result = lib.ma_device_init(self._context, ffi.addressof(self._devconfig), self._device)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to init device", result)
        if self._device.pContext.backend == lib.ma_backend_null:
            raise MiniaudioError("no suitable audio backend found")
        self.backend = ffi.string(lib.ma_get_backend_name(self._device.pContext.backend)).decode()

    def start(self, callback_generator: DuplexCallbackGeneratorType) -> None:   # type: ignore
        """Start the audio device: playback and capture begin.
        The audio data for playback is provided by the given callback generator, which is sent the
        recorded audio data at the same time.
        (it should already be started before passing it in)"""
        return super().start(callback_generator)

    def _data_callback(self, device: ffi.CData, output: ffi.CData, input: ffi.CData, framecount: int) -> None:
        buffer_size = self.sample_width * self.capture_channels * framecount
        in_data = bytearray(buffer_size)
        ffi.memmove(in_data, input, buffer_size)
        if self.callback_generator:
            try:
                out_data = self.callback_generator.send(in_data)
            except StopIteration:
                self.callback_generator = None
                return
            except Exception:
                self.callback_generator = None
                raise
            if out_data:
                samples_bytes = _bytes_from_generator_samples(out_data)
                ffi.memmove(output, samples_bytes, len(samples_bytes))


def _bytes_from_generator_samples(samples: Union[array.array, memoryview, bytes]) -> bytes:
    # convert any non-bytes generator result to raw bytes
    if isinstance(samples, array.array):
        return memoryview(samples).cast('B')       # type: ignore
    elif isinstance(samples, memoryview) and samples.itemsize != 1:
        return samples.cast('B')    # type: ignore
    elif numpy and isinstance(samples, numpy.ndarray):
        return samples.tobytes()
    return samples      # type: ignore


class WavFileReadStream(io.RawIOBase):
    """An IO stream that reads as a .wav file, and which gets its pcm samples from the provided producer"""
    def __init__(self, pcm_sample_gen: PlaybackCallbackGeneratorType, sample_rate: int, nchannels: int,
                 output_format: SampleFormat, max_frames: int = 0) -> None:
        self.sample_gen = pcm_sample_gen
        self.sample_rate = sample_rate
        self.nchannels = nchannels
        self.format = output_format
        self.max_frames = max_frames
        self.sample_width = _width_from_format(output_format)
        self.max_bytes = (max_frames * nchannels * self.sample_width) or sys.maxsize
        self.bytes_done = 0
        # create WAVE header
        fmt = ffi.new("drwav_data_format*")
        fmt.container = lib.drwav_container_riff
        fmt.format = lib.DR_WAVE_FORMAT_PCM
        fmt.channels = nchannels
        fmt.sampleRate = sample_rate
        fmt.bitsPerSample = self.sample_width * 8
        data = ffi.new("void**")
        datasize = ffi.new("size_t *")
        if max_frames > 0:
            pwav = lib.drwav_open_memory_write_sequential(data, datasize, fmt, max_frames * nchannels)
        else:
            pwav = lib.drwav_open_memory_write(data, datasize, fmt)
        lib.drwav_close(pwav)
        self.buffered = bytes(ffi.buffer(data[0], datasize[0]))
        lib.drflac_free(data[0])

    def read(self, amount: int = sys.maxsize) -> Optional[bytes]:
        """Read up to the given amount of bytes from the file."""
        if self.bytes_done >= self.max_bytes or not self.sample_gen:
            return b""
        while len(self.buffered) < amount:
            try:
                samples = next(self.sample_gen)
            except StopIteration:
                self.bytes_done = sys.maxsize
                break
            else:
                self.buffered += _bytes_from_generator_samples(samples)
        result = self.buffered[:amount]
        self.buffered = self.buffered[amount:]
        self.bytes_done += len(result)
        return result

    def close(self) -> None:
        """Close the file"""
        pass


_callback_converter = {}      # type: Dict[int, StreamingConverter]

# this lowlevel callback function is used in the StreamingConverter streaming audio conversion
# to produce input PCM audio frames. There is some trickery going on with the
# userdata that contains an id into the dictionary to link back to the Python object
# that the callback originates from.
@ffi.def_extern()
def _internal_pcmconverter_read_callback(converter: ffi.CData, frames: ffi.CData,
                                         framecount: int, userdata: ffi.CData) -> int:
    if framecount <= 0 or not userdata:
        return framecount
    userdata_id = struct.unpack('q', ffi.unpack(ffi.cast("char *", userdata), struct.calcsize('q')))[0]
    callback_converter = _callback_converter[userdata_id]
    return callback_converter._read_callback(converter, frames, framecount)


class StreamingConverter:
    """Sample format converter that works on streams stream, rather than doing all at once."""
    def __init__(self, in_format: SampleFormat, in_channels: int, in_samplerate: int,
                 out_format: SampleFormat, out_channels: int, out_samplerate: int,
                 frame_producer: PlaybackCallbackGeneratorType,
                 dither: DitherMode = DitherMode.NONE) -> None:
        if not inspect.isgenerator(frame_producer):
            raise TypeError("producer must be a generator", type(frame_producer))
        self.frame_producer = frame_producer        # type: Optional[PlaybackCallbackGeneratorType]
        _callback_converter[id(self)] = self
        self._userdata_ptr = ffi.new("char[]", struct.pack('q', id(self)))
        self._conv_config = lib.ma_pcm_converter_config_init(
            in_format.value, in_channels, in_samplerate, out_format.value, out_channels, out_samplerate,
            lib._internal_pcmconverter_read_callback, self._userdata_ptr)
        self._conv_config.ditherMode = dither.value
        self._converter = ffi.new("ma_pcm_converter*")
        result = lib.ma_pcm_converter_init(ffi.addressof(self._conv_config), self._converter)
        if result != lib.MA_SUCCESS:
            raise MiniaudioError("failed to init pcm_converter", result)
        self.in_format = in_format
        self.in_channels = in_channels
        self.in_samplerate = in_samplerate
        self.in_samplewidth = _width_from_format(in_format)
        self.out_format = out_format
        self.out_channels = out_channels
        self.out_samplerate = out_samplerate
        self.out_samplewidth = _width_from_format(out_format)

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if id(self) in _callback_converter:
            del _callback_converter[id(self)]

    def read(self, num_frames: int) -> array.array:
        """Read a chunk of frames from the source and return the given number of converted frames."""
        frames = bytearray(num_frames * self.out_channels * self.out_samplewidth)
        num_converted_frames = lib.ma_pcm_converter_read(self._converter, ffi.from_buffer(frames), num_frames)
        result = _array_proto_from_format(self.out_format)
        buf = memoryview(frames)[0:num_converted_frames * self.out_channels * self.out_samplewidth]
        result.frombytes(buf)       # type: ignore
        return result

    def _read_callback(self, converter: ffi.CData, frames: ffi.CData, framecount: int) -> int:
        if self.frame_producer:
            try:
                data = self.frame_producer.send(framecount)
            except StopIteration:
                self.frame_producer = None
                return 0
            except Exception:
                self.frame_producer = None
                raise
            frames_bytes = _bytes_from_generator_samples(data)
            if frames_bytes:
                if len(frames_bytes) > framecount * self.in_samplewidth * self.in_channels:
                    self.frame_producer = None
                    raise MiniaudioError("number of frames from callback exceeds maximum")
                ffi.memmove(frames, frames_bytes, len(frames_bytes))
                return int(len(frames_bytes) / self.in_samplewidth / self.in_channels)
        return 0
