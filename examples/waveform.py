"""
Demo: play a generated waveform (sine wave) using miniaudio's waveform generator.
"""

import sys
import miniaudio


def main():
    sample_rate = 44100
    channels = 1
    frequency = 440.0
    waveform_type = miniaudio.WaveformType.SINE

    # optional command line: frequency and waveform type
    if len(sys.argv) > 1:
        frequency = float(sys.argv[1])
    if len(sys.argv) > 2:
        waveform_type = miniaudio.WaveformType[sys.argv[2].upper()]

    output_format = miniaudio.SampleFormat.FLOAT32

    stream = miniaudio.stream_waveform(
        sample_rate=sample_rate,
        channels=channels,
        waveform_type=waveform_type,
        amplitude=0.5,
        frequency=frequency,
        sample_format=output_format,
        frames_to_read=1024,
    )

    with miniaudio.PlaybackDevice(
        output_format=output_format,
        sample_rate=sample_rate,
        nchannels=channels,
    ) as device:
        print("backend:", device.backend)
        print("playing", waveform_type.name, "wave at", frequency, "hz - press Enter to stop")
        device.start(stream)
        input()


if __name__ == "__main__":
    main()