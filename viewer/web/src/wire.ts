// What the world says it is, as the browser reads it: the one place the shapes of the wire live.
//
// This file mirrors `viewer/src/wire.rs`, which writes the header by hand. `cargo test -p viewer`
// reads this file and compares it with the header the Rust actually writes, so a field renamed
// on one side is a failing build rather than a blank screen. A field that only some worlds have
// is optional here (`?`) and the test lets it be missing; everything else must be in the header.

/** How a cell layer's byte stands for a value (`Scale` in wire.rs). */
export type Scale = 'linear' | 'sqrt' | 'log';

/** How a number in the agent record is packed. */
export type NumType = 'u8' | 'u16' | 'u32' | 'f32';

/** The records the stream is cut into (`KIND_*` in wire.rs). */
export const RECORD = { HEADER: 0, BODY: 1, FRAME: 2 } as const;

/** One per-cell layer of the world. `name` is what the browser draws it as: `plant` is what
 * stands on a cell, `fruit` and `carrion` what lies on it. A name it does not know is ignored. */
export interface LayerSpec {
  name: string;
  max: number;
  scale: Scale;
}

/** The fields of a body in a frame, in the order wire.rs writes them. The browser reads the
 * record off the header rather than from here; this is what those names are, so that a body's
 * field is spelled the same everywhere. */
export type AgentField =
  | 'id'
  | 'lineage'
  | 'body'
  | 'x'
  | 'y'
  | 'facing'
  | 'diet'
  | 'fill'
  | 'energy'
  | 'ripe'
  | 'fat'
  | 'age'
  | 'born';

/** One field of the agent record: where it is is worked out from the order, and a byte with a
 * `max` is that share of it. */
export interface AgentFieldSpec {
  name: AgentField;
  type: NumType;
  max?: number;
}

/** The run's laws and arguments, as the experiment wrote them. The browser reads the few it
 * draws with (the season is worked out from the law itself: see `World.seasonOf`); the rest
 * rides along for whoever looks at `world.params` in the console. */
export interface Params {
  relief?: number;
  water_rain?: number;
  water_evap?: number;
  depth?: number;
  weather?: string;
  amplitude?: number;
  season?: number;
  winter?: string;
  max_age?: number;
  wear?: number;
  thirst?: number;
  [key: string]: unknown;
}

/** What the world is, sent once before anything else. */
export interface Header {
  version: number;
  experiment: string;
  live: boolean;
  w: number;
  h: number;
  sub: number; // sub-cells per cell along one side: a body cell is 1/sub of a world cell
  stride: number;
  layer_stride: number;
  layers: LayerSpec[];
  globals: string[];
  blocks: string[]; // block kinds by index, 0 = empty
  deaths: string[]; // what a body dies of, by the number a frame carries (empty: none are sent)
  agent_record: AgentFieldSpec[];
  params: Params;
  height: number[];
  band: number[];
  /** Added by the replay server, not by `header_json`: what the recording holds. */
  replay?: { first: number; last: number; frames: number; bodies: number };
}

/** What `/state` says before the stream starts. */
export interface State {
  live: boolean;
  speed?: number;
  paused?: boolean;
  watchers?: number;
}

/** A body's numbers in one frame, a flat array per field: there are thousands of bodies a frame
 * and an object each would be an allocation each. */
export type AgentColumns = Record<AgentField, Uint8Array | Uint16Array | Uint32Array>;

/** The cell layers at one moment, by the header's names, as physical values. `wood` is not a
 * layer of the world: the browser remembers it (`World.woodAt`). */
export interface Layers {
  plant?: Float32Array;
  fruit?: Float32Array;
  carrion?: Float32Array;
  soil?: Float32Array;
  water?: Float32Array;
  root?: Float32Array;
  wood?: Float32Array;
  [name: string]: Float32Array | undefined;
}
