"""Assemble Video 2 (redo) from tl2b: each shot rendered on its own (clean slow motion by frame blending, which can
never warp a static bottle; gentle camera drift on non-product shots only; soft sunlit grade), then joined with soft
dissolves (hard cuts where the shot is flagged "cut"), the end card last. Audio: placed narration + Afro-soul score,
ducked gently under the voice, loudness -14 LUFS -> base4.mov (graphics come from overlay2b.py)."""
import os
import subprocess

import tl8 as tl

UP = "scale=1080:1920:flags=lanczos,cas=0.5,setsar=1"
GRADE = ("eq=contrast=1.05:saturation=1.07,"
         "colorbalance=rs=0.02:bs=-0.03:rm=0.03:gm=0.005:bm=-0.035:rh=0.01:bh=-0.02,"
         "curves=all='0/0.012 0.25/0.245 0.5/0.5 0.8/0.81 1/0.985'")   # one warm sun-gold look across every clip; mids held, so skin is never lightened
SEG = "seg8"


def mv(z0, z1, dx, dy, dur):
    if (z0, z1, dx, dy) == (1.0, 1.0, 0, 0):
        return "null"
    p = f"min(1\\,on/({dur}*24))"
    e = f"({p}*{p}*(3-2*{p}))"
    return (f"scale=2160:3840:flags=lanczos,zoompan=z='{z0}+({z1}-{z0})*{e}':x='iw/2-(iw/zoom/2)+{dx}*2*{e}'"
            f":y='ih/2-(ih/zoom/2)+{dy}*2*{e}':d=1:s=1080x1920:fps=24,setsar=1")


def seg(k, src, st, dur, cam, fl):
    out = f"{SEG}/{k:02d}.mp4"
    if src == "EC":
        vf = f"trim=0:{dur},setpts=PTS-STARTPTS,fps=24,format=yuv420p"
        inp = tl.EC_FILE
    else:
        sp = next((float(t[3:]) for t in fl if t.startswith("sp:")), 1.0)
        z0, z1, dx, dy, _ = cam
        slow = [] if sp == 1.0 else [f"setpts=PTS/{sp}", "minterpolate=fps=24:mi_mode=blend"]
        look = [] if "nograde" in fl else [GRADE, "split[a][b];[b]gblur=sigma=28[g];[a][g]blend=all_mode=screen:all_opacity=0.06"]
        vf = ",".join([f"trim={st}:{st + dur * sp + 0.05:.4f}", "setpts=PTS-STARTPTS", "fps=24"] + slow
                      + [UP, mv(z0, z1, dx, dy, dur)] + look + [
                         f"trim=0:{dur:.4f}", "setpts=PTS-STARTPTS", "format=yuv420p"])
        inp = f"{src}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-an",
                    "-c:v", "libx264", "-crf", "10", "-preset", "medium", out], check=True)
    return out


def main():
    os.makedirs(SEG, exist_ok=True)
    n = len(tl.SHOTS)
    files, lens = [], []
    for k, (src, st, dur, cam, fl) in enumerate(tl.SHOTS):
        tail = 0 if ("cut" in fl or k == n - 1) else tl.XF
        files.append(seg(k, src, st, dur + tail, cam, fl))
        lens.append(dur + tail)
        print("seg", k, src, round(dur + tail, 3), flush=True)
    # join: dissolve into shot k+1 when shot k carries a tail, else a hard cut (xfade of one frame = cut)
    vf, cur, acc = [], "[0:v]", lens[0]
    for k in range(1, n):
        dissolve = lens[k - 1] > tl.SHOTS[k - 1][2] + 1e-6
        d = tl.XF if dissolve else 1 / 24
        off = tl.STARTS[k] - (0 if dissolve else d)
        if not dissolve:
            # hard cut: pad shot k by one frame at its head so timing stays exact
            vf.append(f"[{k}:v]tpad=start=1:start_mode=clone,settb=1/24,setpts=PTS-STARTPTS[p{k}]")
            nxt = f"[p{k}]"
        else:
            vf.append(f"[{k}:v]settb=1/24,setpts=PTS-STARTPTS[p{k}]")
            nxt = f"[p{k}]"
        lab = f"[x{k}]"
        vf.append(f"{cur}settb=1/24{',setpts=PTS-STARTPTS' if k == 1 else ''}[c{k}];[c{k}]{nxt}xfade=transition=fade:duration={d:.4f}:offset={off:.4f}{lab}")
        cur = lab
    T = tl.TOTAL
    if all(abs(l - s[2]) < 1e-6 for l, s in zip(lens, tl.SHOTS)):     # hard cuts only: exact frame concat
        vf = ["".join(f"[{k}:v]settb=1/24,setpts=PTS-STARTPTS,fps=24[q{k}];" for k in range(n))
              + "".join(f"[q{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[cc]"]
        cur = "[cc]"
    vf.append(f"{cur}trim=0:{T},format=yuv420p[v]")
    iVO, iMU = n, n + 1
    af = [f"[{iVO}:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-1.5,"
          f"equalizer=f=3500:t=q:w=1.5:g=2.5,acompressor=threshold=-22dB:ratio=2.5:attack=10:release=150:makeup=2dB,"
          f"apad=whole_dur={T},atrim=0:{T},asplit=2[vo][key]",
          f"[{iMU}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T},volume=0.62,apad=whole_dur={T}[mus]",
          "[mus][key]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=450:makeup=1[duck]",
          f"[vo][duck]amix=inputs=2:normalize=0:duration=first,atrim=0:{T},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"]
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-i", tl.VO, "-i", tl.MUSIC, "-filter_complex", ";".join(vf + af), "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "base8.mov"]
    subprocess.run(cmd, check=True)
    print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "base8.mov"],
                         capture_output=True, text=True).stdout.strip())


if __name__ == "__main__":
    main()
