from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from threading import Thread, Event

import time


class Metronome(FloatLayout):
    click = SoundLoader.load("./sounds/Clap-1.wav")

    def __init__(self, **kwargs):
        super().__init__()
        self.starttime = time.time()
        self.stopped = Event()
        self.thread = Thread(target=self.play, daemon=True)
        self.interval = 0.5
        self.thread.start()

    def play(self):
        while not self.stopped.wait(self.interval - (time.time() - self.starttime) % self.interval):
            if self.click.state == "play":
                print("stopped")
                self.click.stop()
            print(self.interval - (time.time() - self.starttime) % self.interval)  # should be 0
            Clock.schedule_once(self.click.play, -1)
    #
    # def _play(self, *args):
    #     self.click.play()

    def stop(self):
        self.stopped.set()


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()