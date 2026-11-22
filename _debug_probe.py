import subprocess, json
path = r'D:\DigitalBrain\data\videos\hemomemo_24360.mp4'
r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=duration', '-of', 'json', path], capture_output=True, text=True)
print('RAW:', r.stdout)
d = json.loads(r.stdout)
fmt = d.get('format', {})
st = d.get('streams', [{}])[0]
print('FMT-DUR:', fmt.get('duration'))
print('ST-DUR:', st.get('duration'))
