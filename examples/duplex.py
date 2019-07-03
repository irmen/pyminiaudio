import miniaudio
from time import sleep


def choose_devices():
    devices = miniaudio.Devices()
    print("Available capture devices:")
    captures = devices.get_captures()
    for d in enumerate(captures):
        print("{num} = {name}".format(num=d[0], name=d[1]['name']))
    capture_choice = int(input("record from which device? "))
    print("\nAvailable playback devices:")
    playbacks = devices.get_playbacks()
    for d in enumerate(playbacks):
        print("{num} = {name}".format(num=d[0], name=d[1]['name']))
    playback_choice = int(input("play on which device? "))
    return captures[capture_choice], playbacks[playback_choice]


if __name__ == "__main__":
    def pass_through():
        data = yield b""
        while True:
            print(".", end="", flush=True)
            data = yield data

    capture_dev, playback_dev = choose_devices()
    duplex = miniaudio.DuplexStream(buffersize_msec=0, sample_rate=48000,
                                    playback_device_id=playback_dev["id"], capture_device_id=capture_dev["id"])
    generator = pass_through()
    next(generator)
    print("Starting duplex stream. Press Ctrl + C to exit.")
    duplex.start(generator)

    running = True
    while running:
        try:
            sleep(1)
        except KeyboardInterrupt:
            running = False
    duplex.stop()
