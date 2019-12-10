from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from threading import Thread, Event

import numpy as np
import time, scipy.io.wavfile as wavfile
import subprocess


class Metronome(FloatLayout):
    click = SoundLoader.load("./sounds/Clap-1.wav")

    def __init__(self, **kwargs):
        super().__init__()
        self.starttime = time.time()
        self.stopped = Event()
        self.thread = Thread(target=self.play, daemon=True)
        self.interval = 0.75
        # read_rate, read_data = wavfile.read("./sounds/Clap-1.wav")
        read_data = [[1, 1] for channel_sample in range(10000)]
        rest = [[0, 0] for channel_sample in read_data]
        write_data = read_data + rest + read_data + rest + read_data + rest + read_data + rest
        wav_write = wavfile.write("sound.wav", 44100, np.array(write_data, dtype="float32"))

        self.sound = SoundLoader.load("sound.wav")
        self.sound.loop = True
        # self.sound.play()
        # self.thread.start()
        completed = subprocess.run(["ffplay/bin/ffplay.exe", "-loop", "0", "-nodisp", "sound.wav"])

    def play(self):
        while not self.stopped.wait(self.interval - (time.time() - self.starttime) % self.interval):
            if self.click.state == "play":
                print("stopped")
                self.click.stop()
            print(self.interval - (time.time() - self.starttime) % self.interval)  # should be 0
            self.sound.play()

    def stop(self):
        self.stopped.set()


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()