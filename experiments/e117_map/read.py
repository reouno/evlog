"""e117: the map's climate read from a run's maps - by latitude (lowlands), by height, by an island's two sides.

    uv run python experiments/e117_map/read.py [prefix]      (default: this experiment's results/map)

Prints the reading and writes `<prefix>_reading.csv` and, beside it, `provenance.csv` (the window and every
threshold). Months run from the spring equinox: quarters are spring, summer, autumn, winter.
"""
import csv, json, os, sys, numpy as np
LOW = 300      # m: lowlands are land under this
LYING = 5      # mm of water: snow lies on a cell in a month whose mean pack is over this
SIDE = 2       # cells: an island's lowlands west and east of its summit start this far from it
ISLAND = 60    # cells: islands smaller than this are not read by side
pre=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),'results','map')
rows=[]
m=json.load(open(pre+'_maps.json')); n=m['n']; F=m['fields']; S=m['static']; Y=len(m['years'])
a=np.fromfile(pre+'_maps.bin',dtype='<f4')
ann=a[:Y*len(F)*n*n].reshape(Y,len(F),n,n).mean(0); st=a[Y*len(F)*n*n:].reshape(len(S),n,n)
g=lambda k: ann[F.index(k)]; s=lambda k: st[S.index(k)]
land=s('sea')<0.5; elev=s('elev'); lat=s('lat')
sj=json.load(open(pre+'_season.json')); MF=sj['fields']
mo=np.fromfile(pre+'_season.bin',dtype='<f4').reshape(12,len(MF),n,n)
M=lambda k: mo[:,MF.index(k)]
# months run from the spring equinox: 0-2 spring, 3-5 summer, 6-8 autumn, 9-11 winter
print(pre, 'annual land rain %.0f mm, T %.1f'%(g('rain')[land].mean(), g('temp')[land].mean()))
print('band        T    rain  | spr  sum  aut  win (rain mm) | summer share | fill spr sum aut win | snow months | T win/sum')
for lo,hi in [(0,32),(32,64),(64,96),(96,128)]:
    sel=land.copy(); sel[:lo]=False; sel[hi:]=False; sel&=elev<LOW
    r=[M('rain')[q*3:q*3+3].sum(0)[sel].mean() for q in range(4)]
    f=[M('fill')[q*3:q*3+3].mean(0)[sel].mean() for q in range(4)]
    snowm=(M('snow')[:,sel]>LYING).mean(1).sum()
    tw=M('temp')[9:12].mean(0)[sel].mean(); ts=M('temp')[3:6].mean(0)[sel].mean()
    rows.append(dict(part=f'lowland {lat[lo,0]:.0f}-{lat[hi-1,0]:.0f}N',cells=int(sel.sum()),temp=round(float(g('temp')[sel].mean()),2),rain=round(float(sum(r))),rain_spring=round(float(r[0])),rain_summer=round(float(r[1])),rain_autumn=round(float(r[2])),rain_winter=round(float(r[3])),fill_summer=round(float(f[1]),3),fill_winter=round(float(f[3]),3),snow_months=round(float(snowm),2),temp_winter=round(float(tw),2),temp_summer=round(float(ts),2)))
    print(f'{lat[lo,0]:.0f}-{lat[hi-1,0]:.0f}N low {g("temp")[sel].mean():5.1f} {sum(r):6.0f} | {r[0]:4.0f} {r[1]:4.0f} {r[2]:4.0f} {r[3]:4.0f} | {r[1]/sum(r):.2f} | {f[0]:.2f} {f[1]:.2f} {f[2]:.2f} {f[3]:.2f} | {snowm:.1f} | {tw:.1f}/{ts:.1f}')
for b in [(300,800),(800,1200),(1200,1900)]:
    sel=land&(elev>=b[0])&(elev<b[1])
    if sel.any():
        snowm=(M('snow')[:,sel]>LYING).mean(1).sum()
        rows.append(dict(part=f'height {b[0]}-{b[1]} m',cells=int(sel.sum()),temp=round(float(g('temp')[sel].mean()),2),rain=round(float(g('rain')[sel].mean())),snow_months=round(float(snowm),2)))
        print(f'elev {b}: cells {sel.sum()} lat {lat[sel].mean():.0f} T {g("temp")[sel].mean():.1f} rain {g("rain")[sel].mean():.0f} snow months {snowm:.1f} deepest month mean {M("snow")[:,sel].mean(1).max():.0f} mm')
# the high island: lowlands (<300 m) west and east of its summit
lab=np.zeros((n,n),int); k=0
for y in range(n):
    for x in range(n):
        if land[y,x] and not lab[y,x]:
            k+=1; stack=[(y,x)]; lab[y,x]=k
            while stack:
                yy,xx=stack.pop()
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    u,v=yy+dy,xx+dx
                    if 0<=u<n and 0<=v<n and land[u,v] and not lab[u,v]: lab[u,v]=k; stack.append((u,v))
R=g('rain')
for i in range(1,k+1):
    isl=lab==i
    if isl.sum()<ISLAND: continue
    top=np.unravel_index(np.where(isl,elev,-1).argmax(),elev.shape)
    low=isl&(elev<LOW)
    xs=np.arange(n)[None,:].repeat(n,0)
    w=low&(xs<top[1]-SIDE); e=low&(xs>top[1]+SIDE)
    if w.sum()>5 and e.sum()>5:
        rows.append(dict(part=f'island {isl.sum()*0.015625:.1f} km2 top {elev[top]:.0f} m',cells=int(isl.sum()),rain_west=round(float(R[w].mean())),rain_east=round(float(R[e].mean())),rain_driest=round(float(R[isl].min())),rain_wettest=round(float(R[isl].max()))))
        print(f'island {isl.sum()*0.015625:.1f} km2 top {elev[top]:.0f} m at lat {lat[top]:.0f}: lowland rain west of the summit {R[w].mean():.0f} mm, east {R[e].mean():.0f} mm (x{R[w].mean()/R[e].mean():.1f}); driest {R[isl].min():.0f}, wettest {R[isl].max():.0f}')
fl=M('flow'); tot=fl[:,land].sum(1)
print('land run-off by month (share of the year, from the spring equinox):', ' '.join(f'{v:.2f}' for v in tot/tot.sum()))
keys=[]
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
with open(pre+'_reading.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
with open(os.path.join(os.path.dirname(pre),'provenance.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['what','value'])
    w.writerow(['run',os.path.basename(pre)]); w.writerow(['years read (the kept years, their mean)',' '.join(str(y) for y in m['years'])])
    w.writerow(['months','12 from the spring equinox; quarters of 3'])
    w.writerow(['lowland: land under (m)',LOW]); w.writerow(['snow lies: a month\'s mean pack over (mm of water)',LYING])
    w.writerow(['an island\'s sides: lowland cells further west or east of its summit than (cells of 125 m)',SIDE])
    w.writerow(['islands read by side: at least (cells)',ISLAND]); w.writerow(['latitude bands','four of 32 rows'])
