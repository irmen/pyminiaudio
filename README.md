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

## Synthesizer, modplayer?

If you like this library you may also be interested in my [software FM synthesizer](https://pypi.org/project/synthplayer/)
or my [mod player](https://pypi.org/project/libxmplite/) which uses libxmp. 


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


@todo regenerate

