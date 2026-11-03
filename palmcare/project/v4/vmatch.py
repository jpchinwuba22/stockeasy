import numpy as np, librosa, soundfile as sf, sys
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-q8.onnx", "voices.npz")
V = np.load("voices.npz")
fem = [n for n in V.files if n[:2] in ("af", "bf")]
def feats(y, sr):
    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=90, fmax=400, sr=16000)
    f0 = f0[vf]
    m = librosa.feature.mfcc(y=y, sr=16000, n_mfcc=20)[1:]
    return np.median(f0), np.std(np.log(f0)), m.mean(1), m.std(1)
ref, sr = sf.read("../v3/v3_vo.mp3" if False else "../v4/old_vo16.wav")
R = feats(ref.astype(np.float32), sr)
print("amanda f0 %.0f  var %.3f" % (R[0], R[1]))
txt = "Lagos sun, meet your match. Ultra active vitamin C for radiance and even tone. Broad spectrum, no white cast. Made for the sun."
for n in fem:
    a, s = k.create(txt, voice=n, speed=0.9, lang="en-gb" if n[0] == "b" else "en-us")
    F = feats(a, s)
    d = np.linalg.norm((F[2] - R[2]) / (R[3] + 1e-3))
    print(f"{n:14s} f0 {F[0]:5.0f} var {F[1]:.3f} mfccdist {d:6.2f}  dur {len(a)/s:.1f}")
