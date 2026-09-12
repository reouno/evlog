// What the world says it is, as the browser reads it: the one place the shapes of the wire live.
//
// This file mirrors `viewer/src/wire.rs`, which writes the header by hand. `cargo test -p viewer`
// reads this file and compares it with the header the Rust actually writes, so a field renamed
// on one side is a failing build rather than a blank screen. A field that only some worlds have
// is optional here (`?`) and the test lets it be missing; everything else must be in the header.
/** The records the stream is cut into (`KIND_*` in wire.rs). */
export const RECORD = { HEADER: 0, BODY: 1, FRAME: 2 };
//# sourceMappingURL=wire.js.map