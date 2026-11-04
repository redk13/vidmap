#!/usr/bin/env python3
"""Generate whisper-quiet minor pad (Dm - Bb - C - Am, peak 0.066) from audio_mg.py recipe."""
import sys
import wave
import numpy as np

SR = 44100

def midi_f(m: float) -> float:
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))

def synth_pad(duration_sec: float, peak: float = 0.066) -> np.ndarray:
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 48, 52]]  # Dm - Bb - C - Am
    ch_dur = 4.5
    n_total = int(round(duration_sec * SR))
    music = np.zeros(n_total + SR * 2, np.float64)
    tt = 0.0
    ci = 0
    rng = np.random.RandomState(7)
    while tt < duration_sec + 2.0:
        ch = chords[ci % 4]
        n = int(ch_dur * SR * 1.25)
        t = np.arange(n) / SR
        env = np.minimum(t / 1.8, 1.0) * np.exp(-np.maximum(t - ch_dur * 0.9, 0.0) / 0.9)
        sig = np.zeros(n)
        for m in ch:
            f = midi_f(m)
            ph = rng.rand() * 6.28
            sig += (
                np.sin(2 * np.pi * f * t + ph)
                + 0.26 * np.sin(4 * np.pi * f * t)
                + 0.07 * np.sin(6 * np.pi * f * t)
            )
        sig += 1.1 * np.sin(2 * np.pi * midi_f(ch[0] - 24) * t)
        sig *= env / len(ch)
        i0 = int(tt * SR)
        nn = min(n, len(music) - i0)
        if nn > 0:
            music[i0:i0 + nn] += sig[:nn]
        tt += ch_dur
        ci += 1

    music = music[:n_total]
    music *= peak / max(np.abs(music).max(), 1e-9)
    fade_in = int(1.5 * SR)
    fade_out = int(1.5 * SR)
    if n_total > fade_in + fade_out:
        music[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
        music[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)
    return music

def write_wav(path: str, sig: np.ndarray) -> None:
    pcm = np.clip(sig * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

if __name__ == '__main__':
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 23.4
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'audio/pad-mg.wav'
    pad = synth_pad(dur, peak=0.066)
    write_wav(out_path, pad)
    print(f"Wrote {out_path}: {dur:.2f}s, peak={np.abs(pad).max():.4f}")
