rem ffmpeg -i tempout.wav -af pan="mono|c0=c0" -y tempout_L.wav
rem ffmpeg -i tempout.wav -af pan="mono|c0=c1" -y tempout_R.wav


ffmpeg  -loglevel error -i tempout.wav -af "pan=stereo|c0=c0"  -y tempout_L.wav
ffmpeg  -loglevel error -i tempout.wav -af "pan=stereo|c1=c1"  -y tempout_R.wav
