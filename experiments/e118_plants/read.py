"""e118: plants at metres read against the lines written before the run.

    uv run python experiments/e118_plants/read.py [prefix]      (default: this experiment's results/main)

Prints the reading and writes `<prefix>_reading.csv` and, beside it, `provenance.csv` (the window and every
threshold). Places are the cells of 125 m; wood, field and crown are a m2 of a cell's soil.
"""
import csv, json, os, sys
import numpy as np

LOW = 300        # m: lowlands are land under this
WET, DRY = 2 / 3, 1 / 3  # the lowlands' wettest third and driest third, by the kept years' rain
LINE = 0.05      # a height band is under trees while its crowns take this share of the light or more
BAND = 200       # m: the height bands of the tree line
OLD = 20         # years after the sowing: a tree that became a thing by then is one of the first
TREE = np.dtype([('x', '<f4'), ('y', '<f4'), ('h', '<f4'), ('r', '<f4'), ('leaf', '<f4'), ('wood', '<f4'), ('age', '<f4'),
                 ('tough', '<f4'), ('g', '<u4'), ('born', '<u4')])

pre = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'results', 'main')
rows = []
log = list(csv.DictReader(open(pre + '_log.csv')))
m = json.load(open(pre + '_maps.json')); n = m['n']; F = m['fields']; S = m['static']; Y = len(m['years'])
a = np.fromfile(pre + '_maps.bin', dtype='<f4')
ann = a[:Y * len(F) * n * n].reshape(Y, len(F), n, n).mean(0)
st = a[Y * len(F) * n * n:].reshape(len(S), n, n)
g = lambda k: ann[F.index(k)]
s = lambda k: st[S.index(k)]
land = s('sea') < 0.5; elev = s('elev'); lat = s('lat'); rain = g('rain')
sn = json.load(open(pre + '_snaps.json')); sow = sn['sow']; last = sn['years'][-1]; T = sn['traits']; nt = len(T)
tr = np.fromfile(f'{pre}_traits_{last}.bin', dtype='<f4').reshape(2 * nt + 4, n, n)
# the field, the trees' wood and the light the crowns take: the kept years' means (a snapshot is the end of a winter)
field, wood, crown = g('field'), g('wood'), g('crown')
trees = np.fromfile(f'{pre}_trees_{last}.bin', dtype=TREE)
soil = land & (np.isfinite(tr[0]) | (field > 0) | (wood > 0))

print(f'{pre}: sown in year {sow}, read at year {last} ({last - sow} years of plants); maps of years {m["years"][0]}-{m["years"][-1]}')

# 1. it stands, every ledger closed
plant = [r for r in log if int(r['year']) > sow]
errs = {k: max(float(r[k]) for r in plant) for k in ('water_err', 'a_err', 'b_err', 'c_err')}
f0, f1 = plant[len(plant) // 2], plant[-1]
print(f'1. ledgers: worst water {errs["water_err"]:.0e}, A {errs["a_err"]:.0e}, B {errs["b_err"]:.0e}, matter {errs["c_err"]:.0e}')
print(f'   field {float(f1["field"]):.2f} kg/m2 (half way {float(f0["field"]):.2f}), wood {float(f1["wood"]):.2f} ({float(f0["wood"]):.2f}), litter {float(f1["litter"]):.2f}; '
      f'trees {f1["trees"]} to {float(f1["tree_h_max"]):.1f} m; a year of plants {np.mean([float(r["secs"]) for r in plant]):.0f} s')
rows.append(dict(part='land', field=float(f1['field']), wood=float(f1['wood']), litter=float(f1['litter']), trees=int(f1['trees']),
                 tree_h_max=float(f1['tree_h_max']), crown=float(f1['crown']), **{k: f'{v:.1e}' for k, v in errs.items()}))

# 2. crowns over the land; wood on the wet ground against the dry
low = land & (elev < LOW) & soil
q_wet, q_dry = np.quantile(rain[low], WET), np.quantile(rain[low], DRY)
wet, dry = low & (rain >= q_wet), low & (rain <= q_dry)
print(f'2. crowns take {100 * crown[soil].mean():.1f}% of the light over the land\'s soil (the kept years\' mean; {100 * (crown[soil] >= LINE).mean():.0f}% of its cells are under trees)')
rows[0]['crown'] = float(crown[soil].mean())
print(f'   lowlands: wettest third (rain over {q_wet:.0f} mm) wood {wood[wet].mean():.2f} kg/m2, crowns {100 * crown[wet].mean():.1f}%, field {field[wet].mean():.2f}; '
      f'driest third (under {q_dry:.0f} mm) wood {wood[dry].mean():.2f}, crowns {100 * crown[dry].mean():.1f}%, field {field[dry].mean():.2f}; wood x{wood[wet].mean() / max(wood[dry].mean(), 1e-9):.1f}')
rows.append(dict(part='lowland wettest third', cells=int(wet.sum()), rain=round(float(rain[wet].mean())), wood=float(wood[wet].mean()), crown=float(crown[wet].mean()), field=float(field[wet].mean())))
rows.append(dict(part='lowland driest third', cells=int(dry.sum()), rain=round(float(rain[dry].mean())), wood=float(wood[dry].mean()), crown=float(crown[dry].mean()), field=float(field[dry].mean())))
for lo, hi in [(0, 32), (32, 64), (64, 96), (96, 128)]:
    sel = low.copy(); sel[:lo] = False; sel[hi:] = False
    if sel.any():
        print(f'   lowlands {lat[lo, 0]:.0f}-{lat[hi - 1, 0]:.0f} N: wood {wood[sel].mean():.2f}, crowns {100 * crown[sel].mean():.1f}%, field {field[sel].mean():.2f}, rain {rain[sel].mean():.0f} mm, '
              f'burnt {100 * g("burnt")[sel].mean() / 625:.2f}% a year')
        rows.append(dict(part=f'lowland {lat[lo, 0]:.0f}-{lat[hi - 1, 0]:.0f}N', cells=int(sel.sum()), rain=round(float(rain[sel].mean())), wood=float(wood[sel].mean()),
                         crown=float(crown[sel].mean()), field=float(field[sel].mean()), burnt=float(g('burnt')[sel].mean() / 625)))

# 3. a tree line
print('3. by height:')
top = None
for lo in range(0, int(elev[land].max()) + BAND, BAND):
    sel = land & soil & (elev >= lo) & (elev < lo + BAND)
    if not sel.any():
        continue
    hmax = g('height')[sel].max()
    print(f'   {lo}-{lo + BAND} m: {sel.sum()} cells, crowns {100 * crown[sel].mean():.1f}%, wood {wood[sel].mean():.2f}, field {field[sel].mean():.2f}, tallest tree {hmax:.1f} m, T {g("temp")[sel].mean():.1f} C')
    rows.append(dict(part=f'height {lo}-{lo + BAND} m', cells=int(sel.sum()), wood=float(wood[sel].mean()), crown=float(crown[sel].mean()), field=float(field[sel].mean()), tree_h_max=float(hmax)))
    if crown[sel].mean() >= LINE:
        top = lo + BAND
print(f'   crowns take {100 * LINE:.0f}% of the light or more up to {top} m (the land rises to {elev[land].max():.0f} m)')

# 4. leaves north and south
print('4. traits by latitude (the mean of the genotypes by mass):')
for grp, off, w in (('field', 0, field), ('trees', nt, wood)):
    for lo, hi in [(0, 64), (64, 128)]:
        sel = land.copy(); sel[:lo] = False; sel[hi:] = False; sel &= np.isfinite(tr[off]) & (w > 0)
        if sel.any():
            v = {T[i]: float(np.average(tr[off + i][sel], weights=w[sel])) for i in range(nt)}
            print(f'   {grp} {lat[lo, 0]:.0f}-{lat[hi - 1, 0]:.0f} N: leaf A {100 * v["leaf_a"]:.2f}%, B {100 * v["leaf_b"]:.2f}%, shed {v["shed"]:.2f} a year, t_opt {v["t_opt"]:.1f} C, '
                  f'deep {v["deep"]:.2f}, height {v["height"]:.1f} m, wood share {v["alloc_wood"]:.2f}, store {v["alloc_store"]:.2f}')
            rows.append(dict(part=f'{grp} traits {lat[lo, 0]:.0f}-{lat[hi - 1, 0]:.0f}N', **{k: round(x, 4) for k, x in v.items()}))

# 5. lives turn over
first = trees['born'] <= sow + OLD
died = sum(float(r['fallen']) for r in plant[-10:]) / 10
print(f'   (with leaf at the winter\'s end: {100 * (trees["leaf"] > 0.01).mean():.0f}% of them)')
print(f'5. trees at year {last}: {len(trees)}, heights 10/50/90/99% {np.percentile(trees["h"], [10, 50, 90, 99]).round(1)} m, crowns\' radius 50/90/99% {np.percentile(trees["r"], [50, 90, 99]).round(1)} m')
print(f'   {100 * first.mean():.0f}% became things within {OLD} years of the sowing ({100 * trees["wood"][first].sum() / max(trees["wood"].sum(), 1e-9):.0f}% of the wood); '
      f'{died:.0f} trees fall a year ({100 * died / max(len(trees), 1):.2f}% of them); mean age {float(f1["tree_age"]):.0f} years; genotypes with trees {len(np.unique(trees["g"]))}, '
      f'born after the sowing {100 * float(f1["mutant_share"]):.1f}% of the living mass')
rows.append(dict(part='trees', trees=len(trees), first_share=float(first.mean()), fall_a_year=died, genotypes=int(len(np.unique(trees['g'])))))

keys = []
for r in rows:
    for k in r:
        if k not in keys:
            keys.append(k)
with open(pre + '_reading.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys, lineterminator='\n'); w.writeheader(); w.writerows(rows)
with open(os.path.join(os.path.dirname(pre), 'provenance.csv'), 'w', newline='') as f:
    w = csv.writer(f, lineterminator='\n'); w.writerow(['what', 'value'])
    w.writerow(['run', os.path.basename(pre)]); w.writerow(['snapshot read (year)', last]); w.writerow(['sown (year)', sow])
    w.writerow(['maps read (the kept years, their mean)', ' '.join(str(y) for y in m['years'])])
    w.writerow(['lowland: land under (m)', LOW]); w.writerow(['wet and dry lowlands: thirds of the kept years\' rain', f'over {q_wet:.0f} mm, under {q_dry:.0f} mm'])
    w.writerow(['under trees: crowns take this share of the light or more', LINE]); w.writerow(['height bands (m)', BAND])
    w.writerow(['one of the first trees: a thing within (years of the sowing)', OLD]); w.writerow(['trees falling a year: mean of the last (years)', 10])
