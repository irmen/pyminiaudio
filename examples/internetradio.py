import miniaudio


if __name__ == "__main__":
    url = input("Enter audio stream URL, or '1' for WUVT-FM 90.7, or '2' for SomaFM GrooveSalad: ")
    if url == "1":
        url = "https://stream.wuvt.vt.edu/wuvt-lb.ogg"
    elif url == "2":
        url = "http://ice5.somafm.com/groovesalad-128-mp3"

    def title_printer(client: miniaudio.IceCastClient, new_title: str) -> None:
        print("Stream title: ", new_title)

    source = miniaudio.IceCastClient(url, update_stream_title=title_printer)
    print("Connected to internet stream, audio format:", source.audio_format.name)
    print("Station name: ", source.station_name)
    print("Station genre: ", source.station_genre)
    print("Press <enter> to quit playing.\n")
    stream = miniaudio.stream_any(source, source.audio_format)
    with miniaudio.PlaybackDevice() as device:
        device.start(stream)
        input()
    source.close()
