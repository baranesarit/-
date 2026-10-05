import numpy as np, wave, os
SR = 44100; DUR = 25.0; BPM = 120; BEAT = 60 / BPM
SF = os.path.join(os.path.dirname(__file__), 'sf')
out = np.zeros((int(SR * DUR) + SR, 2))
rng = np.random.default_rng(3)
cache = {}
def sample(inst, note):
    k = (inst, note)
    if k not in cache:
        with wave.open(f'{SF}/{inst}-{note}.wav') as w:
            cache[k] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    return cache[k]
def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); sig = sig[: len(out) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:i + len(sig), 0] += sig * gain * l * 1.41
    out[i:i + len(sig), 1] += sig * gain * r * 1.41
def note(inst, n, t, length, gain, pan=0.0):
    s = sample(inst, n)[: int((length + .35) * SR)].copy()
    fade = int(.35 * SR); s[-fade:] *= np.linspace(1, 0, fade) ** 2
    place(s, t, gain, pan)

# chords: C G Am F, three times, then final C
prog = [('C', ['C', 'E', 'G']), ('G', ['G', 'B', 'D']), ('A', ['A', 'C', 'E']), ('F', ['F', 'A', 'C'])] * 3
order = 'CDEFGAB'
def up(n, o):  # note name + octave, keep ascending order
    return f'{n}{o}'

for bar, (root, tri) in enumerate(prog):
    t0 = bar * 4 * BEAT
    # marimba bouncy arpeggio (8ths): r5 r 3' 5 3' r 5
    pat = [(tri[0], 4), (tri[2], 4), (tri[0], 5), (tri[1], 5), (tri[2], 4), (tri[1], 5), (tri[0], 5), (tri[2], 4)]
    for k, (n, o) in enumerate(pat):
        acc = 1.0 if k % 2 == 0 else .7
        note('marimba', up(n, o), t0 + k * BEAT / 2, BEAT / 2, .42 * acc, pan=-.25 if k % 2 else .25)
    if bar >= 1:  # bass: root on 1, root on 3, pickup on the "and" of 4
        note('acoustic_bass', f'{root}2', t0, BEAT * 1.5, .75)
        note('acoustic_bass', f'{root}2', t0 + 2 * BEAT, BEAT, .6)
        note('acoustic_bass', f'{tri[2]}2', t0 + 3.5 * BEAT, BEAT / 2, .45)
    if bar >= 2:  # pizzicato off-beat chord stabs
        for b in (1, 3):
            for n in tri:
                note('pizzicato_strings', f'{n}4', t0 + b * BEAT, BEAT / 2, .16)

# glockenspiel hook from bar 4 (8s) – one phrase per 2 bars
hook = [  # (beat offset, note)
    [(0, 'E6'), (1, 'G6'), (1.5, 'E6'), (2, 'C6'), (3, 'D6')],
    [(0, 'D6'), (1, 'B5'), (2, 'G5'), (3.5, 'D6')],
    [(0, 'C6'), (.5, 'E6'), (1, 'A6'), (2, 'G6'), (3, 'E6')],
    [(0, 'F6'), (1, 'E6'), (2, 'C6'), (2.5, 'D6'), (3, 'C6')],
]
for bar in range(4, 12):
    for b, n in hook[bar % 4]:
        note('glockenspiel', n, bar * 4 * BEAT + b * BEAT, BEAT, .2, pan=.35)

# final chord at 24s
for n, g in (('C4', .5), ('E4', .45), ('G4', .45), ('C5', .45)):
    note('marimba', n, 24.0, 1.0, g)
note('acoustic_bass', 'C2', 24.0, 1.0, .75)
note('glockenspiel', 'C6', 24.0, 1.0, .25); note('glockenspiel', 'G6', 24.12, .9, .18)

# soft drums from 2s to 24s
def kick():
    n = int(.28 * SR); t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
def hp(x, a=.85):  # crude one-pole high-pass
    y = np.zeros_like(x)
    for i in range(1, len(x)): y[i] = a * (y[i-1] + x[i] - x[i-1])
    return y
def snap():
    n = int(.18 * SR); t = np.arange(n) / SR
    nz = hp(rng.standard_normal(n), .7)
    env = np.exp(-t * 35) + .6 * np.exp(-np.maximum(t - .012, 0) * 45) * (t > .012)
    return nz * env * .35
def shaker():
    n = int(.06 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), .5) * np.exp(-t * 70) * np.minimum(t * 600, 1)
K, S = kick(), snap()
b = 4
while b * BEAT < 24.0:
    t = b * BEAT
    if b % 4 in (0, 2): place(K, t, .8)
    if b % 4 in (1, 3): place(S, t, .22, pan=-.1)
    for k in range(2): place(shaker(), t + k * BEAT / 2, .035 if k else .02, pan=.4)
    b += 1

# master: gentle fade in/out, normalize
n = int(SR * DUR); out = out[:n]
out[:int(.4 * SR)] *= np.linspace(0, 1, int(.4 * SR))[:, None]
fo = int(.8 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out / np.abs(out).max() * 1.2) * .89
with wave.open(os.path.join(os.path.dirname(__file__), 'music.wav'), 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print('ok')
