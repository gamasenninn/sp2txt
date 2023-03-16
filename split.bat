ffmpeg -i %1 -af volume=10dB, highpass=f=200, lowpass=f=3000 %~n1.wav

ffmpeg -ss 0 -to 60 -i %~n1.wav 01_%~n1.wav 
ffmpeg -ss 60 -to 120 -i %~n1.wav 02_%~n1.wav 
rem ffmpeg -ss 120 -to 180 -i %~n1.wav 03_%~n1.wav 
rem ffmpeg -ss 180 -to 240 -i %~n1.wav 04_%~n1.wav 


pause