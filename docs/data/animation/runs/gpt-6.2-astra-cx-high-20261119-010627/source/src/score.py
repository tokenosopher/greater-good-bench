"""Render the flight, unfolding paper, a pencil stroke, and a small acoustic motif."""
import array
import math
import random
import sys
import wave

sr = 44100
duration = 9.5
rng = random.Random(12061998)
samples = [0.0] * int(sr * duration)

def pluck(start, freq, gain, decay):
    offset = round(start * sr)
    for j in range(min(round(3.2 * decay * sr), len(samples) - offset)):
        t = j / sr
        ph = 2 * math.pi * freq * t
        tone = (math.sin(ph) + 0.32 * math.sin(2.004 * ph) * math.exp(-t * 6)
                + 0.19 * math.sin(3.01 * ph) * math.exp(-t * 10))
        env = (1 - math.exp(-t * 130)) * math.exp(-t * 3.3 / decay)
        samples[offset + j] += gain * env * tone

# A spare, ascending five-note figure and its lower, settled reply.
for note in [(0.12,196,.13,1.4),(.24,293.66,.10,1.0),(.54,392,.09,1.2),
             (1.05,440,.07,1.4),(1.36,587.33,.075,1.8),
             (4.65,196,.09,1.5),(4.79,293.66,.055,1.5),
             (6.32,392,.12,2.4),(6.39,493.88,.07,2.1),(6.48,587.33,.065,2.6)]:
    pluck(*note)

def surface(start, length, gain, kind):
    offset = int(sr * start)
    low = mid = 0
    for i in range(int(length * sr)):
        t = i / sr
        u = t / length
        white = rng.uniform(-1, 1)
        mid += .39 * (white - mid)
        low += .046 * (mid - low)
        if kind == 'graphite':
            sound = (mid - low) * (.65 + .23 * math.sin(2*math.pi*33*t + 16*t*t))
        elif kind == 'fold':
            sound = (mid - low) * (.52 + .4 * math.sin(43*t + 4*math.sin(55*t)))
            if rng.random() < .0018:
                sound += rng.uniform(-1.8, 1.8)
        else:
            sound = 4 * low
        samples[offset+i] += gain * sound * math.sin(math.pi*u)**.75

surface(0,1.65,.08,'air')
for a,b,c in [(2.93,.54,.19),(3.43,.34,.21),(3.66,.73,.24),(4.29,.48,.18)]:
    surface(a,b,c,'fold')
surface(5.12,1.10,.24,'graphite')
with wave.open(sys.argv[1], 'wb') as wav:
    wav.setparams((1,2,sr,0,'NONE','not compressed'))
    wav.writeframes(array.array('h',(round(max(-1,min(1,s))*32767) for s in samples)).tobytes())
