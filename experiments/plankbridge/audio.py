import numpy as np, wave
sr=44100; T=17.5; t=np.arange(int(sr*T))/sr
out=np.zeros_like(t)
def add(st, sig):
    i=int(st*sr); n=min(len(sig),len(out)-i); out[i:i+n]+=sig[:n]
def pop(st,f):
    tt=np.arange(int(sr*0.5))/sr
    add(st, 0.35*np.sin(2*np.pi*(f*(1+2*np.exp(-tt*25)))*tt)*np.exp(-tt*9))
for st,f in [(2.8,300),(5.0,340),(6.6,380),(8.2,430),(9.8,480)]: pop(st,f)
# creak at plank
tt=np.arange(int(sr*0.6))/sr; add(3.4, 0.08*np.sin(2*np.pi*(180+60*np.sin(tt*30))*tt)*np.exp(-tt*4))
# toll ding
tt=np.arange(int(sr*1.2))/sr; add(10.5, 0.25*(np.sin(2*np.pi*1318*tt)+0.4*np.sin(2*np.pi*2637*tt))*np.exp(-tt*4))
# footsteps (soft ticks) 3.4..15.5
for s in np.arange(3.4,15.5,0.29):
    tt=np.arange(int(sr*0.05))/sr; rng=np.random.default_rng(int(s*100)); add(s, 0.05*rng.standard_normal(len(tt))*np.exp(-tt*80))
# end boing
tt=np.arange(int(sr*0.6))/sr; add(15.6, 0.3*np.sin(2*np.pi*(250+300*tt)*tt)*np.exp(-tt*6))
# light marimba bed
for k,st in enumerate(np.arange(0.2,16.5,0.58)):
    f=[392,440,523.25,440,392,329.6][k%6]; tt=np.arange(int(sr*0.4))/sr; add(st, 0.06*np.sin(2*np.pi*f*tt)*np.exp(-tt*8))
out*=np.clip((T-t)/0.5,0,1)
out/=np.abs(out).max()/0.8
w=wave.open('audio.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
