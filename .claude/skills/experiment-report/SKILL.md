---
name: experiment-report
description: Build the report.html for an evlog experiment (charts with matplotlib, hand-drawn SVG diagram, paper-like structure, plain English). Use when an experiment has results and needs its report written or updated.
---

# Experiment report

Every experiment folder `experiments/eNNN_<name>/` ships a `report.html` built by its own `report.py`.
The reader does not know the code or the algorithms. Keep it short: if it is long, nobody reads it.

## Steps

1. Copy `template.py` from this skill folder to `experiments/eNNN_<name>/report.py`.
2. Fill in the `TODO` parts: data loading, the charts, the diagram, and the text.
3. Build from the repo root: `uv run python experiments/eNNN_<name>/report.py`.
4. Look at the result before calling it done: serve the folder (`python3 -m http.server 8765 --bind 127.0.0.1`), open it in the browser, and check both a light and a dark rendering for legend overlap, clipped labels, and diagram text colliding with lines. `file://` URLs do not work in the browser tool.
5. Commit `report.py` and `report.html` together with `results/`.

## Structure (paper-like, tone can stay casual)

1. Title and one-line subtitle (date, what was run)
2. **TL;DR** - a few sentences: the answer, and what comes next
3. **Question** - why this experiment, and the hypotheses as a short numbered list
4. **The world / Method** - what was built, with a mechanism diagram (Figure 1), then the runs and the list of measurements (one line each; this replaces a glossary)
5. **Results** - summary table, one Yes/No verdict per hypothesis, then charts grouped under short claim-style headings ("3.1 The population is stable")
6. **Discussion** - what it means, what surprised us, what it does not show
7. **Conclusion and next step**
8. **Appendix: data** - collapsed tables, pointer to `results/*.csv` and the build command

Write in plain English. One idea per paragraph. Numbers where possible. Do not restate a chart in prose; say what it means.

## Charts

- matplotlib, exported as SVG and inlined. Never hand-draw a chart.
- Chart chrome in mid-gray `#898781`, transparent background, so one image reads in light and dark mode. The rcParams in the template do this.
- Series colors in fixed slot order: `#2a78d6` blue, `#eb6834` orange, `#1baf7a` aqua, `#eda100` yellow, `#e87ba4` magenta. Same entity, same color across every chart.
- Legend above the plot area (`legend_above` in the template), at most 4 y ticks, x axis labeled with its unit (`step` for time series), `k` formatting for thousands. Helpers: `line_chart`, `stacked_area`, `hist_chart`.
- Every chart has a title and a one-line subtitle saying how to read it (what a flat line or a zero would mean).
- Two charts per row (`.grid2`). Put charts under the heading that states their claim.
- One y axis per chart. Two measures of different scale are two charts.

## Diagram

- Hand-written inline SVG, no library. Show the mechanism: which parts interact, what flows along each arrow, the numbers that matter (costs, thresholds, rates).
- Label every arrow. Use `currentColor` for lines and text; one accent color (`var(--s1)`) for the single element the argument hinges on.
- Text 12px, short labels; explanations go in the `<figcaption>`.
- Set `viewBox` to fit the content and keep 10-15px between text and any line it could touch.

## Conventions

- Everything in the report is English. Plain words over jargon; define a term once where it is first used.
- Keep `report.py` self-contained (standard library + matplotlib). No shared report library until several experiments need the same thing.

## Viewer (when the experiment has snapshots)

- Reuse the latest experiment's `VIEWER_JS` and `pack_frames` (e007 onward: any world size, frames as one gzip'd blob).
- Playback must be slow by default: 600 ms per frame in the long view, 250 ms in the clip, with a
  Slow / Normal / Fast selector (1x / 2x / 4x) next to Play. The user asked for this; do not speed it up again.
- Keep the marks: lineage color, white dot on agents that can bite, block legend, per-lineage label with teeth / armor / eyes.

## Length (from e012 on)

Reports had grown to the length of a paper by e011. Keep them short:

- TL;DR: at most 5 sentences. Question: one paragraph. Discussion: at most 3 paragraphs. Conclusion: one paragraph.
- Only charts that carry a claim. Aim for 6-8 charts in total, not 16. If two charts say the same thing, keep one.
- One paragraph of prose per results heading, and no restating of the summary table: give the number once.
- The summary table: at most 15 rows. Rare measures go to the appendix tables.
- Method: the mechanism diagram, the runs in one paragraph, the measures as one list. Do not repeat the README.

## Bodies of the lineages that prospered

Show them. For the lineages with the most agent-steps (or the longest life), draw the most common body of the
lineage at its peak as an 8x8 grid of colored cells (block colors as the viewer), with one line of caption: world,
seed, lineage id, lifetime, peak agents, mass, hard / muscle / digestive, meat share. Pick 6-8 that differ in shape.
Add one line saying what the shape does in the physics (where it has force, where it cannot be touched, what it
reaches), so that the reader learns to read bodies. `e011`'s `report.py` has `gallery()` for this. A reader
remembers shapes, not percentiles.
