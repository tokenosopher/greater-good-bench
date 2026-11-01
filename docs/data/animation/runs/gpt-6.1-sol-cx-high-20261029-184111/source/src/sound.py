"""A quiet, original bell-and-pad score; standard-library synthesis only."""
import math, struct, wave
from pathlib import Path
SR = 44100
DURATION = 10
# D6/9: a gentle unresolved beginning opens into a bright shared chord.
events = [(0.12,146.832,0.17,4.5),(1.55,220.0,0.13,4.0),
          (2.65,293.665,0.15,3.5),(3.35,369.994,0.13,3.5),
          (4.15,440.0,0.12,3.2),(4.95,493.883,0.10,3.2),
          (5.75,587.330,0.10,3.5),(6.35,369.994,0.10,3.5),
          (6.52,440.0,0.09,3.3),(6.69,587.330,0.09,3.0)]
result = []
for i in range(SR*DURATION):
    t = i/SR
    value = 0.0
    for start, hz, amp, dur in events:
        age = t-start
        if 0 <= age < dur:
            env = (1-math.exp(-age*35))*math.exp(-age*1.5)*(min(1,(dur-age)*3))
            tone = math.sin(2*math.pi*hz*age)+0.25*math.sin(2*math.pi*hz*2.003*age)*math.exp(-age*1.7)
            value += amp*env*tone
    # A soft, slow chord takes over as the circle fills with sunlight.
    rise = max(0,min(1,(t-3)/3))
    pad = sum(math.sin(2*math.pi*hz*t+0.3*math.sin(t*0.8)) for hz in (146.832,220,293.665,369.994))
    value += pad*0.014*rise
    fade = min(1,t/0.15,max(0,(10-t)/1.1))
    value *= fade
    result.append(int(max(-1,min(1,value))*32767))
Path('.build').mkdir(exist_ok=True)
with wave.open('.build/score.wav','wb') as out:
    out.setparams((1,2,SR,0,'NONE','not compressed'))
    out.writeframes(struct.pack('<'+'h'*len(result),*result))
