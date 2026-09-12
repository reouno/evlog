// Following a line of descent: the world is watched through one body, and when that body breeds
// the watching goes on with its child.
//
// The two ways of doing it are not the same thing. A recording knows how it ends, so a line can
// be walked back from a body alive in the last frame to the first of its line (`/lines`, worked
// out by the replay server, which holds the whole recording). Followed forward, every birth on
// that path goes to the child that leads to the end, and the watching never stops. A body picked
// off the screen has no such future: at each of its births the watching goes to the parent or to
// the child at random, and when that line dies out there is nothing left to follow.
/** Where on the line `step` falls: the last body of it that has appeared by then. The bodies
 * that no frame caught are not in the path, so this steps over them to the next one seen. */
export function alongLine(line, step) {
    let lo = 0, hi = line.path.length - 1;
    while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (line.path[mid][1] <= step)
            lo = mid;
        else
            hi = mid - 1;
    }
    // A body of the line can die a frame or two before its child is first caught in one. The line
    // is in the child by then, so the watching waits on it rather than on a body that is gone.
    while (lo + 1 < line.path.length && line.path[lo][2] < step)
        lo++;
    return lo;
}
/** The body of `line` to follow at `step`. */
export function onLine(line, step) {
    return line.path[alongLine(line, step)][0];
}
/** A walk from a body picked off the screen: at each of its births it goes on with the parent or
 * the child, evenly, and it ends where the line does. It reads the frames the watcher has played
 * through, not the ones that have arrived, so it follows what is on the screen. */
export class Walk {
    constructor(id, step) {
        this.id = id;
        this.at = step;
        this.ended = false;
    }
    /** Play the walk up to `step` and give the body to watch, or null once the line has ended. */
    follow(world, step) {
        if (this.ended)
            return null;
        if (step < this.at) {
            this.at = step; // the watcher went back; the walk holds the body it is on
            return this.id;
        }
        for (const s of world.steps) {
            if (s <= this.at || s > step)
                continue;
            this.at = s;
            const f = world.frames.get(s);
            if (f.births) {
                for (const [child, parent] of f.births) {
                    if (parent === this.id && Math.random() < 0.5)
                        this.id = child;
                }
            }
            // Every living body is in every frame, so a body that is not in this one is gone.
            if (!f.index.has(this.id)) {
                this.ended = true;
                return null;
            }
        }
        return this.id;
    }
}
//# sourceMappingURL=line.js.map