---
name: doestaxx-blender-blockout
description: "Use when a text brief or a reference image must become a Blender blockout whose playblast guides a render-to-real video pass (a Higgsfield video model that takes a reference clip, such as an omni-reference or motion-transfer model): graybox or previs built for a video model, color-coded proxies at metric scale from rough to detailed, density levels from a simple shot to an expert scene with crowds, traffic and many cuts, character stand-ins chosen per video model (colored capsules, capsules with signature features, rigged gray mannequins), a camera locked to the timeline, rail or tracking camera rigs, lens per shot, framing and occlusion checks, a playblast, a hand-off sheet for the video prompt. Also when a render-to-real pass renders the proxies as boxes, reads one figure as two people, gives runners a stiff, lockstep or sliding gait, swaps a car's front and rear, drifts at the end, or the guide camera pops on a cut."
license: MIT
---

# Blender blockout for a render-to-real video pass

The blockout is the guide clip: the video model copies the camera path, framing, lens feel, easing,
cut points, shot lengths, the position and scale of every mass, figure facing and every trajectory,
and it invents the rest from text and images (materials, light, weather, what each proxy really is,
faces, wardrobe, extras, sound). So the blockout has full authority over motion and layout and none
over look. Ambiguity ruins the pass; crudeness does not: a bent lamppost comes back as a snake,
loose limb blocks as extra people, an unmarked car driving backward. Fix identity in geometry first,
in prompt text second, and judge the result on a synced side-by-side of playblast and video, never
in the viewport alone. If a sibling skill named here is missing from your available skills, ask the
user to install it from the Doestaxx skills repository (https://github.com/Doestaxx/skills);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** doestaxx-blender-expert (execution channel, review loop, 5.2 API changes).
Video generation: the `doestaxx` skill (Higgsfield connection, uploads, pricing, jobs) and
`doestaxx-blender` (the Higgsfield use Blender session this skill builds in).

Toolkit: [`scripts/bx_blockout.py`](scripts/bx_blockout.py):
`import sys; sys.path.insert(0, "<this skill>/scripts"); [sys.modules.pop(m, None) for m in ("bx_blockout", "bx_kits")]; import bx_blockout as B`,
where `<this skill>` is the installed folder's absolute path. The pop drops a copy an earlier run
left in Blender's one Python. Builders are get-or-create by name, so a call can run again, and they
refuse a name the user's own work already holds (names are global to the file). An empty audit
result is a pass. The module docstring shows the call order.
[`scripts/bx_kits.py`](scripts/bx_kits.py) (`import bx_kits as K`, same rules) adds buildings,
stalls, trees, lamps, rocks and vehicles at three fidelity tiers, figures in four cast styles,
crowds, traffic, color schemes and `K.audit_budget`. Four worked scenes, simple to expert, with
render-pass results: [examples](references/examples.md) ([harness](scripts/examples/ex_common.py),
[1](scripts/examples/ex1_watchmaker.py), [2](scripts/examples/ex2_saltflat.py),
[3](scripts/examples/ex3_bridge.py), [4](scripts/examples/ex4_sky_islands.py)).

**Which skill.** This one: guides for a video model. Story previs and animatics judged by a director
and an editor: doestaxx-blender-previs-storyboard; an approved animatic that must guide a video
model is rebuilt here.

## 1. Restate the brief as a build plan

Before any call, write down:

- **Elements and their primitive**: "bus = long box with a marked front", "figures = colored
  capsules". Never model past what the brief names.
- **Dimensions** in meters for everything; when the brief is silent, take them from
  [the contract tables](references/contract.md) and say so.
- **Format**: integer fps, aspect, seconds. The range is 1 to fps x seconds (8 s at 24 fps: 1..192).
- **Shots**: count, move, lens, framing invariants ("hero always in frame, full figure"), cut style;
  beats pinned to seconds, converted to frames now.
- **Levels**: density (simple, medium, advanced, expert: footprint, elements, heroes, extras,
  shots), fidelity (rough, shaped, detailed) and color scheme, read off the brief and set apart:
  [levels](references/levels.md). Where the brief is silent (naming only heroes and shots is
  silent): advanced, shaped, category colors, and say so; drop to simple or medium only for one
  actor in one place. Expert means many elements, movers and cuts, never finer blocks.
- **Video model**, now: cast style and prompt grammar depend on it (`models_explore` `recommend`
  with `type: "video"` and the brief's words, then `get` for its `video_references` role and caps).
- **Cast style** per character ([cast](references/cast.md)): a stand-in with limbs hands the model a
  gait to copy; one without limbs lets it invent body and motion. Default heroes to colored
  capsules, featured (two or three signature features: goggles, a hood, a held lantern) when
  characters must stay apart or carry the story's object; a rigged gray mannequin only when the
  blockout must own limb motion. Tell the user the style chosen, its cost in control, and that the
  others can be A/B tested on a short window.
- **Identity colors**: a hero takes the brief's color ("yellow raincoat": yellow) as the nearest
  `B.PALETTE` color, else the next free one: red, blue, green, yellow, purple, cyan. Two heroes in
  one color, or black, white, gray, brown: [contract](references/contract.md).
- **Deliberate gaps** the video model fills, and **acceptance tests** the brief states: they become
  mandatory audits.

Decide what the brief leaves open and record the decision; do not stop to ask. Spending is the
exception: the user approves every Higgsfield price (section 6). With a reference image: list its
masses, block them at plausible scale, match camera height and lens, `bl_render` from the camera,
compare, adjust until the composition matches, and only then animate.

## 2. Output contract

Four deliverables: the scene, a locked camera timeline, the playblast, the hand-off sheet.

- **Scene hygiene.** Role prefixes (`ENV_`, `FIG_`, `PRP_`, `CAM_`, `CRV_`, `RIG_`, `NULL_target_`,
  full table in the contract), one root collection with role sub-collections. Park the default Cube,
  Light and Camera with `B.park`, never delete. If the file holds other work, build in a new scene
  (`B.make_scene`) and touch nothing existing; every object must trace to one of your stages.
- **Scale.** Meters, Z up, ground at z = 0, figure roots at the feet. The model keeps every mass
  where it is at its size, mistakes included. Nothing familiar for scale: add a `REF_` figure.
- **Color separates masses and names identities.** One saturated color per hero (`B.PALETTE`), the
  set in one `K.scheme` (category hues by default, identity grays, or material colors), extras in
  mid grays, one light, a dark world. `B.paint` and the kits set object color and materials; a kit
  carries several colors, so Solid view needs color type Material (`B.solid_view()`'s default and
  the playblast's). An all-gray playblast has lost identity. Recolor a kit through its arguments:
  its materials are shared per color. Grid or checker texture only where the camera travels and
  depth must read, declared "replace, never inherit" in the sheet.
- **Timeline.** `B.lock_format` before any geometry: integer fps, frames 1 to fps x seconds,
  1920x1080 (2520x1080 for 21:9) at 100 %. One camera per shot, bound to a `CUT_` marker on its
  first frame (`B.bind_cuts`), hard cuts, zero transition frames.
- **Camera rigs.** Rail: `B.rail_camera` (curve, dolly on Follow Path, aim with Track To, camera).
  Handheld tracking, straight push-in and multi-shot masters: recipes in the contract. Reframe by
  moving the aim target, never by rotating the camera.
- **Lens.** One lens per shot from shot size (`B.lens_for_coverage`; 28 mm orbits, 42 to 45 mm
  over-the-shoulder, 24 to 30 mm interiors, 85 mm macro), `clip_start` 0.05. A cut changes lens only
  by changing camera: never key a lens step on a cut frame. A lens may ease inside a shot (a
  deliberate zoom), never jump.
- **Easing.** Bezier keys with auto-clamped handles (`B.smooth_keys`); speed is key spacing on the
  rail (`B.key_rail`), a pause is two near-equal values. LINEAR only for per-frame baked travel
  (vehicles, wheels). Keys run past every cut so nothing stops on the boundary.
- **Handheld** is NOISE F-curve modifiers, never keyed jitter. Measure the result with
  `B.audit_handheld` against the budget in the contract; `animation_data_clear()` removes the
  modifiers, so re-add them after rekeying.

## 3. Channel: the session or headless

The session channel is the Higgsfield use Blender MCP server, `higgsfield-use-blender`: one
background Blender per MCP connection, set up per `doestaxx-blender`. Tool table, call limits and
recovery after a timeout: [session](references/session.md). The two that bite first: it never sees
the user's open window (they save, then `bl_open_project` loads the file), and unsaved state dies
with the connection, so run `B.stage_backup(label)` after each stage and save deliverables with
`bl_save_project`.

**Camera paths** are always `B.rail_camera` and `B.key_rail`: no tool keys a shot camera for you.

**Headless**, with no MCP session: run each stage through doestaxx-blender-expert's headless
helper. Load the preceding `.blend`, check it with `B.guard`, extend it, then save a new
`B.stage_backup(label)` for the next stage. The [examples harness](scripts/examples/ex_common.py) is
only for one-shot builds from factory startup: `start()` deletes all objects, including prior
stages. Never reuse it to resume a backup.

## 4. Build order

A reset is recovered from the last backup ([contract](references/contract.md)). Every call or stage
script starts with `B.guard(expected_file=..., scene=...)`: queued calls land in whatever file is
open.

0. **Probe**, read-only: `bl_get_scene_summary` (headless: `bpy.data`). Other work
   present: new scene.
1. **Format and scaffolding**: `B.make_scene`, `B.lock_format`, `B.collection` tree, `B.park`, dark
   world.
2. **Set**: kits at the chosen fidelity (`K.building`, `K.stall`, `K.tree`) or thick boxes (`B.box`)
   at true scale, repeats as linked duplicates (`K.instance`).
3. **Figures**: `K.figure(..., style=, features=)` per hero in the chosen cast style, root at the
   feet, facing along travel ([cast](references/cast.md)). Travel with `K.walk_path` from a table of
   (frame, position), stride 0.42 x height for a walk, about 0.7 for a run; gestures with `K.pose`;
   extras with `K.crowd(style=...)`.
4. **Props and vehicles**: literal primitives at true position. Mark a vehicle's front in geometry
   (light blocks and grille in front, dark red at the rear); wheels at z = radius, separate with one
   spin channel only when a close shot reads rotation (kit wheels are body mesh). No loose blocks
   near a figure.
5. **Light**: one area light; named key, fill, rim only when the brief designs light.
6. **Cameras**: rigs and lenses per shot, `B.bind_cuts`.
7. **Motion polish**: `B.key_rail` and `B.smooth_keys`, keys past cuts, handheld, vehicle travel as
   one monotone curve keyed per frame.
8. **Audit** (section 5) until clean. When set dressing hides the hero, move the blockers and keep
   the camera plan.
9. **Finalize**: frame 1, shot 1's camera, `B.audit_frames`, `B.state_audit`, final backup, then
   playblast and hand-off sheet.

## 5. Audits: numbers judge, then look

| Check                                | Helper                                                                        |
| ------------------------------------ | ----------------------------------------------------------------------------- |
| Frame math and resolution            | `B.audit_frames(seconds, fps)`                                                |
| Markers bound, switches, lens, jumps | `B.audit_cuts()` (`same_lens_across_cuts=True` when the brief wants one lens) |
| Subjects in frame per shot           | `B.audit_framing({"CAM_s1": ["FIG_red"]}, whole=True)` for full figures       |
| Head never hidden                    | `B.audit_occlusion("FIG_red")`                                                |
| Too close, outside the legal volume  | `B.audit_distance(subject, volume=...)` (full-figure shots only)              |
| Interpenetration                     | `B.audit_intersections(names)`                                                |
| Feet and wheels on the ground        | `B.audit_ground(names)`                                                       |
| Handheld amplitude                   | `B.audit_handheld("CAM_s1")`                                                  |
| Census before hand-off               | `B.state_audit()`                                                             |

Audit each shot's own subject (the wheel for a macro, the hand for an insert). Then look:
`bl_render` through the shot camera at the first, middle and last frame of every shot (set each
frame with the session's Python tool first), and check what numbers miss: a vehicle's front,
connected figures, rigid props without organic curves, nothing stray at frame edges, an ending as
locked as the opening. Thresholds and readings: [audits](references/audits.md). An audit samples
every `step` frames; on a long shot raise `step` to stay under the call limit.

## 6. Playblast, hand-off sheet, video pass

**Playblast.** Headless, on the latest `B.stage_backup` copy, with doestaxx-blender-expert's
`bx_review.playblast(out_path, res_pct=100)`: an H.264 MP4 of the scene camera over the frame range
in Workbench, cuts following the bound markers. Use the session's binary (`bpy.app.binary_path`): an
older `blender` on PATH refuses the file. With no shell, the same call through the session's Python
tool blocks that Blender while it renders: keep it to short clips, and after a timeout poll
`bl_job_status` and look for the file before running it again. Add camera stills at each shot's
start, middle and end.

**Hand-off sheet**, built from the scene ([template](references/handoff.md)):

- color legend tied to reference images and garments;
- `K.cast()` rows, the cut list from `B.cut_list()` with exact times;
- which entities are blocked and which exist only in words;
- every artifact with its timecode, each motion state in words ("creeps", "stands still");
- tie-break clauses ("if text and video disagree about motion, the video wins").

**Video pass**, always through Higgsfield, after the user approves the exact credit cost.
Unattended, stop at the quote (`get_cost: true`) and report it. Steps in
[handoff](references/handoff.md), "The video pass":

- Upload the MP4 and the style board (`media_upload`, PUT, `media_confirm` with `type: "video"` and
  `"image"`).
- `generate_video` with the playblast under the model's `video_references` role and the board under
  `image_references`, `duration` set to the clip's length inside the model's range, priced first.
- `jobs_wait`, then sweep the result against the playblast.

When no Higgsfield video model takes a reference clip, or the clip is longer than every model's
cap, stop and give the user the options in [handoff](references/handoff.md).

Write the prompt motion-first: the clip is rehearsal footage, the cast is described by role and
motion, never by the proxies' shapes, and style comes from a four-panel style board rather than one
restyled frame. A capsule cast adds a stand-in clause (the capsules only mark position, height, pace
and heading) and a gait clause ([cast](references/cast.md)). The prompt names each reference's job
in words: the clip governs camera, motion and layout, the board governs style only. Grammar, clauses
and tested limits: [handoff](references/handoff.md).

## Worked example

Brief: "10 s, 24 fps: a red runner sprints between crate rows toward camera in a warehouse; a blue
guard steps out at second 6; handheld 35 mm backing away."

1. `bl_health`, then `bl_open_project` on the user's saved file and `bl_get_scene_summary`: the
   file holds other work, so build beside it.
2. The session's Python tool: `B.make_scene("BLK_warehouse")`; next call
   `B.guard(scene="BLK_warehouse")`, `B.lock_format(24, 10)` (1..240), collections, backup.
3. Floor 34 x 20 m, 7 m walls, two rows of 1.2 m crates with `B.box`; backup.
4. `K.figure("red", 1.8, (0, 15, 0), style="featured", features=("hood",))`, then `K.walk_path` to
   (0, 1) by frame 200 with a sprint's stride (1.3 m); the blue guard, a capsule, steps into the
   aisle over frames 144 to 156; backup.
5. `B.rail_camera("s1", [(0, 3, 1.5), (0, -1, 1.5), (0, -4, 1.5)], follow="FIG_red", target_offset=(0, 0, 1.2), lens=35)`,
   `B.key_rail("RIG_dolly_s1", [(1, 0), (260, 1)])`, `B.bind_cuts([(1, "CAM_s1")])`, handheld noise
   within budget.
6. `B.audit_frames(10, 24)`, `B.audit_cuts()`,
   `B.audit_framing({"CAM_s1": ["FIG_red", "FIG_blue"]}, whole=True)`,
   `B.audit_occlusion("FIG_red")`, `B.audit_handheld("CAM_s1")`; move crates until clean.
7. Frames 1, 120 and 240, each set in Python and rendered with `bl_render`, and look. Backup,
   `bl_save_project` to a new path, headless playblast, `B.cut_list()` into the sheet.

## Common mistakes and downstream misreads

- **Identity not in geometry**: a floating head or slab arms; loose blocks near a figure read as
  extra people; a car with no marked front driven in reverse; an occupant behind an opaque cabin
  vanishes (give the cabin alpha).
- **Camera grammar**: a key on the cut frame freezes motion there; an overhead orbit read as a cut;
  seats mirrored on a reverse camera; invented reverse shots in dialogue; drift in the last seconds.
- **Ambiguous motion**: slow proxy motion reads as either rolling or still; the sheet decides.
- **Copied limbs**: on a reference-video model, stepped or looped legs come back stiff, in lockstep
  or sliding; switch that character to a capsule ([cast](references/cast.md)).
- **Fragile detail**: sub-pixel parts change identity between restyles; a style that implies text
  invents gibberish lettering.
- **Opening-frame fiction**: "starts at the door" needs a doorway behind frame 1; high shots over
  flat ground read flat.
- **State drift**: render probes that leave resolution or file path changed; pre-existing objects
  adopted as your own; Blender 5 slotted actions hiding F-curves (use `B.fcurves`).
