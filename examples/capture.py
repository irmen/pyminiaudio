"""
Recording audio from a selected input device.
"""

from time import sleep
import miniaudio


def choose_device():
    devices = miniaudio.Devices()
    print("Available recording devices:")
    captures = devices.get_captures()
    for d in enumerate(captures):
        print("{num} = {name}".format(num=d[0], name=d[1]['name']))
    choice = int(input("record from which device? "))
    return captures[choice]


if __name__ == "__main__":
    buffer_chunks = []

    def record_to_buffer():
        _ = yield
        while True:
            data = yield
            print(".", end="", flush=True)
            buffer_chunks.append(data)

    selected_device = choose_device()
    capture = miniaudio.CaptureDevice(buffersize_msec=1000, sample_rate=44100, device_id=selected_device["id"])
    generator = record_to_buffer()
    print("Recording for 5 seconds")
    next(generator)
    capture.start(generator)
    sleep(5)
    capture.stop()

    samples = miniaudio._array_proto_from_format(capture.format)
    for chunk in buffer_chunks:
        samples.extend(chunk)
    sound = miniaudio.DecodedSoundFile('capture', capture.nchannels, capture.sample_rate, capture.format, samples)
    print("\nRecorded sound info:", sound)
    print("Wring to ./capture.wav")
    miniaudio.wav_write_file('capture.wav', sound)
    print("done.")
