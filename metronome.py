from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty


from threading import Thread, Event
import time, wave, pyaudio, math


class Metronome(FloatLayout):
    needle_angle = NumericProperty(0)

    def __init__(self, **kwargs):
        self.box = BoxLayout()
        self.buttonbar = BoxLayout()
        self.max_needle_angle = 35
        super().__init__()
        self.bpm = 200
        self.spb = 60 / self.bpm
        self.time_sig = 4
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

    def play(self, *args):
        thread = Thread(target=self._play, daemon=True)
        thread.start()

    def _play(self, *args):
        '''Update the Metronome's needle angle on every iteration, play beat at appropriate times.

        Since progress goes from 0-1, and beats are being represented by max, min of cos wave,
        we are constantly traversing 0-pi in the wave. Keep track of parity so we know if needle
        angle needs to be negative.
        '''
        testmax = 0
        beat_num = 0
        beat_parity = 1
        start = time.time()
        while not self.stop_event.is_set():
            beats_so_far, t_after_b = divmod(time.time() - start, self.spb)
            progress = t_after_b / self.spb
            if beats_so_far > beat_num:
                beat_num = beats_so_far
                beat_parity *= -1
                if beat_num % self.time_sig == 0:
                    self.stream.write(self.high_data)
                else:
                    self.stream.write(self.low_data)
            self.needle_angle = self.max_needle_angle * math.cos(progress * math.pi) * beat_parity
            self.stop_event.wait(self.spb/50)  # prevents mouse hover from freezing needle
        self.stop_event.clear()

    def stop(self, *args):
        self.stop_event.set()
        self.needle_angle = 0

    def close(self, *args):
        self.stream.close()
        self.player.terminate()

    def on_size(self, *args):
        target_ratio = 1
        width, height = self.size
        if width / height > target_ratio:
            self.box.height = height
            self.box.width = target_ratio * height
        else:
            self.box.width = width
            self.box.height = width / target_ratio

class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()

