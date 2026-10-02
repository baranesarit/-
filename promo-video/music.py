import math, random, wave, array
SR=44100; T=36.2; N=int(SR*T); L=[0.0]*N; R=[0.0]*N
random.seed(1); beat=0.5
def add(buf,start,samples,g=1.0):
    s=int(start*SR)
    for i,v in enumerate(samples):
        if 0<=s+i<N: buf[s+i]+=v*g
def both(start,samples,g=1.0,pan=0.0):
    add(L,start,samples,g*(1-pan)); add(R,start,samples,g*(1+pan))
def kick():
    n=int(.35*SR); out=[];ph=0
    for i in range(n):
        t=i/SR; f=50+110*math.exp(-t*30); ph+=2*math.pi*f/SR
        out.append(math.sin(ph)*math.exp(-t*8))
    return out
def noise(d,decay,hp=False):
    out=[];prev=0
    for i in range(int(d*SR)):
        x=random.uniform(-1,1); y=x-prev if hp else x; prev=x
        out.append(y*math.exp(-i/SR*decay))
    return out
def tone(freqs,d,decay=4,wave='saw'):
    out=[]
    for i in range(int(d*SR)):
        t=i/SR; v=0
        for f in freqs:
            p=(t*f)%1
            v+= (2*p-1) if wave=='saw' else (1 if p<.5 else -1) if wave=='sq' else math.sin(2*math.pi*f*t)
        env=min(1,t*200)*math.exp(-t*decay)
        out.append(v/len(freqs)*env)
    return out
def lp(x,a=.15):
    y=0;o=[]
    for v in x: y+=a*(v-y); o.append(y)
    return o
K=kick(); CL=noise(.2,25); HH=noise(.05,90,True)
mid=lambda m:440*2**((m-69)/12)
chords=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]  # C Am F G
bass=[36,33,29,31]
stabs={}
nbeats=int(36/beat)
for b in range(nbeats):
    t=b*beat; bar=b//4; ch=chords[bar%4]
    intro = t<4
    both(t,K,.9 if not intro or b%2==0 else .7)
    if b%2==1 and not intro: both(t,CL,.35)
    for h in (0,.25): both(t+h,HH,.18 if h else .1,pan=.3)
    if not intro:
        key=(bar%4,'b')
        if key not in stabs: stabs[key]=lp(tone([mid(bass[bar%4])],.24,6,'saw'),.25)
        both(t+.25,stabs[key],.45)
    key=(bar%4,'c')
    if key not in stabs: stabs[key]=lp(tone([mid(n+12) for n in ch]+[mid(n+12)*1.006 for n in ch],.22,9,'saw'),.35)
    if b%4 in (0,1,2,3): both(t+(.25 if b%2 else 0),stabs[key],.22,pan=-.2 if b%2 else .2)
    # arp sparkle
    if t>=8:
        for k in range(2):
            n=ch[(b*2+k)%3]+24
            kk=('a',n)
            if kk not in stabs: stabs[kk]=tone([mid(n)],.2,14,'sq')
            both(t+k*.25,stabs[kk],.06,pan=.4 if k else -.4)
# impacts on scene cuts + risers
for c in [4,8.5,15.5,20.5,25,29]:
    both(c,lp(noise(1.2,3),.3),.5); both(c,K,.6)
    r=[random.uniform(-1,1)*(i/(SR*1.0))**2 for i in range(int(SR*1.0))]
    both(c-1.0,lp(r,.5),.18)
# final hit
both(29,tone([mid(48),mid(55),mid(60),mid(64)],3,1.2,'saw'),.25)
fade=int(2*SR)
m=max(max(abs(v) for v in L),max(abs(v) for v in R))
a=array.array('h')
for i in range(N):
    g=0.89/m*(min(1,(N-i)/fade))
    a.append(int(max(-1,min(1,L[i]*g))*32767)); a.append(int(max(-1,min(1,R[i]*g))*32767))
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes()); w.close()
