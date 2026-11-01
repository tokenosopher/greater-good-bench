"""Original, softly struck pentatonic tones. No external sound assets."""
import math, wave, struct
from pathlib import Path
rate=32000
length=10
notes=[(0.25,62,.20),(1.45,69,.18),(2.6,74,.22),(4.25,66,.16),(4.75,69,.16),(5.25,74,.16),(5.75,76,.14),(6.25,78,.13),(6.75,81,.11),(7.55,74,.16),(7.55,69,.09),(7.55,62,.10)]
frames=bytearray()
for i in range(rate*length):
    t=i/rate
    l=r=0.0
    for j,(start,midi,amp) in enumerate(notes):
        a=t-start
        if not 0<=a<4: continue
        freq=440*2**((midi-69)/12)
        env=(1-math.exp(-a*65))*math.exp(-a*1.65)
        sig=amp*env*(math.sin(math.tau*freq*a)+.18*math.exp(-a*2)*math.sin(math.tau*freq*2*a)+.045*math.sin(math.tau*freq*3*a))
        pan=.16*math.sin(j*2)
        l+=sig*(.7-pan);r+=sig*(.7+pan)
    fade=min(1,t/.15,max(0,(10-t)/1.15))
    frames+=struct.pack('<hh',int(max(-1,min(1,l*fade)) * 27000),int(max(-1,min(1,r*fade))*27000))
Path('.build').mkdir(exist_ok=True)
with wave.open('.build/sound.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes(frames)
