from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from kivy.animation import Animation


from threading import Thread, Event
import time, wave, pyaudio, math


class Metronome(FloatLayout):
    needle_angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__()
        self.bpm = 120
        self.spb = (self.bpm / 60) ** -1
        self.time_sig = 4
        self.max_needle_angle = 50
        self.stop_event = Event()
        self.accent_file = "./sounds/metronome-klack.wav"
        self.beat_file = "./sounds/metronome-click.wav"

        self.player = pyaudio.PyAudio()
        high = wave.open(self.accent_file, "rb")
        low = wave.open(self.beat_file, "rb")
        self.high_data = high.readframes(2048)
        self.low_data = low.readframes(2048)
        self.stream = self.player.open(
            format=self.player.get_format_from_width(high.getsampwidth()),
            channels=high.getnchannels(),
            rate=high.getframerate(),
            output=True)

        self.anim = Animation(duration=self.spb) + Animation(duration=self.spb)
        self.anim.repeat = True
        self.anim.bind(on_progress=self.custom_transition)

    def play(self, *args):
        thread = Thread(target=self._play, daemon=True)
        thread.start()

    def _play(self, *args):
        goal = time.time()
        i = 0
        self.anim.start(self)
        while not self.stop_event.is_set():
            if i == self.time_sig - 1:
                print(time.time() - goal)
                self.stream.write(self.high_data)
            else:
                print(time.time() - goal)
                self.stream.write(self.low_data)
            goal += self.spb
            i = (i + 1) % self.time_sig
            self.stop_event.wait(goal - time.time())
        self.stop_event.clear()

    def stop(self, *args):
        self.stop_event.set()
        self.needle_angle = 0
        self.anim.cancel(self)

    def close(self, *args):
        self.stream.close()
        self.player.terminate()

    def custom_transition(self, w, a, progress):
        self.needle_angle = self.max_needle_angle * math.cos(2*math.pi*progress)


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()

