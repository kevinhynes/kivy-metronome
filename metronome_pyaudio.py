from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from threading import Thread, Event

import time, wave, pyaudio


class Metronome(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__()
        self.bpm = 120
        self.spb = (self.bpm/60) ** -1
        self.time_sig = 4
        self.accent_file = "./sounds/metronome-klack.wav"
        self.beat_file = "./sounds/metronome-click.wav"
        self.stop_event = Event()

        # Prepare sound files
        self.p = pyaudio.PyAudio()
        high = wave.open(self.accent_file, "rb")
        low = wave.open(self.beat_file, "rb")
        self.high_data = high.readframes(2048)
        self.low_data = low.readframes(2048)
        self.stream = self.p.open(format=self.p.get_format_from_width(high.getsampwidth()),
                                  channels=high.getnchannels(),
                                  rate=high.getframerate(),
                                  output=True)

        self.add_widget(Button(text="play", on_press=self.play))
        self.add_widget(Button(text="stop", on_press=self.stop))

    def play(self, *args):
        goal = time.time()
        i = 0
        while not self.stop_event.is_set():
            if i == self.time_sig - 1:
                self.stream.write(self.high_data)
            else:
                self.stream.write(self.low_data)
            goal += self.spb
            i = (i + 1) % self.time_sig
            self.stop_event.wait(goal - time.time())
            # time.sleep(goal - time.time())
        self.stop_evnet.clear()

    def stop(self, *args):
        self.stop_event.set()


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()