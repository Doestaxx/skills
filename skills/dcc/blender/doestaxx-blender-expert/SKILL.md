---
name: doestaxx-blender-expert
description: "Use when doing any 3D work in Blender through Python or an MCP bridge, headless or in a live session: modeling, sculpting a character or head, retopology, UV unwrapping, baking, texturing, rigging, animating, previs, geometry nodes, lighting and rendering, grease pencil, or finishing an AI-generated mesh into a production asset. Also before exporting or handing off an asset, to check it is ready for a game engine, a render or a 3D print (floating parts, z-fighting, inside-out normals, unapplied scale, missing UVs). Also when a bpy script fails on Blender 5.x API changes, a brush or sculpt operator fails or crashes headless, or a result has to be judged like a professional 3D artist would."
license: MIT
---

# Blender expert (router and agent protocol)

Expert-level Blender work is a loop, not a script: build big to small, and at every stage turn the
model, measure it and fix it before adding detail. This skill is the protocol every Blender task
follows and the map to the domain skills distilled from Blender Studio artists, Blender Conference
talks and top instructors (sources in each skill). If a sibling skill named here is missing from
your available skills, ask the user to install it from the Doestaxx skills repository
(https://github.com/Doestaxx/skills); unattended, proceed from tool schemas and flag the gap.

## 1. Execution channel

- **Session Blender** (Higgsfield use Blender: one background Blender per MCP connection, below),
  for scene work an agent drives call by call. **Live GUI Blender** (a bridge into the user's open
  window), for anything interactive: real sculpt/paint brushes, weight painting, viewport
  screenshots. On either, one short, idempotent script per call returning a compact result dict.
  Get-or-create by name. Never touch objects you did not create. Save a stage backup
  `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` after each stage.
- **Headless helper** `blender -b [file] --factory-startup --python-exit-code 1 -P x.py -- args`,
  for renders, audits, batch ops, anything when no bridge is up. Use `--factory-startup` so the
  user's add-ons and preferences stay out of the run (an add-on can call the network or change
  defaults). Without `--python-exit-code` a failing script still exits 0. Print a final
  machine-readable result line.

Never open your own GUI Blender window to test things on the user's machine: windows steal focus and
pile up. Live work goes through the user's already-running Blender; everything else runs headless,
one Blender process at a time per agent (other sessions may be rendering on the same machine).

**Session channel: Higgsfield use Blender.** The `higgsfield-use-blender` local MCP server
(`fnf-blender-mcp`) runs one dedicated background Blender per MCP connection. Setup and the
generation hand-off are the `doestaxx-blender` skill's work; this section covers the bpy side.

- It never attaches to an open Blender window. To edit the user's work, they save it first, then
  `bl_open_project` loads the file. Unsaved work in their window is unreachable.
- `bl_health` starts the process (factory startup, `background: true`) and reports the version,
  PID and active file. `bl_get_scene_summary` reads the session's scene.
- Before edits, load `bl_get_skill` with `name: "blender-scene"`. Read each tool's input schema from
  the server's tool list before its first call, Python execution included: copy names, never guess
  them.
- There is no viewport screenshot. Look through a camera with `bl_render`.
- Scene datablocks persist between calls; Python local variables do not. Look objects up by name.
- A timeout neither cancels nor repeats a command: poll its `job_id` with `bl_job_status`. Other
  execution tools refuse calls while that job runs.
- Reconnecting, stopping the server or a crash loses unsaved state, and nothing restarts by itself.
  Save deliverables with `bl_save_project`; save and render refuse to overwrite unless
  `overwrite: true`, so use a new path unless the user authorized replacement.
- Errors can leave partial changes: inspect before retrying, never assume a rollback.

**Live GUI channel.** Interactive work in the user's running window (real brushes, weight painting,
viewport screenshots) needs a bridge that attaches to that window, such as another Blender MCP
add-on the user runs. Read its tool list first: names differ per bridge. Budget every call (many
clients stop waiting after 60 s), make one logical change per call so one Undo reverts it, and send
bakes, dense QuadriFlow, turntables, playblasts and final renders to a headless Blender on a saved
copy. A timed-out call has an unknown outcome: read the scene again before retrying. Bridges rarely
save the user's file: the stage backup (`save_as_mainfile(..., copy=True)`) writes a separate copy,
which is also where headless work starts. Ask the user to save their own file at milestones.

Check `bpy.app.version` first; this skill set targets 5.2 LTS, while the Higgsfield use Blender
server accepts Blender 4.2 and later (`bl_health` reports the version), so check the version
timeline in the deltas before using a recent API. Many tutorials the experts recorded use 2.8x to
4.2 UI: read [`references/blender-5.2-deltas.md`](references/blender-5.2-deltas.md) before trusting
any remembered operator, brush name or API.

**Verified capability matrix (Blender 5.2.1):**

| Action                                                                                                                                | Headless                                               | GUI session                                       |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------- |
| Voxel remesh, QuadriFlow, multires subdivide, modifiers, bmesh, UV ops with edit-mode context, Cycles/EEVEE/Workbench renders, baking | yes                                                    | yes                                               |
| `bpy.ops.brush.asset_activate`, dyntopo toggle                                                                                        | yes                                                    | yes                                               |
| Brush strokes (`sculpt.brush_stroke`, `paint.image_paint`, `paint.weight_paint`)                                                      | no (poll fails)                                        | yes, via [`scripts/bx_gui.py`](scripts/bx_gui.py) |
| `paint.mask_flood_fill`, `sculpt.mesh_filter`                                                                                         | CRASHES Blender                                        | yes, via `bx_gui.run()`                           |
| Programmatic sculpting on mesh data                                                                                                   | yes, `doestaxx-blender-sculpting/scripts/bx_sculpt.py` | yes                                               |

## 2. The expert loop (every domain)

1. **Establish the brief** in numbers: purpose (film, game engine, still, animation), budgets (tris,
   texture size, frame range), style (stylized or realistic), references. When the brief is silent,
   choose a documented default from the domain skill and write it down.
2. **Plan the stages** the domain skill defines. Never start with detail.
3. **Build one stage** with the smallest scripts that do it.
4. **Gate the stage:** run the measurable checks ([`scripts/bx_audit.py`](scripts/bx_audit.py) for
   meshes, the domain's own checks) AND render a review sheet
   ([`scripts/bx_review.py`](scripts/bx_review.py): silhouette, matcap, wire from
   front/side/three-quarter/low) and open it with the image reader. Experts orbit constantly; the
   review sheet is the agent's orbit. Every image read stays in the agent's context: for quick looks
   use a camera render at about 768 px wide (`bl_render`, or the live bridge's screenshot), and
   keep review sheets near 1600 px (`res=400` for four views and three modes). Judge with the
   domain's `references/critique.md`.
5. **Fix before advancing.** A problem found at blockout costs one script; found after texturing it
   costs the stage.
6. **Deliver with evidence:** run the delivery gate (`bx_audit.deliverable`, below) on the parts of
   the asset before any export or handoff and fix every error. Then report final renders, gate and
   audit numbers, and what was not verified.

Never report a model, rig, animation or render as done without having looked at a render of it.

## 3. Persona pipelines

| Persona / brief                                       | Skill chain                                                                                                                                                                                                | Deliverable                                                  |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Character artist, stylized or realistic               | doestaxx-blender-sculpting, doestaxx-blender-retopology, doestaxx-blender-uv-baking, doestaxx-blender-texturing-shading, doestaxx-blender-hair                                                             | sculpt, animation-ready low poly, UVs, baked maps, materials |
| AI-mesh finisher (Higgsfield 3D output to production) | gate the generated asset, doestaxx-blender-retopology (or cleanup + remesh), doestaxx-blender-uv-baking (bake FROM the generated high), doestaxx-blender-texturing-shading; generation itself: doestaxx-3d | clean, UV'd, baked asset at a stated budget                  |
| Game asset artist                                     | doestaxx-blender-hard-surface or doestaxx-blender-sculpting, doestaxx-blender-retopology (game budget), doestaxx-blender-uv-baking, doestaxx-blender-texturing-shading, doestaxx-blender-export            | low poly + PBR set, exported glTF/FBX                        |
| Rigger / character TD                                 | doestaxx-blender-rigging                                                                                                                                                                                   | rig with controls, weights, deformation tests                |
| Animator                                              | doestaxx-blender-previs-storyboard (shot planning), doestaxx-blender-animation                                                                                                                             | blocked, splined, polished shot + playblast                  |
| Story / previs artist                                 | doestaxx-blender-previs-storyboard, doestaxx-blender-grease-pencil                                                                                                                                         | shots, cameras, animatic                                     |
| Look-dev and lighting artist                          | doestaxx-blender-texturing-shading, doestaxx-blender-lighting-rendering                                                                                                                                    | lit, color-managed, composited renders                       |
| Technical artist / procedural                         | doestaxx-blender-geometry-nodes                                                                                                                                                                            | node-group assets, procedural systems                        |
| 2D / 2.5D animator                                    | doestaxx-blender-grease-pencil                                                                                                                                                                             | GP animation                                                 |

Related skills outside this set: doestaxx-3d (generate meshes to finish here), doestaxx-blender
(Higgsfield generation and the hosted 3D Jutsu scene from Blender).

## 4. Shared toolkit (`scripts/`, all tested on 5.2.1)

- `bx_audit.py`: `audit(obj, high=None)` returns quads %, n-gons, poles (valence 3 / 5+ / 6+),
  non-manifold, loose, duplicates, flipped faces, self-intersections, boundary loops, symmetry %,
  edge-length CV, and fidelity to a high poly; `verdict(report)` lists problems. CLI:
  `blender -b f.blend --python bx_audit.py -- --object Name [--high Sculpt] [--json out.json]`.
- `bx_audit.deliverable(objs, profile="game")`: the delivery gate. `audit` grades topology; this
  grades what an engine, renderer or slicer receives, across the parts of ONE asset:
  - errors in every profile: a mesh with no faces after modifiers, floating parts and fragments,
    closed parts inside out, negative scale; z-fighting between parts everywhere but `print`;
  - by profile (`game`, `render`, `print`, `roblox`): unapplied scale, faces pointing into a part
    (an error from 0.1% of its surface, a warning below except for `print`), duplicate faces, no UV
    map under an image texture, open borders for `print` and `roblox`, any gap between parts for
    `print`, the Roblox 20,000-triangle mesh limit (checked 2026-10-18).
  - Returns `{pass, errors, warnings, per_object}`. Tolerances scale with the asset's diagonal.
    UV-seam splits from a glTF import are welded for the checks, so seams never read as holes.
  - Gate separate props one by one: every prop but the largest reads as floating.
  - CLI, exit code 2 on failure:
    `blender -b --factory-startup --python-exit-code 1 -P bx_audit.py -- --deliverable [--import model.glb | --objects A B] --profile game [--json out.json]`.
  - Fixes: apply scale (`obj.data.transform(Matrix.Diagonal(obj.scale).to_4x4())`, then
    `obj.scale = (1, 1, 1)`; a scale the message puts on a parent: select the parent and its
    children, `bpy.ops.object.transform_apply(scale=True)`), `bmesh.ops.recalc_face_normals` for
    inside-out parts, `bmesh.ops.reverse_faces` for faces pointing inward
    (`per_object[name]["inward_faces_at"]`), delete or offset the hidden face of a z-fighting pair,
    join or move floating parts, delete fragments.
  - Engines cull back faces: to see what they draw, render
    `bx_review.review(parts, out, culling=True)` (magenta shows through a face pointing inward) and
    compare with a sheet without.
- `bx_review.py`: `review(objs, out_dir, views, modes, culling=False)` takes objects or names and
  writes one contact sheet (rows = modes, cols = views) in a temporary scene, user settings
  untouched; `playblast(out_path, res_pct=50)`; `turntable(obj, out_path, frames=72, res=720)`. Only
  `review` has a command line: call the others from a short wrapper script.
- `bx_gui.py`: real brushes in a live session: `set_view`, `activate_brush(mode, name)`,
  `stroke(mode, world_points, size, strength)`, `run(op, **kw)`, `set_paint_color`, `screenshot`.

Import pattern: `import sys; sys.path.append("<this skill>/scripts"); import bx_audit, bx_review`.
Replace `<this skill>` with the absolute path of the installed skill folder: Blender's Python does
not share the agent's working directory, and over a live bridge the code runs inside the user's
Blender. Check the path in the first call (`result["ok"] = os.path.isdir(path)`) and
`importlib.reload` a module after the skill updates.

## 5. Version traps that break most remembered code

- Brushes are assets (4.3):
  `bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', asset_library_identifier="", relative_asset_identifier="brushes/essentials_brushes-mesh_sculpt.blend/Brush/Clay Strips")`;
  brush size is a diameter (5.0); Flatten/Fill/Scrape merged into the Plane type.
- Auto Smooth removed (4.1): `mesh.shade_smooth()` / Smooth by Angle modifier; voxel remesh output
  is flat-shaded until you call `shade_smooth()`.
- Principled BSDF v2 (4.0): address sockets by name; Emission strength defaults to 0.
- `BLENDER_EEVEE` is the EEVEE Next identifier in 5.x (`BLENDER_EEVEE_NEXT` fails).
- Compositor is a node group (5.0): `scene.compositing_node_group`, not `scene.node_tree`.
- Video output: set `image_settings.media_type = 'VIDEO'` before `file_format = 'FFMPEG'` (5.0).
- Slotted actions (4.4), `action.fcurves` removed (5.0): use
  `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot)`.
- Bone collections replace armature layers (4.0); Grease Pencil v3 is `GREASEPENCIL` with
  `bpy.ops.grease_pencil.*` (4.3).
- Positional context dicts for operators are gone: `with bpy.context.temp_override(...)`.
- `obj.matrix_world` is stale right after setting location/scale until `view_layer.update()`.

## References

- [`references/bpy-reliability.md`](references/bpy-reliability.md): checklist and tested procedures
  for reliable bpy (operators vs data API, stale references, evaluated vs original data, idempotent
  headless jobs, numpy bulk access, node trees, persistence). Load before writing any non-trivial
  script.
- `references/blender-5.2-deltas.md`: full, cited list of what changed from 2.8x to 5.2 per domain
  (load before writing code from memory or following an old tutorial).
