---
name: doestaxx-3d-worlds
description: "Use when a task asks for a navigable 3D world, explorable environment, walkable level, graybox, or Gaussian splat scene through the Higgsfield MCP: text-to-world, image-to-world, a concept painting or location photo rebuilt as a 3D set, new camera angles of one place, or a 360 panorama turned into a space. Keywords: 3D Jutsu, scene_builder_3d, world generation, splat, 3DGS, spz, World Labs Marble, VR."
license: MIT
---

# Doestaxx 3D Worlds

## Overview

Higgsfield has no Gaussian splat or world-generation model at authoring time. The closest path is a
hosted 3D Jutsu scene: a revision-controlled Blender scene built by running Python through the
`scene_builder_3d_*` tools, matched to a concept image, then exported as GLB or `.blend`, rendered,
or re-imagined as new AI angles.

Be plain with the user before building:

- The result is a modeled polygon scene, not a splat. It is editable, collidable, and engine-ready,
  but it does not carry a photo's appearance the way a splat does.
- Photoreal new views come from `scene_builder_3d_generate_angles` on top of a render, not from the
  geometry itself.
- Scenes import curated catalog GLBs only. A mesh made with `generate_3d` cannot enter a 3D Jutsu
  scene in this version; place it in local Blender instead (`doestaxx-blender`).

When the user needs a real splat, give them the options in "When Higgsfield cannot do it" before
spending anything. Single meshes: `doestaxx-3d`. Panoramas: `doestaxx-skyboxes`. A photo of a room
to walk and play in: `doestaxx-walkable-room`. Connection and the core loop: the `doestaxx` skill.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Quick reference

Load `get_preset_instructions` with `{ preset: "/3d-jutsu" }` once before any scene tool. It owns
the runtime rules; this skill only routes.

| You have                     | Route                                                                    |
| ---------------------------- | ------------------------------------------------------------------------ |
| A text idea                  | 3D Jutsu scene from a written plan, then renders                         |
| One concept image or photo   | 3D Jutsu with the `/3d-jutsu/references/location-new-angles` reference   |
| New views of one place       | Same reference, then `scene_builder_3d_generate_angles` per approved shot |
| A 360 panorama               | Reference only: build the scene, or offer a splat service                |
| Many photos or a walkthrough | No Higgsfield route: offer the splat options                             |
| One object                   | `doestaxx-3d`, not a world                                               |

| Step           | Tool                                                                 |
| -------------- | -------------------------------------------------------------------- |
| Project        | `scene_builder_3d_list_projects` or `scene_builder_3d_create_project` |
| Guards         | `scene_builder_3d_get_project`, then `scene_builder_3d_query_python` |
| Edit           | `scene_builder_3d_run_python` with `revision`, `expectedSceneSequence` |
| Props          | `scene_builder_3d_search_assets`, then `scene_builder_3d_import_asset` |
| Look           | Render in a query, publish via `artifacts`, `scene_builder_3d_get_artifact` |
| Show           | `scene_builder_3d_show_scene` once per review, exact `revisionAfter` |
| Files          | `scene_builder_3d_get_glb`, `scene_builder_3d_get_blend`             |
| AI angle       | `scene_builder_3d_generate_angles`, then `scene_builder_3d_get_generation` |

## Worked example: graybox a level from a concept image

1. **Load the recipes.** `get_preset_instructions` for `/3d-jutsu`, then
   `/3d-jutsu/references/location-new-angles` and `/3d-jutsu/references/scene-building`.
2. **Read the image.** Look at the concept's pixels and dimensions. Write down what is observed
   (silhouettes, counts, openings, light direction) separately from what is inferred (depth, hidden
   walls). Ask only about hidden areas that matter, such as what lies behind the camera.
3. **Project.** `scene_builder_3d_create_project` once with a descriptive name. If the response is
   uncertain, `scene_builder_3d_list_projects` before retrying: a second create duplicates it.
4. **Guards.** `scene_builder_3d_get_project`, then a `scene_builder_3d_query_python` that reports
   object names. Its `revisionBefore` and `sceneSequenceAfter` are the next edit's guards.
5. **Blockout.** `scene_builder_3d_run_python` with a stable `operationId` (`blockout-01`):
   - a source-control camera matched to the concept's perspective (`CAM_source`);
   - floor, walls, and major masses in meters, named by role (`ENV_floor`, `HERO_dome`);
   - one key light and a soft fill. Use Sun, Spot, or Point lights: GLB export drops Area lights.
6. **Match the source.** In a query, render a small preview from `CAM_source` and a top view,
   publish both through `artifacts`, fetch them with `scene_builder_3d_get_artifact`, and compare
   with the concept. Fix the largest mismatch, re-render, repeat. A succeeded edit proves the code
   ran, not that the scene is right.
7. **Dress.** `scene_builder_3d_search_assets` for catalog props, then
   `scene_builder_3d_import_asset` with the result's `importArguments` copied verbatim. One
   mutation at a time, imports included.
8. **Show.** `scene_builder_3d_show_scene` once with the final `revisionAfter`.
9. **Deliver.** `scene_builder_3d_get_glb` for the engine and `scene_builder_3d_get_blend` for the
   editable source, only when the user wants files. Procedural shaders and world lighting do not
   reliably carry into GLB.
10. **New angles (paid, optional).** For each shot the user approves, render it, then
    `scene_builder_3d_generate_angles` with that render's `operationId` and `artifactId`, the
    uploaded concept as `referenceMediaId`, and a fresh `requestId`. Poll
    `scene_builder_3d_get_generation`. On an uncertain response, repeat the same `requestId` and
    arguments, never a new one.

Before step 10, state the shot count and the cost, and wait for approval. A request for "new
angles" is not approval of a paid batch.

## Errors

- **Stale-state conflict**: re-query, see what changed, regenerate the edit with fresh guards and a
  new `operationId`. Never replay the old code.
- **`EXECUTION_TIMEOUT`**: nothing committed. Split the work or shrink the render.
- **`CONTAINER_UNAVAILABLE` or another retryable error**: resubmit the same code under a new
  `operationId` against the same guards.
- **Import failed**: report it. Never fall back to Python downloads or base64 model bytes.

## When Higgsfield cannot do it

Give the user these options for a real splat or a photo-faithful world, and let them choose:

- **World Labs Marble** (at authoring time): text, one image, a 360 panorama, several photos, or a
  video to a navigable splat, with mesh export. A panorama from `doestaxx-skyboxes` can feed it.
- **ComfyUI** through `doestaxx-workflows`: 3D or splat nodes, if the user's server has them
  installed.
- **Local Gaussian splatting** from overlapping photos or a walkthrough video, with an open-source
  trainer on a GPU machine. Best when the camera moved through a static scene with parallax.
- **The 3D Jutsu path above**, accepting a modeled scene in place of a splat.

Unattended, take the route the task allows and say which in the report.

## Common mistakes

- Calling a 3D Jutsu scene a splat, or promising photo-identical appearance from geometry alone.
- Importing a `generate_3d` mesh into a 3D Jutsu scene: the import takes catalog assets only.
- Guessing a revision or scene sequence: read them from the last query or edit.
- Running two mutations at once on one project: the second conflicts.
- Using Area lights, then exporting GLB: the lights vanish.
- Repeating `scene_builder_3d_create_project` after a lost response: list projects first.
- Spending on AI angles before the source-camera render matches the concept.
