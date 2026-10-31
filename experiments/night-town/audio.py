import numpy as np, wave
sr=44100; T=5.0; t=np.arange(int(sr*T))/sr
def env(a,b): return np.clip((t-a)/(b-a),0,1)
out=np.zeros_like(t)
# dark pad: A minor-ish, detuned
for f in [55,110,130.81,164.81,207.65]:
    for d in [-0.4,0.4]:
        ph=2*np.pi*(f+d)*t
        out+=0.06*(np.sin(ph)+0.3*np.sin(2*ph)+0.15*np.sin(3*ph))
out*=0.5+0.5*env(0,1.2)
# music box plinks
notes=[(0.2,880),(0.7,1046.5),(1.2,987.8),(1.7,830.6),(2.9,659.3),(3.4,622.3),(3.9,587.3)]
for st,f in notes:
    m=t>=st; tt=t[m]-st
    out[m]+=0.12*np.sin(2*np.pi*f*tt)*np.exp(-tt*3.5)+0.04*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*6)
# rising rumble as the creature rises, hit when eyes open (~2.4s)
rng=np.random.default_rng(3); n=rng.standard_normal(len(t))
k=np.ones(400)/400; rumble=np.convolve(n,k,'same')*8
out+=rumble*0.25*env(0.4,2.4)
m=t>=2.4; tt=t[m]-2.4
out[m]+=0.5*np.sin(2*np.pi*(45-10*tt)*tt)*np.exp(-tt*1.8)
out[m]+=0.12*np.sin(2*np.pi*233.08*tt)*np.exp(-tt*0.9)  # dissonant tone
out*=1-env(4.6,5.0)*0.8
out/=np.abs(out).max()/0.85
d=(out*32767).astype(np.int16)
w=wave.open('audio.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(d.tobytes()); w.close()
