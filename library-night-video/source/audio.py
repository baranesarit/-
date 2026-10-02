import numpy as np
from scipy.signal import fftconvolve, butter, lfilter
from scipy.io import wavfile
sr=44100;T=50;n=sr*T;t=np.arange(n)/sr
L=np.zeros(n);Rr=np.zeros(n);rs=np.random.default_rng(1)
def f(m):return 440*2**((m-69)/12)
def add(sig,start,pan=0.,g=1.):
    i=int(start*sr);sig=sig[:max(0,n-i)];l=np.sqrt((1-pan)/2);r=np.sqrt((1+pan)/2)
    L[i:i+len(sig)]+=sig*g*l;Rr[i:i+len(sig)]+=sig*g*r
def env(d,a=.005,dec=1.):
    tt=np.arange(int(d*sr))/sr;return np.minimum(tt/a,1)*np.exp(-tt/dec),tt
def bell(m,d=2.5,g=.25):
    e,tt=env(d,.002,.7);fr=f(m);return g*e*(np.sin(2*np.pi*fr*tt)+.4*np.sin(2*np.pi*fr*2.76*tt)*np.exp(-tt*3)+.25*np.sin(2*np.pi*fr*5.4*tt)*np.exp(-tt*6))
def pad(ms,start,dur,g=.06):
    tt=np.arange(int(dur*sr))/sr;s=np.zeros_like(tt)
    for m in ms:
        for det in(-.12,0,.12):s+=np.sin(2*np.pi*f(m+det)*tt+rs.random()*6)+.3*np.sin(2*np.pi*2*f(m+det)*tt)
    fade=np.minimum(np.minimum(tt/1.5,1),np.minimum((dur-tt)/1.5,1));lfo=.7+.3*np.sin(2*np.pi*.15*tt)
    return s*fade*lfo*g/len(ms)
def boom(d=2.5,g=.9,fr=48):
    e,tt=env(d,.003,.6);ph=2*np.pi*np.cumsum(fr*(1+2*np.exp(-tt*8)))/sr;return g*e*np.sin(ph)+g*.3*rs.standard_normal(len(tt))*np.exp(-tt*25)
def whoosh(d=1.6,g=.25,rev=False):
    tt=np.arange(int(d*sr))/sr;nz=rs.standard_normal(len(tt));b,a=butter(2,[400/(sr/2),6000/(sr/2)],'band');nz=lfilter(b,a,nz)
    e=(tt/d)**2 if not rev else np.sin(np.pi*tt/d);return g*nz*e
def heart(g=.7):
    s=np.zeros(int(.8*sr))
    for o,a in((0,1),(.18,.7)):
        e,tt=env(.25,.004,.06);x=a*e*np.sin(2*np.pi*55*tt);i=int(o*sr);s[i:i+len(x)]+=x
    return s*g
# harmony: D minor -> Bb -> Gm -> A ; tempo
prog_=[[50,57,62,65],[46,53,58,62],[43,50,55,58],[45,52,57,61]]
for k in range(0,50,4):
    add(pad(prog_[(k//4)%4],k,4.6),k,0,1)
# deep drone
add(.07*np.sin(2*np.pi*f(38)*t)*np.minimum(t/3,1)*np.minimum((T-t)/2,1),0)
# music box melody (D harmonic minor), sections
mel=[74,77,81,79,77,76,77,74, 73,76,79,77,76,74,73,69, 74,77,81,86,84,82,81,79, 77,81,79,77,76,73,74,74]
beat=.5
def melody(st,en,step=beat,oct=0,g=.18):
    i=0;tm=st
    while tm<en:
        add(bell(mel[i%len(mel)]+oct,g=g),tm,pan=np.sin(i)*.5);i+=1;tm+=step
melody(0.4,6)
melody(12.4,18.4,step=1.0,oct=-12,g=.12)
melody(19.0,32,step=.25,g=.12)
melody(32.2,42.6,step=.5,g=.14)
melody(42.6,48.5,step=.25,oct=12,g=.08)
melody(42.6,48.5,step=1,oct=-12,g=.12)
# clock tick in scene2 and midnight chimes
for k in np.arange(6.4,9.4,.5):
    e,tt=env(.05,.001,.01);add(.25*e*rs.standard_normal(len(tt)),k,pan=.3 if int(k*2)%2 else -.3)
for i,k in enumerate([9.45,10.6,11.75]):add(bell(50,4,.5)+bell(62,4,.25),k)
# heartbeat in scene3
for k in np.arange(12.6,18.4,.85):add(heart(),k)
# booms/whooshes at transitions
for k in [6.2,12.4,25.4,32.2]:add(whoosh(1.2,.18),k-1.2);add(boom(2,.5),k)
add(whoosh(2.0,.35),16.6);add(boom(3.5,1.0,40),18.6)
# shimmer glissando at title
for i in range(24):add(bell(74+i,1.5,.09),18.6+i*.04,pan=(i%2)*.6-.3)
# stamp
add(boom(2.5,1.0,55),37.4+.75)
for i in range(16):add(bell(86-i%5*3,1.2,.07),38.2+i*.06,pan=np.sin(i))
# final chord
add(pad([50,57,62,65,69],46,4,.12),46)
for i,m in enumerate([62,65,69,74,77,81,86]):add(bell(m,3,.12),46+i*.08)
# reverb
ir_len=int(2.8*sr);it=np.arange(ir_len)/sr
def ir(seed):g=np.random.default_rng(seed).standard_normal(ir_len)*np.exp(-it*2.2);g[0]=0;return g/np.sqrt(np.sum(g**2))*0.5
Lw=L+fftconvolve(L,ir(5))[:n]*.9;Rw=Rr+fftconvolve(Rr,ir(6))[:n]*.9
out=np.stack([Lw,Rw],1);out*=np.minimum(1,(T-t)/1.0)[:,None];out/=np.max(np.abs(out))/0.89
wavfile.write('music.wav',sr,(out*32767).astype(np.int16))
