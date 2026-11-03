"""Swap the friend's word "skin" for "face" in clip D: take the model's own spoken "face" from the same clip, convert it
to the friend's voice with the WORLD vocoder (her pitch level + rising emphasis, her average spectral envelope), match
loudness, lay it over the street ambience from her own pause, and splice it into "skin" with short crossfades."""
import warnings
warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf, pyworld as pw
from scipy.ndimage import uniform_filter1d
x, sr = sf.read('D.wav'); x = x.astype(np.float64)
def world(seg):
    f0, t = pw.harvest(seg, sr, f0_floor=100, f0_ceil=600, frame_period=5)
    return f0, pw.cheaptrick(seg, f0, t, sr), pw.d4c(seg, f0, t, sr)
def S(a, b): return x[int(a * sr):int(b * sr)].copy()
fF, spF, _ = world(S(2.06, 5.56)); fM, spM, _ = world(S(6.48, 8.56))
corr = uniform_filter1d(np.log(spF[fF > 0]).mean(0) - np.log(spM[fM > 0]).mean(0), 25)
f0, sp, ap = world(S(7.825, 8.150))
v = f0 > 0
ratio = 330 / np.median(f0[v])
f0n = f0 * ratio
idx = np.nonzero(v)[0]
f0n[idx] *= np.linspace(0.96, 1.06, len(idx))
y = pw.synthesize(f0n, sp * np.exp(corr)[None, :], ap, sr, frame_period=5)
sk = S(3.52, 3.86)
rms = lambda z: np.sqrt(np.mean(z[np.abs(z) > 0.01] ** 2))
y *= rms(sk) / rms(y)
y[:int(0.10 * sr)] *= np.linspace(2.0, 1.0, int(0.10 * sr))          # lift the soft 'f' so the word reads clearly
s0, s1 = int(3.535 * sr), int(3.862 * sr)
L = s1 - s0
amb = S(2.75, 3.25); bed = np.tile(amb, int(np.ceil(L / len(amb))) + 1)[:L]
seg = (y[:L] if len(y) >= L else np.pad(y, (0, L - len(y)))) + bed * 0.9
fade = int(0.012 * sr)
w = np.ones(L); w[:fade] = np.linspace(0, 1, fade); w[-fade:] = np.linspace(1, 0, fade)
out = x.copy(); out[s0:s1] = out[s0:s1] * (1 - w) + seg * w
sf.write('D_face.wav', out.astype(np.float32), sr, subtype='PCM_24')
print('pitch ratio', round(ratio, 2))
