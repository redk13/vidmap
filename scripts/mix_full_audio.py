#!/usr/bin/env python3
"""Assemble the full Tokyo VO with the code-generated whispered Dm-Bb-C-Am pad."""
import argparse
import subprocess
import wave
import numpy as np
from make_pad import SR, synth_pad

TOTAL_FRAMES = 12685
FPS = 30
DURATION = TOTAL_FRAMES / FPS
# Absolute timeline offsets (frames) from the approved VO map.
VO_OFFSETS = [24, 1047, 1800, 2556, 3208, 4040, 4881, 6151, 7692, 8927, 10093, 10688, 11584, 12190]
VO_FILES = [
    'vo/01-coldopen.mp3', 'vo/02-act1-arrows.mp3', 'vo/03-act1-fertility.mp3',
    'vo/04-act1-paradox.mp3', 'vo/05-space-dive.mp3', 'vo/06-space-akiya.mp3',
    'vo/07-time.mp3', 'vo/08-machine.mp3', 'vo/09-blackhole.mp3', 'vo/10-bill.mp3',
    'vo/11-economy.mp3', 'vo/12-finale-curve.mp3', 'vo/13-finale-trying.mp3',
    'vo/14-finale-korea.mp3',
]


def decode_mono(path: str) -> np.ndarray:
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'
    ])
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0


def write_wav(path: str, signal: np.ndarray) -> None:
    pcm = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='mix.wav')
    args = ap.parse_args()

    sample_count = TOTAL_FRAMES * (SR // FPS)
    mix = np.zeros(sample_count, np.float64)

    for path, frame in zip(VO_FILES, VO_OFFSETS):
        voice = decode_mono(path)
        start = frame * (SR // FPS)
        n = min(len(voice), sample_count - start)
        if n > 0:
            mix[start:start+n] += voice[:n]

    # Exact legacy audio_mg.py recipe: Dm-Bb-C-Am, 4.5s/chord, peak 0.066.
    pad = synth_pad(DURATION, peak=0.066)
    mix += pad[:sample_count]

    peak = float(np.abs(mix).max())
    if peak > 0.94:
        mix *= 0.94 / peak
    write_wav(args.output, mix)
    print(
        f'Full audio ready: duration={DURATION:.6f}s, '
        f'pad_peak={np.abs(pad).max():.4f}, mix_peak={np.abs(mix).max():.4f}'
    )


if __name__ == '__main__':
    main()
