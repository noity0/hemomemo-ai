import subprocess, glob, json
files = glob.glob(r'D:\DigitalBrain\data\videos\hemomemo_*.mp4')
for p in files[:2]:
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=duration', '-of', 'json', p], capture_output=True, text=True)
    print(p, 'out:', r.stdout.strip())
