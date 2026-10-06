import numpy as np, wave, sys

SR = 44100
DUR = 24.0
BPM = 128
B = 60 / BPM          # beat
BAR = 4 * B
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    buf[i:i + len(sig)] += sig * gain


def addst(start, sig, gain=1.0, pan=0.0):
    add(L, start, sig, gain * (1 - pan) / 1.0 if pan > 0 else gain)
    add(R, start, sig, gain * (1 + pan) if pan < 0 else gain)


def env(n, a=0.005, d=0.1, s=0.6, r=0.05, length=None):
    t = np.arange(n) / SR
    length = length if length is not None else n / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((length - t) / r, 0, 1)
    return e * rel


def tone(freq, dur, kind="lead"):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "lead":  # clarinet-ish: odd harmonics + vibrato
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.15, 0, 1)
        ph = 2 * np.pi * freq * np.cumsum(vib) / SR
        s = sum(np.sin(k * ph) / k for k in (1, 3, 5, 7, 9)) + 0.25 * np.sin(2 * ph)
        return s * env(n, 0.01, 0.08, 0.75, 0.04) * 0.5
    if kind == "pluck":
        ph = 2 * np.pi * freq * t
        s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
        return s * np.exp(-t * 9) * 0.5
    if kind == "bass":
        ph = 2 * np.pi * freq * t
        s = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
        return s * env(n, 0.004, 0.08, 0.7, 0.03)
    if kind == "pad":
        s = sum(np.sin(2 * np.pi * freq * (1 + d) * t) for d in (-0.004, 0, 0.004))
        return s * env(n, 0.25, 0.3, 0.8, 0.4) * 0.25
    if kind == "bell":
        s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
        return s * np.exp(-t * 4) * 0.5


def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def noise(dur, decay, hp=1):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    for _ in range(hp):
        x = np.diff(x, prepend=0)
    return x * np.exp(-t * decay)


def clap():
    s = noise(0.25, 18, 1) * 0.5
    t = np.arange(len(s)) / SR
    return s + 0.3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)


def impact():
    n = int(1.6 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.5)
    return boom * 1.2 + noise(1.6, 3, 1) * 0.35


def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = noise(dur, 0, 1)
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 1500 * (t / dur) ** 2) / SR)
    return (x * 0.15 + sweep * 0.08) * (t / dur) ** 2


# --- harmony / melody (D harmonic minor, klezmer-pop) ---
D4, E4, F4, G4, A4, Bb4, C5, Cs5, D5, E5, F5, G5, A5, Bb5 = 62, 64, 65, 67, 69, 70, 72, 73, 74, 76, 77, 79, 81, 82
chords = {"Dm": [50, 53, 57], "Gm": [55, 58, 62], "A": [57, 61, 64], "C": [48, 52, 55]}
prog = ["Dm", "Gm", "A", "Dm", "Dm", "Gm", "A", "Dm"]
_ = None
mel = [
    [D5, _, A4, _, D5, E5, F5, _],
    [G5, F5, E5, D5, Bb4, _, G4, _],
    [A4, Cs5, E5, _, A5, _, G5, F5],
    [E5, _, D5, _, D5, _, _, _],
    [F5, _, E5, F5, A5, _, F5, _],
    [G5, _, Bb5, _, A5, G5, F5, E5],
    [E5, F5, E5, D5, Cs5, _, E5, _],
    [D5, _, _, _, A4, Cs5, E5, G5],
]


def play_melody(bar_start, phrase, gain=0.32):
    notes = mel[phrase]
    for k, nt in enumerate(notes):
        if nt is None:
            continue
        ln = 1
        while k + ln < 8 and notes[k + ln] is None:
            ln += 1
        d = ln * B / 2 * 0.95
        st = bar_start + k * B / 2
        sig = tone(midi(nt), d, "lead")
        add(L, st, sig, gain); add(R, st + 0.012, sig, gain * 0.85)
        oc = tone(midi(nt + 12), d, "pluck")
        add(L, st, oc, gain * 0.25); add(R, st, oc, gain * 0.35)


def groove(bar_start, chord, full=True):
    root = chords[chord][0] - 12
    for b in range(4):
        st = bar_start + b * B
        if full or b % 2 == 0:
            addst(st, kick(), 0.9)
        if full and b % 2 == 1:
            addst(st, clap(), 0.45)
        addst(st + B / 2, noise(0.06, 70, 2), 0.18)          # offbeat hat
        addst(st, noise(0.04, 120, 2), 0.07)
        if full:
            for e, n in enumerate((root, root + 12)):          # pumping bass
                addst(st + e * B / 2 + 0.01, tone(midi(n), B / 2 * 0.9, "bass"), 0.42)
        # oom-pah chord stab on offbeats
        for n in chords[chord]:
            s = tone(midi(n + 12), 0.18, "pluck")
            add(L, st + B / 2, s, 0.10); add(R, st + B / 2 + 0.008, s, 0.10)
    for n in chords[chord]:
        addst(bar_start, tone(midi(n), BAR, "pad"), 0.22)


# intro (bars 0-1): half-time + impacts on the title slams
for bar in range(2):
    groove(bar * BAR, prog[bar * 3 % 8], full=False)
addst(0.30, impact(), 0.8)
addst(1.40, impact(), 0.7)
addst(2 * BAR - 1.5, riser(1.5), 1.0)

# main (bars 2-11)
for bar in range(2, 12):
    ph = (bar - 2) % 8
    groove(bar * BAR, prog[ph])
    play_melody(bar * BAR, ph)
    if bar in (2, 4, 6, 8, 10):
        addst(bar * BAR, noise(2.0, 1.6, 1), 0.22)          # crash on every scene change
    if bar in (3, 5, 7, 9):
        addst((bar + 1) * BAR - 1.0, riser(1.0), 0.8)
addst(8 * BAR + 0.05, impact(), 0.6)                     # "נס גדול היה פה"

# candle chimes (scene 2): eighth notes from bar 2 beat 2
pent = [74, 76, 78, 81, 83, 86, 88, 90, 93]
for j in range(9):
    st = 2 * BAR + B + j * B / 2
    addst(st, tone(midi(pent[j] + 12), 1.2, "bell"), 0.22)

# ending: final hit at bar 12 then ring out
fin = 12 * BAR
addst(fin, kick(), 1.0); addst(fin, impact(), 0.7); addst(fin, noise(3.0, 1.2, 1), 0.25)
for n in [50, 57, 62, 65, 69, 74]:
    addst(fin, tone(midi(n), 1.5, "pad") , 0.35)
    addst(fin, tone(midi(n + 12), 1.4, "bell"), 0.08)

mix = np.stack([L, R], 1)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.6)
fade = int(0.6 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = (mix / np.max(np.abs(mix)) * 0.92 * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())
print("ok", DUR)
