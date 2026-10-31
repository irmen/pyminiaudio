"""
Demo: play a pulse wave while sweeping its duty cycle during playback.
"""

import math
import sys
import threading
import time
import miniaudio


def main():
    sample_rate = 44100
    channels = 1
    frequency = 80.0
    output_format = miniaudio.SampleFormat.FLOAT32

    stream = miniaudio.stream_pulsewave(
        sample_rate=sample_rate,
        channels=channels,
        duty_cycle=0.5,
        amplitude=0.4,
        frequency=frequency,
        sample_format=output_format,
        frames_to_read=256,
    )

    with miniaudio.PlaybackDevice(
        output_format=output_format,
        sample_rate=sample_rate,
        nchannels=channels,
        buffersize_msec=10,
    ) as device:
        print("backend:", device.backend)
        print("playing pulse wave at", frequency, "hz")
        print("sweeping duty cycle - press Enter to stop")
        device.start(stream)

        stop = threading.Event()

        def sweep():
            start = time.monotonic()
            while not stop.is_set():
                t = time.monotonic() - start
                # Smooth sinusoidal sweep of the duty cycle between 0.1 and 0.9.
                duty = 0.5 + 0.48 * math.sin(t * 0.5)
                stream.set_duty_cycle(duty)
                time.sleep(0.01)

        t = threading.Thread(target=sweep, daemon=True)
        t.start()
        try:
            input()
        finally:
            stop.set()
            t.join(timeout=1.0)


if __name__ == "__main__":
    main()
