[![Latest Version](https://img.shields.io/pypi/v/miniaudio.svg)](https://pypi.python.org/pypi/miniaudio/)


# Python miniaudio

Multiplatform audio playback, recording, decoding and sample format conversion for
Linux (including Raspberri Pi), Windows, Mac and others.

Installation for most users: via [Pypi](https://pypi.org/project/miniaudio/), Raspberri Pi builds via [PiWheels](https://www.piwheels.org/project/miniaudio/).


This is a Pythonic interface to the cross-platform [miniaudio](https://github.com/dr-soft/miniaudio/) C library:

- audio operations run in the background
- python bindings for most of the functions offered in the miniaudio library:
  - reading and decoding audio files
  - getting audio file properties (such as duration, number of channels, sample rate)
  - converting sample formats and frequencies
  - streaming large audio files
  - audio playback
  - audio recording
- decoders for wav, flac, vorbis and mp3
- Audio file and Icecast internet radio streaming
- Python enums instead of just some integers for special values
- several classes to represent the main functions of the library
- generators for the Audio playback and recording
- sample data is usually in the form of a Python ``array`` with appropriately sized elements
  depending on the sample width (rather than a raw block of bytes)
- TODO: filters, waveform generators?


*Requires Python 3.6 or newer.  Also works on pypy3 (because it uses cffi).*

Software license for these Python bindings, miniaudio and the decoders: MIT

## Synthesizer, modplayer?

If you like this library you may also be interested in my [software FM synthesizer](https://pypi.org/project/synthplayer/)
or my [mod player](https://pypi.org/project/libxmplite/) which uses libxmp.


## Examples

### Most basic audio file playback

```python
import miniaudio
stream = miniaudio.stream_file("samples/music.mp3")
with miniaudio.PlaybackDevice() as device:
    device.start(stream)
    input("Audio file playing in the background. Enter to stop playback: ")
```

### Playback of an unsupported file format

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

with miniaudio.PlaybackDevice(output_format=miniaudio.SampleFormat.SIGNED16,
                              nchannels=channels, sample_rate=sample_rate) as device:
    ffmpeg = subprocess.Popen(["ffmpeg", "-v", "fatal", "-hide_banner", "-nostdin",
                               "-i", filename, "-f", "s16le", "-acodec", "pcm_s16le",
                               "-ac", str(channels), "-ar", str(sample_rate), "-"],
                              stdin=None, stdout=subprocess.PIPE)
    stream = stream_pcm(ffmpeg.stdout)
    next(stream)  # start the generator
    device.start(stream)
    input("Audio file playing in the background. Enter to stop playback: ")
    ffmpeg.terminate()
```

## API


*enum class*  ``Backend``
 names:  ``WASAPI`` ``DSOUND`` ``WINMM`` ``COREAUDIO`` ``SNDIO`` ``AUDIO4`` ``OSS`` ``PULSEAUDIO`` ``ALSA`` ``JACK`` ``AAUDIO`` ``OPENSL`` ``WEBAUDIO`` ``CUSTOM`` ``NULL``
> Operating system audio backend to use (only a subset will be available)


*enum class*  ``ChannelMixMode``
 names:  ``RECTANGULAR`` ``SIMPLE`` ``CUSTOMWEIGHTS``
> How to mix channels when converting


*enum class*  ``DeviceType``
 names:  ``PLAYBACK`` ``CAPTURE`` ``DUPLEX``
> Type of audio device


*enum class*  ``DitherMode``
 names:  ``NONE`` ``RECTANGLE`` ``TRIANGLE``
> How to dither when converting


*enum class*  ``FileFormat``
 names:  ``UNKNOWN`` ``WAV`` ``FLAC`` ``MP3`` ``VORBIS``
> Audio file format


*enum class*  ``SampleFormat``
 names:  ``UNKNOWN`` ``UNSIGNED8`` ``SIGNED16`` ``SIGNED24`` ``SIGNED32`` ``FLOAT32``
> Sample format in memory


*enum class*  ``SeekOrigin``
 names:  ``START`` ``CURRENT``
> How to seek() in a source


*enum class*  ``ThreadPriority``
 names:  ``IDLE`` ``LOWEST`` ``LOW`` ``NORMAL`` ``HIGH`` ``HIGHEST`` ``REALTIME``
> The priority of the worker thread (default=HIGHEST)


*function*  ``convert_frames  (from_fmt: miniaudio.SampleFormat, from_numchannels: int, from_samplerate: int, sourcedata: bytes, to_fmt: miniaudio.SampleFormat, to_numchannels: int, to_samplerate: int) -> bytearray``
> Convert audio frames in source sample format with a certain number of channels, to another sample
format and possibly down/upmixing the number of channels as well.


*function*  ``convert_sample_format  (from_fmt: miniaudio.SampleFormat, sourcedata: bytes, to_fmt: miniaudio.SampleFormat, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>) -> bytearray``
> Convert a raw buffer of pcm samples to another sample format. The result is returned as another
raw pcm sample buffer


*function*  ``decode  (data: bytes, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>) -> miniaudio.DecodedSoundFile``
> Convenience function to decode any supported audio file in memory to raw PCM samples in your
chosen format.


*function*  ``decode_file  (filename: str, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>) -> miniaudio.DecodedSoundFile``
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


*function*  ``flac_stream_file  (filename: str, frames_to_read: int = 1024, seek_frame: int = 0) -> Generator[array.array, NoneType, NoneType]``
> Streams the flac audio file as interleaved 16 bit signed integer sample arrays segments. This uses
a fixed chunk size and cannot be used as a generic miniaudio decoder input stream. Consider using
stream_file() instead.


*function*  ``get_enabled_backends  () -> Set[miniaudio.Backend]``
> Returns the set of available backends by the compilation environment for the underlying miniaudio
C library


*function*  ``get_file_info  (filename: str) -> miniaudio.SoundFileInfo``
> Fetch some information about the audio file.


*function*  ``is_backend_enabled  (backend: miniaudio.Backend) -> bool``
> Determines whether or not the given backend is available by the compilation environment for the
underlying miniaudio C library


*function*  ``is_loopback_supported  (backend: miniaudio.Backend) -> bool``
> Determines whether or not loopback mode is support by a backend.


*function*  ``lib_version  () -> str``
> Returns the version string of the underlying miniaudio C library


*function*  ``mp3_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``
> Fetch some information about the audio file (mp3 format).


*function*  ``mp3_get_info  (data: bytes) -> miniaudio.SoundFileInfo``
> Fetch some information about the audio data (mp3 format).


*function*  ``mp3_read_f32  (data: bytes) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole mp3 audio data. Resulting sample format is 32 bits float.


*function*  ``mp3_read_file_f32  (filename: str) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole mp3 audio file. Resulting sample format is 32 bits float.


*function*  ``mp3_read_file_s16  (filename: str) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole mp3 audio file. Resulting sample format is 16 bits signed integer.


*function*  ``mp3_read_s16  (data: bytes) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole mp3 audio data. Resulting sample format is 16 bits signed integer.


*function*  ``mp3_stream_file  (filename: str, frames_to_read: int = 1024, seek_frame: int = 0) -> Generator[array.array, NoneType, NoneType]``
> Streams the mp3 audio file as interleaved 16 bit signed integer sample arrays segments. This uses
a fixed chunk size and cannot be used as a generic miniaudio decoder input stream. Consider using
stream_file() instead.


*function*  ``read_file  (filename: str, convert_to_16bit: bool = False) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole audio file. Miniaudio will attempt to return the sound data in exactly
the same format as in the file. Unless you set convert_convert_to_16bit to True, then the result is
always a 16 bit sample format.


*function*  ``stream_any  (source: miniaudio.StreamableSource, source_format: miniaudio.FileFormat = <FileFormat.UNKNOWN: 0>, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, frames_to_read: int = 1024, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>, seek_frame: int = 0) -> Generator[array.array, int, NoneType]``
> Convenience function that returns a generator to decode and stream any source of encoded audio
data (such as a network stream). Stream result is chunks of raw PCM samples in the chosen format. If
you send() a number into the generator rather than just using next() on it, you'll get that given
number of frames, instead of the default configured amount. This is particularly useful to plug this
stream into an audio device callback that wants a variable number of frames per call.


*function*  ``stream_file  (filename: str, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, frames_to_read: int = 1024, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>, seek_frame: int = 0) -> Generator[array.array, int, NoneType]``
> Convenience generator function to decode and stream any supported audio file as chunks of raw PCM
samples in the chosen format. If you send() a number into the generator rather than just using
next() on it, you'll get that given number of frames, instead of the default configured amount. This
is particularly useful to plug this stream into an audio device callback that wants a variable
number of frames per call.


*function*  ``stream_memory  (data: bytes, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, frames_to_read: int = 1024, dither: miniaudio.DitherMode = <DitherMode.NONE: 0>) -> Generator[array.array, int, NoneType]``
> Convenience generator function to decode and stream any supported audio file in memory as chunks
of raw PCM samples in the chosen format. If you send() a number into the generator rather than just
using next() on it, you'll get that given number of frames, instead of the default configured
amount. This is particularly useful to plug this stream into an audio device callback that wants a
variable number of frames per call.


*function*  ``stream_raw_pcm_memory  (pcmdata: Union[array.array, memoryview, bytes], nchannels: int, sample_width: int, frames_to_read: int = 4096) -> Generator[Union[bytes, array.array], int, NoneType]``
> Convenience generator function to stream raw pcm audio data from memory. Usually you don't need to
use this as the library provides many other streaming options that work on much smaller, encoded,
audio data. However, in the odd case that you only have already decoded raw pcm data you can use
this generator as a stream source.  The data can be provided in ``array`` type or ``bytes``,
``memoryview`` or even a numpy array. Be sure to also specify the correct number of channels that
the audio data has, and the sample with in bytes.


*function*  ``stream_with_callbacks  (sample_stream: Generator[Union[bytes, array.array], int, NoneType], progress_callback: Optional[Callable[[int], NoneType]] = None, frame_process_method: Union[Callable[[array.array], array.array], None] = None, end_callback: Optional[Callable] = None) -> Generator[Union[bytes, array.array], int, NoneType]``
> Convenience generator function to add callback and processing functionality to another stream. You can specify:
A callback function that gets called during play and takes an ``int``
for the number of frames played.
A function that can be used to process raw data frames before they are yielded back
(takes an ``array.array`` and returns an ``array.array``)
*Note: if the processing method is slow it will result in audio glitchiness*
A callback function that gets called when the stream ends playing.


*function*  ``vorbis_get_file_info  (filename: str) -> miniaudio.SoundFileInfo``
> Fetch some information about the audio file (vorbis format).


*function*  ``vorbis_get_info  (data: bytes) -> miniaudio.SoundFileInfo``
> Fetch some information about the audio data (vorbis format).


*function*  ``vorbis_read  (data: bytes) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole vorbis audio data. Resulting sample format is 16 bits signed integer.


*function*  ``vorbis_read_file  (filename: str) -> miniaudio.DecodedSoundFile``
> Reads and decodes the whole vorbis audio file. Resulting sample format is 16 bits signed integer.


*function*  ``vorbis_stream_file  (filename: str, seek_frame: int = 0) -> Generator[array.array, NoneType, NoneType]``
> Streams the ogg vorbis audio file as interleaved 16 bit signed integer sample arrays segments.
This uses a variable unconfigurable chunk size and cannot be used as a generic miniaudio decoder
input stream. Consider using stream_file() instead.


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


*function*  ``wav_stream_file  (filename: str, frames_to_read: int = 1024, seek_frame: int = 0) -> Generator[array.array, NoneType, NoneType]``
> Streams the WAV audio file as interleaved 16 bit signed integer sample arrays segments. This uses
a fixed chunk size and cannot be used as a generic miniaudio decoder input stream. Consider using
stream_file() instead.


*function*  ``wav_write_file  (filename: str, sound: miniaudio.DecodedSoundFile) ``
> Writes the pcm sound to a WAV file


*function*  ``width_from_format  (sampleformat: miniaudio.SampleFormat) -> int``
> returns the sample width in bytes, of the given sample format.


*class*  ``CaptureDevice``

``CaptureDevice  (self, input_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Optional[_cffi_backend._CDataBase] = None, callback_periods: int = 0, backends: Optional[List[miniaudio.Backend]] = None, thread_prio: miniaudio.ThreadPriority = <ThreadPriority.HIGHEST: 0>, app_name: str = '') ``
> An audio device provided by miniaudio, for audio capture (recording).

> *field* ``buffersize_msec``
> > The size of the audio buffer being held in this capture device.

> *field* ``callback_generator``
> > A callback generator to provide the audio data to. The callback generator should provide the
number of samples it wants to receive, and will receive a ``bytearray`` containing the sample data
for that number of samples.

> *field* ``format``
> > The sample format this capture device produces.

> *field* ``nchannels``
> > The number of audio channels this capture device produces.

> *field* ``running``
> > Whether the device is currently capturing (has been started).

> *field* ``sample_rate``
> > The number of samples this capture device produces per second.

> *field* ``sample_width``
> > The sample width in bytes that this capture device produces.

> *method*  ``close  (self) ``
> > Halt playback or capture and close down the device. If you use the device as a context manager,
it will be closed automatically.

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
> Contains various properties and also the PCM frames of a fully decoded audio file.

> *field* ``duration``
> > The duration of the audio in this file if played back at normal rate, in seconds (as ``float``).

> *field* ``name``
> > The path to the file that was decoded.

> *field* ``nchannels``
> > The number of audio channels that this file contains.

> *field* ``num_frames``
> > The total number of frames contained in this file.

> *field* ``sample_format``
> > The sample format that this file was decoded to, as a ``SampleFormat`` enum.

> *field* ``sample_format_name``
> > A human-readable name for the ``sample_format`` field, as a string.

> *field* ``sample_rate``
> > The number of samples that should be played per second to play this file back at normal rate.

> *field* ``sample_width``
> > The width of the samples that this file was decoded to, in bytes.

> *field* ``samples``
> > The sample data contained in this sound file, as an array of bytes.


*class*  ``Devices``

``Devices  (self, backends: Optional[List[miniaudio.Backend]] = None) ``
> Query the audio playback and record devices that miniaudio provides

> *field* ``backend``
> > The audio back-end currently being used to record and/or playback audio through the system.

> *method*  ``get_captures  (self) -> List[Dict[str, Any]]``
> > Get a list of capture devices and some details about them

> *method*  ``get_playbacks  (self) -> List[Dict[str, Any]]``
> > Get a list of playback devices and some details about them


*class*  ``DuplexStream``

``DuplexStream  (self, playback_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, playback_channels: int = 2, capture_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, capture_channels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, playback_device_id: Optional[_cffi_backend._CDataBase] = None, capture_device_id: Optional[_cffi_backend._CDataBase] = None, callback_periods: int = 0, backends: Optional[List[miniaudio.Backend]] = None, thread_prio: miniaudio.ThreadPriority = <ThreadPriority.HIGHEST: 0>, app_name: str = '') ``
> Joins a capture device and a playback device.

> *field* ``backend``
> > The name of the audio back-end to use for capturing of playing audio through the system.

> *field* ``buffersize_msec``
> > The size of the audio buffers to use for capturing and playing audio, in milliseconds of
playback.

> *field* ``callback_generator``
> > A callback generator to provide the captured audio data to. The callback generator should
provide the number of samples it wants to receive, and will receive a ``bytearray`` containing the
sample data for that number of samples.

> *field* ``capture_channels``
> > The number of channels to be used for recording audio.

> *field* ``capture_format``
> > The sample format to be used for recording audio.

> *field* ``playback_channels``
> > The number of channels to be used for playing audio.

> *field* ``playback_format``
> > The sample format to be used for playing audio.

> *field* ``running``
> > Whether the device is currently capturing and/or playing (has been started).

> *field* ``sample_rate``
> > The number of samples to capture and playback per second.

> *field* ``sample_width``
> > The width of samples to be used for recording audio, in bytes.

> *method*  ``close  (self) ``
> > Halt playback or capture and close down the device. If you use the device as a context manager,
it will be closed automatically.

> *method*  ``start  (self, callback_generator: Generator[Union[bytes, array.array], Union[bytes, array.array], NoneType]) ``
> > Start the audio device: playback and capture begin. The audio data for playback is provided by
the given callback generator, which is sent the recorded audio data at the same time. (it should
already be started before passing it in)

> *method*  ``stop  (self) ``
> > Halt playback or capture.


*class*  ``IceCastClient``

``IceCastClient  (self, url: str, update_stream_title: Callable[[ForwardRef('IceCastClient'), str], NoneType] = None) ``
> A simple client for IceCast audio streams as miniaudio streamable source. If the stream has Icy
Meta Data, the stream_title attribute will be updated with the actual title taken from the meta
data. You can also provide a callback to be called when a new stream title is available. The
downloading of the data from the internet is done in a background thread and it tries to keep a
(small) buffer filled with available data to read.

> *field* ``audio_info``
> > A string of audio info provided by this station, containing e.g. its sample rate, audio quality
and number of channels.

> *field* ``audio_format``
> > The file format that this station streams.

> *field* ``station_genre``
> > The musical genre that this station plays.

> *field* ``station_name``
> > The name of this station.

> *field* ``stream_title``
> > The title of the currently playing track.

> *field* ``url``
> > The URL to the currently playing stream.

> *method*  ``close  (self) ``
> > Stop the stream, aborting the background downloading.

> *method*  ``read  (self, num_bytes: int) -> bytes``
> > Read a chunk of data from the stream.

> *method*  ``seek  (self, offset: int, origin: miniaudio.SeekOrigin) -> bool``
> > Override this if the stream supports seeking. Note: seek support is sometimes not needed if you
give the file type to a decoder upfront. You can ignore this method then.


*class*  ``MiniaudioError``

``MiniaudioError  (self, /, *args, **kwargs)``
> When a miniaudio specific error occurs.


*class*  ``PlaybackDevice``

``PlaybackDevice  (self, output_format: miniaudio.SampleFormat = <SampleFormat.SIGNED16: 2>, nchannels: int = 2, sample_rate: int = 44100, buffersize_msec: int = 200, device_id: Optional[_cffi_backend._CDataBase] = None, callback_periods: int = 0, backends: Optional[List[miniaudio.Backend]] = None, thread_prio: miniaudio.ThreadPriority = <ThreadPriority.HIGHEST: 0>, app_name: str = '') ``
> An audio device provided by miniaudio, for audio playback.

> *field* ``backend``
> > The audio back-end that is used to play audio through the system.

> *field* ``buffersize_msec``
> > The length of the audio buffer to hold in this device, in milliseconds.

> *field* ``callback_generator``
> > An optional callback generator to get audio data from. The audio data is provided by this
callback generator. The generator gets sent the required number of frames and should yield the
sample data as raw ``bytes``, a ``memoryview``, an ``array.array``, or as a numpy array with shape
``(numframes, numchannels)``. The generator should already be started before setting it here.

> *field* ``format``
> > The sample format to play audio at.

> *field* ``nchannels``
> > The number of audio channels to play audio at.

> *field* ``running``
> > Whether audio is currently being played.

> *field* ``sample_rate``
> > The number of samples to play per second.

> *field* ``sample_width``
> > The width of the samples to play audio at, in bytes.

> *method*  ``close  (self) ``
> > Halt playback or capture and close down the device. If you use the device as a context manager,
it will be closed automatically.

> *method*  ``start  (self, callback_generator: Generator[Union[bytes, array.array], int, NoneType]) ``
> > Start the audio device: playback begins. The audio data is provided by the given callback
generator. The generator gets sent the required number of frames and should yield the sample data as
raw bytes, a memoryview, an array.array, or as a numpy array with shape (numframes, numchannels).
The generator should already be started before passing it in.

> *method*  ``stop  (self) ``
> > Halt playback or capture.


*class*  ``SoundFileInfo``

``SoundFileInfo  (self, name: str, file_format: miniaudio.FileFormat, nchannels: int, sample_rate: int, sample_format: miniaudio.SampleFormat, duration: float, num_frames: int) ``
> Contains various properties of an audio file.

> *field* ``duration``
> > The duration of the audio in this file if played back at normal rate, in seconds (as ``float``).

> *field* ``name``
> > The path to the file.

> *field* ``nchannels``
> > The number of audio channels that this file contains.

> *field* ``num_frames``
> > The total number of frames contained in this file.

> *field* ``sample_format``
> > The sample format contained in this file, as a ``SampleFormat`` enum.

> *field* ``sample_format_name``
> > A human-readable name for the ``sample_format`` field, as a string.

> *field* ``sample_rate``
> > The number of samples that should be played per second to play this file back at normal rate.

> *field* ``sample_width``
> > The width of the samples contained in this file, in bytes.


*class*  ``StreamableSource``

``StreamableSource  (self, /, *args, **kwargs)``
> Base class for streams of audio data bytes. Can be used as a contextmanager, to properly call
close().

> *method*  ``close  (self) ``
> > Override this to properly close the stream and free resources.

> *method*  ``read  (self, num_bytes: int) -> Union[bytes, memoryview]``
> > override this to provide data bytes to the consumer of the stream

> *method*  ``seek  (self, offset: int, origin: miniaudio.SeekOrigin) -> bool``
> > Override this if the stream supports seeking. Note: seek support is sometimes not needed if you
give the file type to a decoder upfront. You can ignore this method then.


*class*  ``WavFileReadStream``

``WavFileReadStream  (self, pcm_sample_gen: Generator[Union[bytes, array.array], int, NoneType], sample_rate: int, nchannels: int, output_format: miniaudio.SampleFormat, max_frames: int = 0) ``
> An IO stream that reads as a .wav file, and which gets its pcm samples from the provided producer

> *field* ``buffered``
> > The current samples in the buffer, as the stream is streaming, as raw ``bytes``.

> *field* ``bytes_done``
> > The number of bytes that have been streamed so far.

> *field* ``format``
> > The sample format provided by this stream.

> *field* ``max_bytes``
> > The maximum size of the buffer kept for this stream, in bytes.

> *field* ``max_frames``
> > The maximum number of frames to keep in the buffer for this stream.

> *field* ``nchannels``
> > The number of channels provided by this stream.

> *field* ``sample_gen``
> > A generator used to provide samples to this stream.

> *field* ``sample_rate``
> > The sample rate provided by this stream.

> *field* ``sample_width``
> > The width of the samples provided by this stream.

> *method*  ``close  (self) ``
> > Close the file

> *method*  ``read  (self, amount: int = 9223372036854775807) -> Optional[bytes]``
> > Read up to the given amount of bytes from the file.



