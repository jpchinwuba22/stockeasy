s = open('v17/mix17.py').read()
rep = [('''for p, a, b, at in ((D+"v21/D_face.wav", 1.80, 5.62, S["hook"]), (D+"v14/src/D.mp4", 6.30, 9.40, S["name"]),
                    (D+"v14/src/E.mp4", 0.0, 10.0, S["review"])):''',
'''for p, a, b, at in ((D+"remo/public/hook1.mp4", 0.55, 7.15, S["hook"]), (D+"remo/public/actives1.mp4", 0.0, 8.1, S["actives"]),
                    (D+"remo/public/apply1.mp4", 0.9, 9.45, S["apply"])):'''),
('''for k, d in enumerate((0.0, 1.26, 2.56, 3.72)):
    pop(S["review"] + d, 760 + 90 * k, 0.17)''','''for k, at in enumerate((S["actives"] + 2.52, S["actives"] + 4.16, S["actives"] + 5.04, S["apply"] + 0.92, S["apply"] + 1.76)):
    pop(at, 760 + 70 * k, 0.17)'''),
('v17/voice17.wav', 'v27/mix/voice.wav'), ('v17/sfx17.wav', 'v27/mix/sfx.wav'), ('v17/amapiano17.wav', 'v27/mix/music.wav'), ('v17/pre17.wav', 'v27/mix/pre.wav')]
for a, b in rep:
    assert a in s, a[:40]; s = s.replace(a, b)
open('v27/mix27.py', 'w').write(s)
