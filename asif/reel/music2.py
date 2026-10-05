import numpy as np, wave, os, json
D = os.path.dirname(os.path.abspath(__file__)); SF = D + '/sf'
SR = 44100; DUR = 30.0; BEAT = .5
out = np.zeros((int(SR * DUR) + SR * 2, 2)); rng = np.random.default_rng(5)
cache = {}
def sample(inst, n):
    if (inst, n) not in cache:
        with wave.open(f'{SF}/{inst}-{n}.wav') as w:
            cache[(inst, n)] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    return cache[(inst, n)]
def place(sig, t, g=1.0, pan=0.0):
    i = int(t * SR); sig = sig[:len(out) - i]
    out[i:i+len(sig), 0] += sig * g * np.cos((pan + 1) * np.pi / 4) * 1.41
    out[i:i+len(sig), 1] += sig * g * np.sin((pan + 1) * np.pi / 4) * 1.41
def note(inst, n, t, L, g, pan=0.0):
    s = sample(inst, n)[:int((L + .25) * SR)].copy(); f = int(.25 * SR); s[-f:] *= np.linspace(1, 0, f) ** 2
    place(s, t, g, pan)
def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += a * (v - acc); y[i] = acc
    return y
def hp(x, a): return x - lp(x, a)
env = lambda n, k: np.exp(-np.arange(n) / SR * k)

# ---- music: C – Am – F – G, bouncy ----
chords = [('C', ['C3', 'G3', 'C4', 'E4', 'G4']), ('A', ['A2', 'E3', 'A3', 'C4', 'E4']), ('F', ['F2', 'C3', 'F3', 'A3', 'C4']), ('G', ['G2', 'D3', 'G3', 'B3', 'D4'])]
bars = int(29.5 // (4 * BEAT))
def strum(t, notes, g, down=True):
    seq = notes if down else notes[::-1]
    for k, n in enumerate(seq): note('acoustic_guitar_nylon', n, t + k * .012, BEAT * 1.2, g * (1 if down else .7), pan=-.3)
for bar in range(bars):
    root, tones = chords[bar % 4]; t0 = bar * 4 * BEAT
    # strum pattern: D . D U . U D U
    for b, d in ((0, 1), (1, 1), (1.5, 0), (2.5, 0), (3, 1), (3.5, 0)):
        strum(t0 + b * BEAT, tones, .22 if d else .16, bool(d))
    if bar >= 1:
        note('acoustic_bass', f'{root}2', t0, BEAT, .7); note('acoustic_bass', f'{root}2', t0 + 1.5 * BEAT, BEAT / 2, .45)
        note('acoustic_bass', f'{root}2', t0 + 2 * BEAT, BEAT, .6); note('acoustic_bass', f'{tones[1][0]}2', t0 + 3.5 * BEAT, BEAT / 2, .45)
    if 2 <= bar:  # marimba hook
        hook = [[(0, 'E5'), (.5, 'G5'), (1, 'C6'), (2, 'G5'), (2.5, 'E5'), (3, 'G5')],
                [(0, 'E5'), (.5, 'A5'), (1, 'C6'), (2, 'A5'), (3, 'E5')],
                [(0, 'F5'), (.5, 'A5'), (1, 'C6'), (2, 'A5'), (2.5, 'F5'), (3, 'A5')],
                [(0, 'G5'), (.5, 'B5'), (1, 'D6'), (2, 'B5'), (3, 'G5'), (3.5, 'A5')]][bar % 4]
        for b, n in hook: note('marimba', n, t0 + b * BEAT, BEAT / 2, .28, pan=.3)
end = bars * 4 * BEAT
for n in ('C3', 'G3', 'C4', 'E4', 'G4', 'C5'): note('acoustic_guitar_nylon', n, end + .02 * 'C3G3C4E4G4C5'.index(n[:2]) / 2, 1.5, .25)
note('acoustic_bass', 'C2', end, 1.5, .7); note('glockenspiel', 'C6', end, 1.5, .25); note('glockenspiel', 'G6', end + .1, 1.4, .2)

# drums (light)
def kick():
    n = int(.25 * SR); t = np.arange(n) / SR; f = 50 + 80 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 15)
clap_n = int(.2 * SR); CLAP = hp(rng.standard_normal(clap_n), .35) * (env(clap_n, 30) + .5 * np.roll(env(clap_n, 40), int(.01 * SR))) * .3
K = kick(); b = 4
while b * BEAT < end:
    t = b * BEAT
    if b % 4 in (0, 2): place(K, t, .75)
    if b % 4 in (1, 3): place(CLAP, t, .4, -.1)
    b += 1

# ---- SFX synced to the animation ----
def sfx(kind):
    if kind == 'slap':
        n = int(.18 * SR); nz = lp(rng.standard_normal(n), .25) * env(n, 30)
        th = np.sin(2 * np.pi * 90 * np.arange(n) / SR) * env(n, 35)
        return (nz * .9 + th * .6), .55
    if kind == 'tap':
        n = int(.06 * SR); return lp(rng.standard_normal(n), .4) * env(n, 90), .35
    if kind == 'stamp':
        n = int(.3 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-t * 30)) / SR) * env(n, 14) + lp(rng.standard_normal(n), .3) * env(n, 40) * .7, .75
    if kind == 'pop':
        n = int(.12 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(350 + 900 * t / .12) / SR) * np.sin(np.pi * t / .12) ** 2, .22
    if kind == 'scribble':
        n = int(.35 * SR); t = np.arange(n) / SR
        return hp(lp(rng.standard_normal(n), .5), .08) * (0.5 + .5 * np.sin(2 * np.pi * 22 * t)) * np.sin(np.pi * t / .35), .1
    if kind == 'whoosh':
        n = int(.45 * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); y = np.empty(n); acc = 0.0
        for i in range(n):
            a = .02 + .25 * np.sin(np.pi * i / n); acc += a * (x[i] - acc); y[i] = acc
        return y * np.sin(np.pi * t / .45) ** 1.5, .5
for t, kind in json.load(open(D + '/sfx.json')):
    s, g = sfx(kind); place(s / (np.abs(s).max() + 1e-9), t, g, pan=rng.uniform(-.3, .3))

n = int(SR * DUR); out = out[:n]
fo = int(1.0 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out / np.abs(out).max() * 1.3) * .9
with wave.open(D + '/music2.wav', 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print('ok')
