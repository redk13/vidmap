#!/usr/bin/env python3
"""Mix VO, the code-generated whispered pad, and restrained transition accents for the V9 sample."""
import argparse
import subprocess
import sys
import wave
import numpy as np
from make_pad import SR, synth_pad


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
    ap.add_argument('--voice', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--duration', type=float, default=23.4)
    args = ap.parse_args()

    duration = args.duration
    count = int(round(duration * SR))
    mix = np.zeros(count, np.float64)

    def add(signal: np.ndarray, start: float, gain: float = 1.0) -> None:
        i0 = int(round(start * SR))
        n = min(len(signal), count - i0)
        if i0 >= 0 and n > 0:
            mix[i0:i0+n] += signal[:n] * gain

    # The narration starts at frame 24 (+0.80s). Trim at 22.60s to finish at 23.40s.
    voice = decode_mono(args.voice)
    voice = voice[:int(round(22.60 * SR))].copy()
    fade = int(0.18 * SR)
    voice[-fade:] *= np.linspace(1.0, 0.0, fade)
    add(voice, 0.80)

    pad = synth_pad(duration, peak=0.066)  # Dm-Bb-C-Am; exact audio_mg.py recipe/peak
    mix += pad

    rng = np.random.RandomState(42)

    def whoosh(seconds: float) -> np.ndarray:
        n = int(seconds * SR)
        noise = rng.randn(n)
        kernel = 200
        filtered = np.convolve(noise, np.ones(kernel) / kernel, mode='same')
        filtered *= np.hanning(n)
        return filtered / max(np.abs(filtered).max(), 1e-9)

    def soft_hit() -> np.ndarray:
        n = SR
        t = np.arange(n) / SR
        hit = np.sin(2 * np.pi * 52 * t * np.exp(-t * 0.35)) * np.exp(-t * 3.4)
        return hit / max(np.abs(hit).max(), 1e-9)

    add(soft_hit(), 152 / 30.0, 0.14)
    add(whoosh(0.42), 186 / 30.0 - 0.12, 0.06)
    add(whoosh(0.42), 311 / 30.0 - 0.12, 0.06)
    add(whoosh(0.48), 453 / 30.0 - 0.14, 0.07)

    peak = np.abs(mix).max()
    if peak > 0.94:
        mix *= 0.94 / peak
    write_wav(args.output, mix)
    print(f'Audio mix: {duration:.2f}s, pad peak={np.abs(pad).max():.4f}, mix peak={np.abs(mix).max():.4f}')


if __name__ == '__main__':
    main()
