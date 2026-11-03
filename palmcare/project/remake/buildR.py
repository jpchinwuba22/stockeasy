"""Assemble a remade PalmCare video (PCV=1|2|3) at 1080x1920/24p: graded clips with camera moves, whips and light
flashes, the product reveals and the end card; the approved narration (unchanged takes, re-spaced), her on-camera
line, ambience, reveal/card SFX and the music ducked under speech -> baseR<V>.mov (captions etc. come from overlayR.py).
Usage: buildR.py"""
import subprocess

import tlR as tl

V = tl.V
UP = "scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0,setsar=1,fps=24"
GRADE = {
    # warm cream / cocoa spa
    1: "eq=contrast=1.06:saturation=1.10:gamma=0.99,colorbalance=rs=0.04:gs=0.01:bs=-0.04:rm=0.04:bm=-0.04:rh=0.02:bh=-0.03,"
       "curves=all='0/0.015 0.25/0.235 0.5/0.505 0.75/0.775 1/0.985',vignette=PI/6,noise=alls=3:allf=t",
    # juicy midday citrus
    2: "eq=contrast=1.06:saturation=1.10:gamma=0.99,colorbalance=rs=0.04:gs=0.01:bs=-0.05:rm=0.03:bm=-0.04:rh=0.03:bh=-0.04,"
       "curves=all='0/0.015 0.25/0.235 0.5/0.505 0.75/0.775 1/0.985',vignette=PI/6,noise=alls=3:allf=t",
    # golden sun, deep rich shadows (no lift)
    3: "eq=contrast=1.06:saturation=1.08:gamma=1.0,colorbalance=rs=0.04:bs=-0.05:rm=0.03:bm=-0.04:rh=0.02:bh=-0.03,"
       "curves=all='0/0.012 0.25/0.24 0.5/0.505 0.75/0.77 1/0.985',vignette=PI/6,noise=alls=3:allf=t",
}[V]
SRC = "setpts=PTS-STARTPTS,setsar=1,fps=24"
FLASH = "0xFFF0D6"


def mv(z0, z1, dx, dy, dur, kind):
    p = f"min(1\\,on/({dur}*24))"
    e = f"(1-pow(1-{p}\\,3))" if kind == "o" else f"({p}*{p}*(3-2*{p}))"
    return (f"scale=2160:3840:flags=lanczos,zoompan=z='{z0}+({z1}-{z0})*{e}':x='iw/2-(iw/zoom/2)+{dx}*2*{e}'"
            f":y='ih/2-(ih/zoom/2)+{dy}*2*{e}':d=1:s=1080x1920:fps=24,setsar=1")


def transitions(tr, dur):
    f = []
    for t in sorted(tr):
        if t == "dip_in":
            f.append("fade=in:st=0:d=0.35:color=black")
        elif t == "flash_in":
            f.append(f"fade=in:st=0:d=0.16:color={FLASH}")
        elif t == "flash_out":
            f.append(f"fade=out:st={dur - 0.12:.3f}:d=0.12:color={FLASH}")
        elif t.startswith("wo:"):
            f.append(f"dblur=angle={t[3:]}:radius=26:enable='gte(t,{dur - 0.125:.3f})'")
        elif t.startswith("wi:"):
            f.append(f"dblur=angle={t[3:]}:radius=26:enable='lt(t,0.125)'")
    return f


def main():
    clips = sorted({s[0] for s in tl.SHOTS if s[0].startswith("v")})
    inputs = [f"{c}.mp4" for c in clips] + [f"hp{V}a.mp4", f"hp{V}b.mp4", f"ec{V}.mp4", tl.VO,
                                             "../v4/sfx_reveal4.mp3", "../v4/sfx_card4.mp3", tl.MUSIC]
    idx = {c: k for k, c in enumerate(clips)}
    n = len(clips)
    iHA, iHB, iEC, iVO, iRV, iCD, iMU = range(n, n + 7)
    times = tl.shot_times()
    vf, af, labels, alabels = [], [], [], []
    for k, ((src, st, dur, cam, tr), (t0, t1)) in enumerate(zip(tl.SHOTS, times)):
        lab = f"s{k}"
        if src in ("HA", "HB", "EC"):
            i = {"HA": iHA, "HB": iHB, "EC": iEC}[src]
            chain = [SRC, "tpad=stop_mode=clone:stop_duration=0.1", f"trim=0:{dur}", SRC] + transitions(tr, dur) + ["format=yuv420p"]
            vf.append(f"[{i}:v]" + ",".join(chain) + f"[{lab}]")
            af.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[a{k}]")
        else:
            i = idx[src]
            z0, z1, dx, dy, kind = cam
            chain = [f"trim={st}:{st + dur}", SRC, UP, mv(z0, z1, dx, dy, dur, kind), GRADE] + transitions(tr, dur) + ["format=yuv420p"]
            vf.append(f"[{i}:v]" + ",".join(chain) + f"[{lab}]")
            af.append(f"[{i}:a]atrim={st}:{st + dur},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                      f"afade=t=in:d=0.05,afade=t=out:st={dur - 0.07:.3f}:d=0.07[a{k}]")
        labels.append(f"[{lab}]")
        alabels.append(f"[a{k}]")
    vf.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[v]")
    T = tl.TOTAL
    af.append("".join(alabels) + f"concat=n={len(alabels)}:v=0:a=1,volume=0.30,apad=whole_dur={T}[amb]")
    # narration: the approved take, cut only in the pauses between sentences
    nseg = len(tl.VOSEG)
    af.append(f"[{iVO}:a]aresample=48000,highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.5:g=2,"
              f"acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=3dB,aformat=channel_layouts=stereo,asplit={nseg}"
              + "".join(f"[vo{k}]" for k in range(nseg)))
    for k, (s0, s1, at) in enumerate(tl.VOSEG):
        ms = int(round(at * 1000))
        af.append(f"[vo{k}]atrim={s0}:{s1},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={s1 - s0 - 0.06:.3f}:d=0.06,"
                  f"adelay={ms}|{ms}[l{k}]")
    af.append("".join(f"[l{k}]" for k in range(nseg)) + f"amix=inputs={nseg}:normalize=0:duration=longest,apad=whole_dur={T}[vo]")
    # her on-camera line, in sync with the picture
    lc, ls, le, lat = tl.LINE
    ms = int(round(lat * 1000))
    af.append(f"[{idx[lc]}:a]atrim={ls}:{le},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,"
              f"equalizer=f=3000:t=q:w=1.5:g=1.5,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2dB,"
              f"afade=t=in:d=0.05,afade=t=out:st={le - ls - 0.1:.3f}:d=0.1,volume=1.15,adelay={ms}|{ms},apad=whole_dur={T}[line]")
    af.append(f"[vo][line]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur={T},asplit=2[speech][key]")
    ha, hb, ec = times[[s[0] for s in tl.SHOTS].index("HA")][0], times[[s[0] for s in tl.SHOTS].index("HB")][0], times[-1][0]
    r1, r2, c1 = (int(round((x - 0.05) * 1000)) for x in (ha, hb, ec))
    af.append(f"[{iRV}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.7,asplit=2[r1][r2]")
    af.append(f"[r1]adelay={r1}|{r1}[x1];[r2]adelay={r2}|{r2}[x2]")
    af.append(f"[{iCD}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.8,adelay={c1}|{c1}[x3]")
    af.append(f"[{iMU}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={tl.MUSOFF},asetpts=PTS-STARTPTS,atrim=0:{T},"
              f"volume={tl.MUSVOL},afade=t=in:d=0.4,afade=t=out:st={T - 1.2:.2f}:d=1.2,apad=whole_dur={T}[mus]")
    af.append("[mus][key]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=450:makeup=1[duck]")
    af.append(f"[amb][speech][duck][x1][x2][x3]amix=inputs=6:normalize=0:duration=first,atrim=0:{T},"
              f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in inputs:
        cmd += ["-i", f]
    cmd += ["-filter_complex", ";".join(vf + af), "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", f"baseR{V}.mov"]
    subprocess.run(cmd, check=True)
    print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"baseR{V}.mov"],
                         capture_output=True, text=True).stdout.strip())


if __name__ == "__main__":
    main()
