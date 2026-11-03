import numpy as np, librosa, soundfile as sf, itertools
from kokoro_onnx import Kokoro
exec(open("../v4/vmatch.py").read().split("ref, sr")[0].split("fem =")[0])
def feats(y, sr):
    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=90, fmax=400, sr=16000); f0 = f0[vf]
    m = librosa.feature.mfcc(y=y, sr=16000, n_mfcc=20)[1:]
    return np.median(f0), np.std(np.log(f0)), m.mean(1), m.std(1)
ref, sr = sf.read("../v4/old_vo16.wav"); R = feats(ref.astype(np.float32), sr)
txt = "Lagos sun, meet your match. Ultra active vitamin C for radiance and even tone. Broad spectrum, no white cast. Made for the sun."
top = ["af_jessica", "bf_lily", "af_sarah", "af_aoede", "af_bella", "bf_alice"]
res = []
for a, b in itertools.combinations(top, 2):
    for w in (0.5, 0.7):
        st = V[a] * w + V[b] * (1 - w)
        lang = "en-us" if a[0] == "a" and (w >= 0.5) else "en-gb"
        au, s = k.create(txt, voice=st, speed=0.9, lang=lang)
        F = feats(au, s); d = np.linalg.norm((F[2] - R[2]) / (R[3] + 1e-3))
        res.append((d, a, b, w, F[0], F[1])); print(f"{a}+{b} {w} f0 {F[0]:.0f} var {F[1]:.3f} d {d:.2f}", flush=True)
res.sort(); print("BEST", res[:4])
