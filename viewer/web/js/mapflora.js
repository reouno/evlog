/**
 * The plants of the map at real size (#135, e118): a run's snapshots - its trees, one record each, the field on the
 * fine cells - and the year recorded with a snapshot: each month's leaf of the field (on a grid of 25 m) and of
 * every tree, and the fronts and the wind of every update of the climate.
 *
 * Read from `/data/snaps.json` (which years), `/data/trees_<year>.bin`, `/data/field_<year>.bin` and
 * `/data/year_<year>.bin`; a run without them has no flora and the page draws the bare map.
 */
const REC = 5; // fine cells a side of the year's grid
async function bin(url) {
    const r = await fetch(url);
    if (!r.ok)
        throw new Error(`${url}: ${r.status}`);
    return r.arrayBuffer();
}
export class Flora {
    constructor() {
        this.years = [];
        this.sow = 0;
        this.year = 0;
        this.ready = false;
        this.n = 0;
        this.g = 0;
        this.start = 79;
        // the trees of the snapshot
        this.count = 0;
        this.updates = 0;
        // the trees of each tile of `tile` fine cells, and the tile's crowns' mean leaf by month
        this.tile = 64;
        this.tiles = 0;
        this.byTile = [];
        // the day set: the two months about it and how far between
        this.m0 = 0;
        this.m1 = 0;
        this.f = 0;
    }
    /** Which years a run has; false if it has no plants. */
    async init(n) {
        const r = await fetch('data/snaps.json').catch(() => null);
        if (!r || !r.ok)
            return false;
        const j = await r.json();
        this.years = j.years;
        this.sow = j.sow;
        this.n = n;
        this.g = n / REC;
        return this.years.length > 0;
    }
    async load(year, status) {
        this.ready = false;
        status(`${year} 年目の木を読み込み中…`);
        const tb = await bin(`data/trees_${year}.bin`), REC_B = 40, k = tb.byteLength / REC_B, dv = new DataView(tb);
        this.count = k;
        const f32 = () => new Float32Array(k);
        this.x = f32();
        this.y = f32();
        this.h = f32();
        this.r = f32();
        this.tough = f32();
        this.age = f32();
        this.born = new Uint32Array(k);
        for (let t = 0; t < k; t++) {
            const o = t * REC_B;
            this.x[t] = dv.getFloat32(o, true);
            this.y[t] = dv.getFloat32(o + 4, true);
            this.h[t] = dv.getFloat32(o + 8, true);
            this.r[t] = dv.getFloat32(o + 12, true);
            this.age[t] = dv.getFloat32(o + 24, true);
            this.tough[t] = dv.getFloat32(o + 28, true);
            this.born[t] = dv.getUint32(o + 36, true);
        }
        status(`${year} 年目の草を読み込み中…`);
        const fb = await bin(`data/field_${year}.bin`), nn = this.n * this.n;
        this.leaf = new Uint8Array(fb, 0, nn);
        this.litter = new Uint8Array(fb, 2 * nn, nn);
        this.under = new Uint8Array(fb, 3 * nn, nn);
        this.burnt = new Uint8Array(fb, 4 * nn, nn);
        status(`${year} 年目の一年を読み込み中…`);
        const yb = await bin(`data/year_${year}.bin`), gg = this.g * this.g;
        this.mField = new Uint8Array(yb, 0, 12 * gg);
        this.mTree = new Uint8Array(yb, 12 * gg, 12 * k);
        const rest = yb.slice(12 * gg + 12 * k);
        this.weather = new Float32Array(rest);
        this.updates = this.weather.length / 3;
        // the trees by tile, and each tile's mean leaf by month (by crown area)
        this.tiles = this.n / this.tile;
        const lists = Array.from({ length: this.tiles * this.tiles }, () => []);
        const cell = 5;
        for (let t = 0; t < k; t++) {
            const ti = Math.min(this.tiles - 1, Math.floor(this.x[t] / cell / this.tile)), tj = Math.min(this.tiles - 1, Math.floor(this.y[t] / cell / this.tile));
            lists[tj * this.tiles + ti].push(t);
        }
        this.byTile = lists.map((l) => Uint32Array.from(l));
        this.tileLeaf = new Float32Array(12 * lists.length).fill(1);
        for (let q = 0; q < lists.length; q++) {
            let area = 0;
            const sum = new Float64Array(12);
            for (const t of lists[q]) {
                const a = this.r[t] * this.r[t];
                area += a;
                for (let m = 0; m < 12; m++)
                    sum[m] += (a * this.mTree[m * k + t]) / 255;
            }
            if (area > 0)
                for (let m = 0; m < 12; m++)
                    this.tileLeaf[m * lists.length + q] = sum[m] / area;
        }
        this.year = year;
        this.ready = true;
    }
    /** The day of the calendar year: the two months about it (the year's months run from the spring equinox). */
    setDay(day) {
        const u = (((day - this.start + 365) % 365) / 365) * 12 - 0.5, a = Math.floor(u);
        this.m0 = (a + 12) % 12;
        this.m1 = (a + 1) % 12;
        this.f = u - a;
    }
    /** The field's leaf at a fine cell on the day set, kg a m2: its month's on the grid, with the snapshot's detail. */
    fieldLeaf(i, j) {
        const g = this.g, c = Math.floor(j / REC) * g + Math.floor(i / REC), gg = g * g;
        const month = (this.mField[this.m0 * gg + c] * (1 - this.f) + this.mField[this.m1 * gg + c] * this.f) / 100;
        const then = this.mField[11 * gg + c] / 100; // the snapshot is the year's end
        const fine = this.leaf[j * this.n + i] / 100;
        return then > 0.005 ? Math.min(2.5, (fine * month) / then) : month;
    }
    /** A tree's leaf on the day set, as a share of its fullest month. */
    treeLeaf(t) {
        const k = this.count;
        return (this.mTree[this.m0 * k + t] * (1 - this.f) + this.mTree[this.m1 * k + t] * this.f) / 255;
    }
    /** A tile's crowns' leaf on the day set. */
    crownLeaf(q) {
        const k = this.byTile.length;
        return this.tileLeaf[this.m0 * k + q] * (1 - this.f) + this.tileLeaf[this.m1 * k + q] * this.f;
    }
    /** The weather of a moment of the recorded year: the latitude a front reaches south to (99: none) and the wind. */
    weatherAt(day, hour) {
        if (!this.updates)
            return { reach: 99, u: 5, v: 1 };
        const t = ((((day - this.start + 365) % 365) + hour / 24) / 365) * this.updates;
        const q = Math.min(this.updates - 1, Math.floor(t)) * 3;
        return { reach: this.weather[q], u: this.weather[q + 1], v: this.weather[q + 2] };
    }
}
//# sourceMappingURL=mapflora.js.map