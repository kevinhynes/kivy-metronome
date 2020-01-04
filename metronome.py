from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.graphics import Ellipse, Color, InstructionGroup
from kivy.animation import Animation


from threading import Thread, Event
import time, wave, pyaudio, math







class TitleBar(BoxLayout):

    def validate_text(self, text):
        bpm = ""
        i = 0
        while i < len(text) and text[i].isdigit():
            bpm += text[i]
            i += 1
        if bpm and 1 <= int(bpm) <= 300:
            bpm = int(bpm)
            if bpm == self.metronome.bpm:
                self.metronome.bpm += 1
                self.metronome.bpm -= 1
            else:
                self.metronome.bpm = bpm
        else:
            # Bpm entered was invalid.  Just change it & change it back to update the text.
            self.metronome.bpm += 1
            self.metronome.bpm -= 1


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
        self.max_rdiff = self.r * 0.2
        self.anim_circle.size = size
        self.marker.size = size

    def animate(self, parent, dur):
        spb = parent.spb
        self._initiate_animation(spb, dur)
        # Binding to the animation.on_progress event only firing twice?  Going custom instead..
        # animation = Animation(duration=dur, s=0)
        # animation.bind(on_progress=print)
        # animation.bind(on_complete=self._end_animation)
        # animation.start(parent)

    def _initiate_animation(self, spb, duration):
        self.anim_color.a = 1
        self.anim_duration = duration
        self.anim_start = time.time()
        self._update_animation(spb)

    def _update_animation(self, spb, *args):
        while not self.stop_event.is_set():
            progress = (time.time() - self.anim_start) / self.anim_duration
            if progress > 1:
                self.stop_event.set()
                progress = 0
            rdiff = progress * self.max_rdiff
            cx, cy = self.marker.pos
            self.anim_circle.pos = cx - rdiff, cy - rdiff
            self.anim_circle.size = [2 * (self.r + rdiff), 2 * (self.r + rdiff)]
            self.anim_color.a = progress
            # self.stop_event.wait(spb/100000)  # stops markers from freezing on hover?
        self._end_animation()

    def _end_animation(self, *args):
        self.anim_color.a = 0
        cx, cy = self.marker.pos
        d, d = self.marker.size
        self.anim_circle.pos = cx, cy
        self.anim_circle.size = d, d
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


############################################################################################
# Playing with some sound stuff here...
# Combination of NumPy and SciPy to write a sin wave .wav file.
# https://www.youtube.com/watch?v=lbV2SoeAggU nightstatic
import numpy as np
from scipy.io import wavfile
sps = 44100
freq_hz = 660.0
duration_s = 0.01
each_sample_number = np.arange(duration_s * sps)
waveform = np.sin(2 * np.pi * each_sample_number * freq_hz / sps)
waveform_quiet = waveform * 0.3
waveform_integers = np.int16(waveform_quiet * 32767)
# Write the .wav file
wavfile.write('sine.wav', sps, waveform_integers)

# simpleaudio can play NumPy arrays directly.
import simpleaudio as sa
# Start playback
play_obj = sa.play_buffer(waveform_integers, 1, 2, sps)
# Wait for playback to finish before exiting
play_obj.wait_done()
############################################################################################


class Metronome(FloatLayout):
    needle_angle = NumericProperty(0)
    num_beats = NumericProperty(4)
    bpm = NumericProperty(200)

    def __init__(self, **kwargs):
        self.box = BoxLayout()
        self.beatbar = FloatLayout()
        self.buttonbar = BoxLayout()
        self.max_needle_angle = 30
        super().__init__()
        self.spb = 60 / self.bpm
        self.time_sig = 4
        self.stop_event = Event()

        self.accent_file = "./sounds/metronome-klack.wav"  # Downloaded real metronome sound
        self.beat_file = "./sounds/metronome-click.wav"    # Downloaded real metronome sound
        self.sine_file = "./sine.wav"                      # Written from NumPy array

        self.player = pyaudio.PyAudio()
        accent = wave.open(self.accent_file, "rb")
        beat = wave.open(self.beat_file, "rb")
        sine = wave.open(self.sine_file, "rb")
        self.accent_data = accent.readframes(2048)
        self.beat_data = beat.readframes(2048)
        self.sine_data = sine.readframes(2048)
        self.stream = self.player.open(
            format=self.player.get_format_from_width(accent.getsampwidth()),
            channels=accent.getnchannels(),
            rate=accent.getframerate(),
            output=True)

        self.is_active = False

    def play(self, *args):
        if not self.is_active:
            self.is_active = True
            thread = Thread(target=self._play, daemon=True)
            thread.start()

    def _play(self, *args):
        '''Update the Metronome's needle angle on every iteration, play beat at appropriate times.

        Since progress goes from 0-1, and beats are being represented by max & min of cos wave,
        we are constantly traversing 0-pi in the wave which would only move the needle from left
        to right.  Keep track of beat_parity so we know if we should go right to left.
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
                beat_parity *= -1
                # [1] Use wave and pyaudio modules to play chunk of real metronome .wav file.
                # Works, but 1) imperfect timing due to using a real sound sample and 2) sound
                # played is somehow not the same everytime - tends to change slightly.
                self.stream.write(self.accent_data)


                # [2] Use simpleaudio to play NumPy array directly.
                # Works, but prevents metronome needle from moving smoothly regardless of using wait_done().
                # Works well with duration_s = 0.01 above.
                # play_obj = sa.play_buffer(waveform_integers, 1, 2, sps)
                # play_obj.wait_done()

                # [3] Use SciPy to write NumPy array to .wav file, wave to open and read, pyaudio to play.
                # Does not work correctly at all.  Changes to duration_s above affect it.
                # self.stream.write(self.sine_data)

                beatmarker.animate(self, 0.1)
                beatmarker = self.beatbar.beatmarkers.children[beat_num % self.num_beats]
            self.needle_angle = self.max_needle_angle * math.cos(progress * math.pi) * beat_parity
            self.stop_event.wait(self.spb/10000)  # prevents mouse hover from freezing needle (?)
        self.stop_event.clear()

    def stop(self, *args):
        if self.is_active:
            self.is_active = False
            self.needle_angle = 0
            self.stop_event.set()
            for beatmarker in self.beatbar.beatmarkers.children:
                beatmarker.stop_event.set()

    def close(self, *args):
        self.stream.close()
        self.player.terminate()

    def on_size(self, *args):
        target_ratio = 0.75
        width, height = self.size
        if width / height > target_ratio:
            self.box.height = height
            self.box.width = target_ratio * height
        else:
            self.box.width = width
            self.box.height = width / target_ratio

    def increment_bpm(self, val):
        self.bpm += val

    def on_bpm(self, instance, bpm):
        self.spb = 60 / self.bpm
        # self.stop()
        # self.play()


class MetronomeApp(App):
    def build(self):
        return Metronome()


if __name__ == "__main__":
    MetronomeApp().run()

