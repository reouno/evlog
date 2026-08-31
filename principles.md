# Principles

Purpose, principles, and decision rules for evlog. Rarely changed. Read this when unsure.

## Purpose

Build a world that keeps evolving on its own, and let people enjoy **watching** it.
The world exists and moves forward whether or not a user is present.

## Principles

1. **Watching is the main activity.** Users do not control the world. The world does not need user input to advance.
2. **Do not script the fun.** Behavior and evolution emerge from simple rules and selection pressure. The author does not decide the outcome.
   - **Laws are about materials and the world, never about traits.** We write what a block is (what it costs, how hard it is, what it can push or digest) and what the world is (where food grows, what a cell holds). We do not write what a creature can do. A bite, armor, an eye, a chase are not rules; they are things a body may turn out to be able to do because of its shape, its materials, and the world. If a rule names a trait (attack, defense, flee, hunt), it is written at the wrong level.
   - **Progress is more freedom, not more rules.** Each step forward should widen what the world and the bodies can be (more shapes, more sizes, more kinds of place) at a bounded compute cost, and then let selection find what is possible. Adding a rule to get a result we want is the failure mode: e008 and e009 hit a wall that was one of our own rules (attack capped at 24 by "the front three rows").
3. **Compute is finite.** The world runs on a device with limited resources. Each step has a bounded cost, and the user controls the load.
4. **It must survive the long run.** Running for days or months must not lead to collapse, stagnation, or explosion. The world keeps changing instead of settling.
5. **No individual belongs to anyone.** Selection happens. There is no user avatar. Attachment is to lineages and the world, not to individuals.
6. **What happened stays.** Events in the world are recorded and can be observed later. The log is part of the world (evlog = evolution log).

## Decision rules

When unsure, ask in this order:

1. Is it interesting to watch?
2. Does it keep running in the long run?
3. Does it add compute cost?
4. Is it a rule about a trait, or about a material or the world? Only the second kind is allowed.

## Where new laws come from

The world will keep needing new laws: a new material, a new kind of place, a new kind of food.
When we look for one, we think in metaphors of the real world.

- **Ask the real world why.** If the world lacks something (large bodies, hunters, eyes), ask why
  the real world has it. Why did elephants, giraffes, whales, and dinosaurs appear and thrive?
  From the answer, extract the simplest premise (food so concentrated that a small mouth cannot
  keep up with it; a cost that falls with size; leaves out of reach of a short body) and write
  it as a law about the world or a material, never about a trait (principle 2).
- **Name the stage the world is at.** e010's five-cell grazers are a world of microbes, or a world
  of mice; the picture tells us what the real world had at that stage that ours does not, and
  which premise is missing.
- **Pressures, not parts.** When one body wins every run, the space of bodies is not too small;
  the world has one optimum. More kinds of parts or a wider genome make that optimum slower to
  reach, not less alone. Add a pressure (a place, a season, matter that cycles) and count how many
  different bodies prosper at once; that count is how a law is judged.
- **The metaphor is a source, not a target.** evlog is a virtual world. It does not have to follow
  the real one, and it should not only imitate it: what can exist here and nowhere else is part of
  what makes it worth watching. Take the premise, not the outcome, and let selection decide.

## Non-goals

- Game elements such as winning, clearing, or scores
- User intervention in the world
- Visual richness over substance
