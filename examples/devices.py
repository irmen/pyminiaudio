import miniaudio

devices = miniaudio.Devices(backends=[])
print("Backend: {}".format(devices.backend))

out_devices = devices.get_playbacks()
print("\nPlayback Devices:")
for device in out_devices:
    print(device)

in_devices = devices.get_captures()
print("\nCapture Devices:")
for device in in_devices:
    print(device)
