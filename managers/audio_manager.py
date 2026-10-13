import io
import math
import random
import struct
import wave

import pygame


class AudioManager:
    SAMPLE_RATE = 22050

    def __init__(self):
        self.sounds = {}
        self.volume = 1.0
        self.error = ""

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1)
            except pygame.error as error:
                self.error = str(error)
                print(f"Audio unavailable: {self.error}")
                return

        self.sounds = {
            "click": self._make_tone(660, 880, 0.075, 0.25),
            "shoot": self._make_tone(760, 310, 0.11, 0.18),
            "hit": self._make_tone(190, 72, 0.28, 0.35, waveform="square"),
            "enemy": self._make_tone(520, 110, 0.18, 0.28, waveform="noise"),
            "pickup": self._make_tone(420, 1050, 0.24, 0.25),
        }

    @property
    def available(self):
        return bool(self.sounds)

    def _make_tone(self, start_hz, end_hz, duration, amplitude, waveform="sine"):
        sample_count = int(self.SAMPLE_RATE * duration)
        noise = random.Random(start_hz + end_hz)
        samples = bytearray()

        for index in range(sample_count):
            progress = index / max(1, sample_count - 1)
            frequency = start_hz + (end_hz - start_hz) * progress
            envelope = min(1.0, progress * 18) * (1 - progress) ** 1.8
            phase = 2 * math.pi * frequency * index / self.SAMPLE_RATE
            if waveform == "square":
                value = 1.0 if math.sin(phase) >= 0 else -1.0
            elif waveform == "noise":
                value = noise.uniform(-1.0, 1.0) * (0.35 + 0.65 * abs(math.sin(phase)))
            else:
                value = math.sin(phase)
            samples.extend(struct.pack("<h", int(value * envelope * amplitude * 32767)))

        wav_data = io.BytesIO()
        with wave.open(wav_data, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(samples)
        wav_data.seek(0)
        return pygame.mixer.Sound(file=wav_data)

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def play(self, name):
        sound = self.sounds.get(name)
        if sound is not None and self.volume > 0:
            sound.play()
