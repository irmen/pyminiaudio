[![saythanks](https://img.shields.io/badge/say-thanks-ff69b4.svg)](https://saythanks.io/to/irmen)
[![Latest Version](https://img.shields.io/pypi/v/miniaudio.svg)](https://pypi.python.org/pypi/miniaudio/)
[![Build Status](https://travis-ci.org/irmen/pyminiaudio.svg?branch=master)](https://travis-ci.org/irmen/pyminiaudio)


# Python miniaudio

This module provides:

- the [miniaudio](https://github.com/dr-soft/miniaudio/) cross platform sound playback, recording and conversion library
- its decoders for wav, flac, vorbis and mp3
- python bindings for most of the functions offered in those libraries:
  - reading and decoding audio files
  - getting audio file properties (such as duration, number of channels, sample rate) 
  - converting sample formats
  - streaming large audio files
  - audio playback
  - audio recording

Audio playback and recording are done with an efficient generator based pull-API.
 

*Requires Python 3.5 or newer.  Also works on pypy3 (because it uses cffi).* 

The library is primarily distributed in source form so you need a C compiler to build and install this
(note: the setup script takes care of the actual compilation process, no need to worry about compiling things yourself).
For Linux and Mac this shouldn't be a problem. For Windows users, if the correct binary install
is not available on pypi, you'll have to get it to compile as well which may be a bit of a hassle 
on this platform. You have to make sure that the required tools that allow you to compile Python extension modules
are installed (Visual Studio or the VC++ build tools).
 
Software license for these Python bindings, miniaudio and the decoders: MIT

## Todo

- wrap the .mod and .xm player API


## Examples

### Most basic audio file playback

```python
import miniaudio
stream = miniaudio.stream_file("samples/music.mp3")
device = miniaudio.PlaybackDevice()
device.start(stream)
input("Audio file playing in the background. Enter to stop playback: ")
device.close()
```

### Playback using several other API functions

```python
import miniaudio

def memory_stream(soundfile: miniaudio.DecodedSoundFile) -> miniaudio.PlaybackCallbackGeneratorType:
    required_frames = yield b""  # generator initialization
    current = 0
    samples = memoryview(soundfile.samples)     # avoid needless memory copying
    while current < len(samples):
        sample_count = required_frames * soundfile.nchannels
        output = samples[current:current + sample_count]
        current += sample_count
        print(".", end="", flush=True)
        required_frames = yield output

device = miniaudio.PlaybackDevice()
decoded = miniaudio.decode_file("samples/music.mp3")
print("The decoded file has {} frames at {} hz and takes {:.1f} seconds"
      .format(decoded.num_frames, decoded.sample_rate, decoded.duration))
stream = memory_stream(decoded)
next(stream)  # start the generator
device.start(stream)
input("Audio file playing in the background. Enter to stop playback: ")
device.close()
```

### Playback of a file format that miniaudio can't decode by itself

This example uses ffmpeg as an external tool to decode an audio file in a format
that miniaudio itself can't decode (m4a/aac in this case):

```python
import subprocess
import miniaudio

channels = 2
sample_rate = 44100
sample_width = 2  # 16 bit pcm
filename = "samples/music.m4a"  # AAC encoded audio file

def stream_pcm(source):
    required_frames = yield b""  # generator initialization
    while True:
        required_bytes = required_frames * channels * sample_width
        sample_data = source.read(required_bytes)
        if not sample_data:
            break
        print(".", end="", flush=True)
        required_frames = yield sample_data

device = miniaudio.PlaybackDevice(ma_output_format=miniaudio.ma_format_s16,
                                  nchannels=channels, sample_rate=sample_rate)
ffmpeg = subprocess.Popen(["ffmpeg", "-v", "fatal", "-hide_banner", "-nostdin",
                           "-i", filename, "-f", "s16le", "-acodec", "pcm_s16le",
                           "-ac", str(channels), "-ar", str(sample_rate), "-"],
                          stdin=None, stdout=subprocess.PIPE)
stream = stream_pcm(ffmpeg.stdout)
next(stream)  # start the generator
device.start(stream)
input("Audio file playing in the background. Enter to stop playback: ")
device.close()
ffmpeg.terminate()
``` 

## API


*function*  ``convert_frames  (from_fmt: miniaudio.SampleFormat, from_numchannels: int, from_samplerate: int, sourcedata: bytes, to_fmt: miniaudio.SampleFormat, to_numchannels: int, to_samplerate: int) -> bytearray``

> Convert audio frames in source sample format with a certain number of channels, to another sample
format and possibly down/upmixing the number of channels as well.


*function*  ``convert_sample_format  (from_fmt: miniaudio.SampleFormat, sourcedata: bytes, to_fmt: miniaudio.SampleFormat, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>) -> bytearray``

> Convert a raw buffer of pcm samples to another sample format. The result is returned as another
raw pcm sample buffer


*function*  ``decode  (data: bytes, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100) -> miniaudio.DecodedSoundFile``

> Convenience function to decode any supported audio file in memory to raw PCM samples in your
chosen format.


*function*  ``decode_file  (filename: str, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100) -> miniaudio.DecodedSoundFile``

> Convenience function to decode any supported audio file to raw PCM samples in your chosen format.


*function*  ``flac_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio file (flac format).


*function*  ``flac_get_info  (data: bytes) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio data (flac format).


*function*  ``flac_read_f32  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio file. Resulting sample format is 32 bits float.


*function*  ``flac_read_file_f32  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio file. Resulting sample format is 32 bits float.


*function*  ``flac_read_file_s16  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio file. Resulting sample format is 16 bits signed integer.


*function*  ``flac_read_file_s32  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio file. Resulting sample format is 32 bits signed integer.


*function*  ``flac_read_s16  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio data. Resulting sample format is 16 bits signed integer.


*function*  ``flac_read_s32  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole flac audio data. Resulting sample format is 32 bits signed integer.


*function*  ``flac_stream_file  (filename: str, frames_to_read: int = 1024) -> Generator[array.array, NoneType, NoneType]``

> Streams the flac audio file as interleaved 16 bit signed integer sample arrays segments.


*function*  ``get_file_info  (filename: str) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio file.


*function*  ``mp3_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio file (mp3 format).


*function*  ``mp3_get_info  (data: bytes) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio data (mp3 format).


*function*  ``mp3_read_f32  (data: bytes, want_nchannels: int = 0, want_sample_rate: int = 0) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole mp3 audio data. Resulting sample format is 32 bits float.


*function*  ``mp3_read_file_f32  (filename: str, want_nchannels: int = 0, want_sample_rate: int = 0) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole mp3 audio file. Resulting sample format is 32 bits float.


*function*  ``mp3_read_file_s16  (filename: str, want_nchannels: int = 0, want_sample_rate: int = 0) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole mp3 audio file. Resulting sample format is 16 bits signed integer.


*function*  ``mp3_read_s16  (data: bytes, want_nchannels: int = 0, want_sample_rate: int = 0) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole mp3 audio data. Resulting sample format is 16 bits signed integer.


*function*  ``mp3_stream_file  (filename: str, frames_to_read: int = 1024, want_nchannels: int = 0, want_sample_rate: int = 0) -> Generator[array.array, NoneType, NoneType]``

> Streams the mp3 audio file as interleaved 16 bit signed integer sample arrays segments.


*function*  ``read_file  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole audio file. Resulting sample format is 16 bits signed integer.


*function*  ``stream_file  (filename: str, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, frames_to_read: int = 1024) -> Generator[array.array, int, NoneType]``

> Convenience generator function to decode and stream any supported audio file as chunks of raw PCM
samples in the chosen format. If you send() a number into the generator rather than just using
next() on it, you'll get that given number of frames, instead of the default configured amount. This
is particularly useful to plug this stream into an audio device callback that wants a variable
number of frames per call.


*function*  ``stream_memory  (data: bytes, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, frames_to_read: int = 1024) -> Generator[array.array, int, NoneType]``

> Convenience generator function to decode and stream any supported audio file in memory as chunks
of raw PCM samples in the chosen format. If you send() a number into the generator rather than just
using next() on it, you'll get that given number of frames, instead of the default configured
amount. This is particularly useful to plug this stream into an audio device callback that wants a
variable number of frames per call.


*function*  ``vorbis_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio file (vorbis format).


*function*  ``vorbis_get_info  (data: bytes) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio data (vorbis format).


*function*  ``vorbis_read  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole vorbis audio data. Resulting sample format is 16 bits signed integer.


*function*  ``vorbis_read_file  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole vorbis audio file. Resulting sample format is 16 bits signed integer.


*function*  ``vorbis_stream_file  (filename: str) -> Generator[array.array, NoneType, NoneType]``

> Streams the ogg vorbis audio file as interleaved 16 bit signed integer sample arrays segments.


*function*  ``wav_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio file (wav format).


*function*  ``wav_get_info  (data: bytes) -> miniaudio.SoundFileInfo``

> Fetch some information about the audio data (wav format).


*function*  ``wav_read_f32  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio data. Resulting sample format is 32 bits float.


*function*  ``wav_read_file_f32  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio file. Resulting sample format is 32 bits float.


*function*  ``wav_read_file_s16  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio file. Resulting sample format is 16 bits signed integer.


*function*  ``wav_read_file_s32  (filename: str) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio file. Resulting sample format is 32 bits signed integer.


*function*  ``wav_read_s16  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio data. Resulting sample format is 16 bits signed integer.


*function*  ``wav_read_s32  (data: bytes) -> miniaudio.DecodedSoundFile``

> Reads and decodes the whole wav audio data. Resulting sample format is 32 bits signed integer.


*function*  ``wav_stream_file  (filename: str, frames_to_read: int = 1024) -> Generator[array.array, NoneType, NoneType]``

> Streams the WAV audio file as interleaved 16 bit signed integer sample arrays segments.


*function*  ``wav_write_file  (filename: str, sound: miniaudio.DecodedSoundFile) ``

> Writes the pcm sound to a WAV file


*enum class*  ``ChannelMixMode``
 names:  ``RECTANGULAR`` ``SIMPLE`` ``CUSTOMWEIGHTS``

> How to mix channels when converting


*enum class*  ``DeviceType``
 names:  ``PLAYBACK`` ``CAPTURE`` ``DUPLEX``

> Type of audio device


*enum class*  ``DitherMode``
 names:  ``NONE`` ``RECTANGLE`` ``TRIANGLE``

> How to dither when converting


*enum class*  ``SampleFormat``
 names:  ``UNKNOWN`` ``UNSIGNED8`` ``SIGNED16`` ``SIGNED24`` ``SIGNED32`` ``FLOAT32``

> Sample format in memory


*class*  ``CaptureDevice``

``CaptureDevice  (self, input_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Union[_cffi_backend.CData, NoneType] = None) ``

> An audio device provided by miniaudio, for audio capture (recording).


> *method*  ``close  (self) ``

> > Halt playback or capture and close down the device.


> *method*  ``start  (self, callback_generator: Generator[NoneType, Union[bytes, array.array], NoneType]) ``

> > Start the audio device: capture (recording) begins. The recorded audio data is sent to the given
callback generator as raw bytes. (it should already be started before)


> *method*  ``stop  (self) ``

> > Halt playback or capture.


*class*  ``DecodeError``

``DecodeError  (self, /, *args, **kwargs)``

> When something went wrong during decoding an audio file.


*class*  ``DecodedSoundFile``

``DecodedSoundFile  (self, name: str, nchannels: int, sample_rate: int, sample_format: miniaudio.SampleFormat, samples: array.array) ``

> Contains various properties and also the raw PCM samples of a fully decoded audio file.


*class*  ``Devices``

``Devices  (self) ``

> Query the audio playback and record devices that miniaudio provides


> *method*  ``get_captures  (self) -> List[Dict[str, Any]]``

> > Get a list of capture devices and some details about them


> *method*  ``get_playbacks  (self) -> List[Dict[str, Any]]``

> > Get a list of playback devices and some details about them


*class*  ``DuplexStream``

``DuplexStream  (self, playback_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, playback_channels: int = 2, capture_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, capture_channels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, playback_device_id: Union[_cffi_backend.CData, NoneType] = None, capture_device_id: Union[_cffi_backend.CData, NoneType] = None) ``

> Joins a capture device and a playback device.


> *method*  ``close  (self) ``

> > Halt playback or capture and close down the device.


> *method*  ``start  (self, callback_generator: Generator[Union[bytes, array.array], Union[bytes, array.array], NoneType]) ``

> > Start the audio device: playback and capture begin. The audio data for playback is provided by
the given callback generator, which is sent the recorded audio data at the same time. (it should
already be started before passing it in)


> *method*  ``stop  (self) ``

> > Halt playback or capture.


*class*  ``MiniaudioError``

``MiniaudioError  (self, /, *args, **kwargs)``

> When a miniaudio specific error occurs.


*class*  ``PlaybackDevice``

``PlaybackDevice  (self, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Union[_cffi_backend.CData, NoneType] = None) ``

> An audio device provided by miniaudio, for audio playback.


> *method*  ``close  (self) ``

> > Halt playback or capture and close down the device.


> *method*  ``start  (self, callback_generator: Generator[Union[bytes, array.array], int, NoneType]) ``

> > Start the audio device: playback begins. The audio data is provided by the given callback
generator. The generator gets sent the required number of frames and should yield the sample data as
raw bytes, a memoryview, an array.array, or as a numpy array with shape (numframes, numchannels).
The generator should already be started before passing it in.


> *method*  ``stop  (self) ``

> > Halt playback or capture.


*class*  ``SoundFileInfo``

``SoundFileInfo  (self, name: str, file_format: str, nchannels: int, sample_rate: int, sample_format: miniaudio.SampleFormat, duration: float, num_frames: int) ``

> Contains various properties of an audio file.


*class*  ``WavFileReadStream``

``WavFileReadStream  (self, pcm_sample_gen: Generator[Union[bytes, array.array], int, NoneType], sample_rate: int, nchannels: int, output_format: miniaudio.SampleFormat, max_frames: int = 0) ``

> An IO stream that reads as a .wav file, and which gets its pcm samples from the provided producer


> *method*  ``close  (self) ``

> > Close the file


> *method*  ``read  (self, amount: int = 9223372036854775807) -> Union[bytes, NoneType]``

> > Read up to the given amount of bytes from the file.



