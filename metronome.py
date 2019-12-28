from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.graphics import Ellipse, Color, InstructionGroup
from kivy.animation import Animation

from threading import Thread, Event
import time, wave, pyaudio, math




class BeatMarker(InstructionGroup):

    def __init__(self, cx=1, cy=1, r=1, **kwargs):
        super().__init__()
        self.anim_color = Color(0, 1, 0, 0)
        self.anim_circle = Ellipse()
        self.color = Color(1, 1, 1, 0.5)
        self.marker = Ellipse()

        self.add(self.anim_color)
        self.add(self.anim_circle)
        self.add(self.color)
        self.add(self.marker)

        self.pos = cx, cy
        self.size = [2*r, 2*r]

        self.stop_event = Event()

    @property
    def pos(self):
        return self.pos

    @pos.setter
    def pos(self, pos):
        self.anim_circle.pos = pos
        self.marker.pos = pos

    @property
    def size(self):
        return self.size

    @size.setter
    def size(self, size):
        d, d = size
        self.r = d/2
        self.max_rdiff = self.r * 0.1
        self.anim_circle.size = size
        self.marker.size = size

    def animate(self, parent, dur):
        print(f'duation {dur}')
        self._initiate_animation(dur)
        # animation = Animation(duration=dur, s=0)
        # animation.bind(on_progress=print)
        # animation.bind(on_complete=self._end_animation)
        # animation.start(parent)

    def _initiate_animation(self, duration):
        self.anim_color.a = 1
        self.anim_duration = duration
        self.anim_start = time.time()
        thread = Thread(target=self._update_animation, daemon=True)
        thread.start()

    def _update_animation(self, *args):
        while not self.stop_event.is_set():
            progress = (time.time() - self.anim_start) / self.anim_duration
            print(progress)
            if progress > 1:
                self.stop_event.set()
            rdiff = progress * self.max_rdiff
            cx, cy = self.marker.pos
            self.anim_circle.pos = cx - rdiff, cy - rdiff
            self.anim_circle.size = [2 * (self.r + rdiff), 2 * (self.r + rdiff)]
            self.anim_color.a = progress
        self._end_animation()

    def _end_animation(self, *args):
        self.anim_color.a = 0
        self.stop_event.clear()

class BeatBar(FloatLayout):
    num_beats = NumericProperty(4)

    def __init__(self, **kwargs):
        super().__init__()
        self.beatmarkers = InstructionGroup()
        for i in range(self.num_beats):
            beatmarker = BeatMarker()
            self.beatmarkers.add(beatmarker)
        self.canvas.add(self.beatmarkers)

    def on_num_beats(self, instance, num_beats):
        while num_beats > len(self.beatmarkers.children):
            beatmarker = BeatMarker()
            self.beatmarkers.add(beatmarker)
        while num_beats < len(self.beatmarkers.children):
            self.beatmarkers.children.pop()
        self.update_beatmarkers()

    def on_size(self, *args):
        self.update_beatmarkers()

    def update_beatmarkers(self):
        target_ratio = self.num_beats / 1
        aspect_ratio = self.width / self.height
        percent_radius = 0.6  # circle shouldn't take up the whole square
        if aspect_ratio > target_ratio:
            side = self.height
            r = side / 2 * percent_radius
            rdiff = side / 2 - r
            dx = (self.width - (self.num_beats * side)) / 2
            cx, cy = self.x + dx + rdiff, self.y + rdiff
            step_x = side
            for beatmarker in self.beatmarkers.children:
                beatmarker.pos = [cx, cy]
                beatmarker.size = [2*r, 2*r]
                cx += step_x
        else:
            side = self.width / self.num_beats
            r = side / 2 * percent_radius
            rdiff = side / 2 - r
            dy = (self.height - side) / 2
            cx, cy = self.x + rdiff, self.y + dy + rdiff
            step_x = side
            for beatmarker in self.beatmarkers.children:
                beatmarker.pos = [cx, cy]
                beatmarker.size = [2*r, 2*r]
                cx += step_x

class Metronome(FloatLayout):
    needle_angle = NumericProperty(0)
    num_beats = NumericProperty(4)
    bpm = NumericProperty(120)

    def __init__(self, **kwargs):
        self.box = BoxLayout()
        self.beatbar = FloatLayout()
        self.buttonbar = BoxLayout()
        self.max_needle_angle = 35
        # self.bpm = 120
        super().__init__()
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
        beat_num = 0
        beatmarker = self.beatbar.beatmarkers.children[0]
        beat_parity = 1
        start = time.time()
        while not self.stop_event.is_set():
            beats_so_far, t_after_b = divmod(time.time() - start, self.spb)
            progress = t_after_b / self.spb
            if beats_so_far > beat_num:
                beat_num = int(beats_so_far)
                print(beat_num, beats_so_far, progress)
                beat_parity *= -1
                if beat_num % self.time_sig == 0:
                    self.stream.write(self.high_data)
                else:
                    self.stream.write(self.low_data)
                beatmarker.animate(self, self.spb/10)
                beatmarker = self.beatbar.beatmarkers.children[beat_num % self.num_beats]
            self.needle_angle = self.max_needle_angle * math.cos(progress * math.pi) * beat_parity
            self.stop_event.wait(self.spb/200)  # prevents mouse hover from freezing needle (?)
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

    def increment_bpm(self, val):
        print(val)
        self.bpm += val
        print(self.bpm)

class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()

