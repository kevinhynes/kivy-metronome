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
        self.spb = 60 / self.bpm
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

    def play(self, *args):
        thread = Thread(target=self._play, daemon=True)
        thread.start()

    def _play(self, *args):
        '''Update the Metronome's needle angle on every iteration, play beat at appropriate times.

        Since progress goes from 0-1, and beats are being represented by max, min of cos wave,
        we are constantly traversing 0-pi in the wave. Keep track of parity so we know if needle
        angle needs to be negative.
        '''
        t0 = time.time()
        beat_num = 0
        beat_parity = 1
        while not self.stop_event.is_set():
            beats_so_far, t_after_b = divmod(time.time() - t0, self.spb)
            progress = t_after_b / self.spb
            if beats_so_far > beat_num:
                beat_num = beats_so_far
                beat_parity *= -1
                if beat_num % self.time_sig == 0:
                    self.stream.write(self.high_data)
                else:
                    self.stream.write(self.low_data)
            self.needle_angle = self.max_needle_angle * math.cos(progress * math.pi) * beat_parity
            # self.stop_event.wait()
        self.stop_event.clear()

    def stop(self, *args):
        self.stop_event.set()
        self.needle_angle = 0

    def close(self, *args):
        self.stream.close()
        self.player.terminate()


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()

