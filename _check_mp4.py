import io, glob, os
files = glob.glob(r'D:\DigitalBrain\data\videos\hemomemo_*.mp4')
print('FILES:', len(files))
for p in files[:3]:
    b = open(p, 'rb').read(32)
    print(os.path.basename(p), 'head:', b[:12], 'has-ftyp:', b'ftyp' in b)
