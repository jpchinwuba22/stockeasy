import soundfile as sf, numpy as np, sys
from scipy.signal import welch
x,sr=sf.read(sys.argv[1]); m=x.mean(1)[int(8*sr):int(20*sr)]
f,p=welch(m,sr,nperseg=8192)
def b(a,c): s=(f>=a)&(f<c); return 10*np.log10(p[s].sum()+1e-20)
tot=b(20,20000)
print(sys.argv[1], " ".join(f"{a}-{c}:{b(a,c)-tot:+.1f}" for a,c in ((20,120),(120,500),(500,2000),(2000,6000),(6000,16000))))
