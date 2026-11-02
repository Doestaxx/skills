---
name: doestaxx-3d
description: Use when generating or handling 3D meshes for Doestaxx on Higgsfield, fal.ai, or a direct 3D API (Meshy, Tripo), including image-to-3D, text-to-3D, or multi-view reconstruction to GLB, PBR-textured or game-ready props and characters, low-poly or quad topology, triangle budgets, remesh, retexture, auto-rigging a humanoid, applying an animation clip, or saving a model for Unity, Unreal, Godot, or Blender. Keywords: generate_3d, Meshy, Tripo, Hunyuan3D, SAM 3D, animation_actions.
license: MIT
---

# Doestaxx 3D Meshes

## Overview

Generate a concept image first, then run image-to-3D: it gives more art direction than text-to-3D.
Every 3D run goes through `generate_3d`, which returns a GLB (one member can return FBX). Rigging,
remesh, and retexture are separate `generate_3d` runs on a finished mesh's URL. Walkable scenes:
`doestaxx-3d-worlds`. Inside Blender: `doestaxx-blender`. Provider choice and the core loop: the
`doestaxx` skill. Steps below use Higgsfield tool names, the default route; the same procedure holds
on fal.ai or a direct 3D API through their reference files there.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Quick reference

| Step         | Tool                                                  | Notes                                  |
| ------------ | ----------------------------------------------------- | -------------------------------------- |
| Find members | `models_explore` `list` or `recommend`, `type: "3d"`  | Re-discover each session               |
| Contract     | `models_explore` `get`                                | Parameters, ranges, `medias[].roles`   |
| Concept      | `generate_image`                                      | One centered subject, plain background |
| Generate     | `generate_3d` with `get_cost: true`, then for real    | Image ids go in `medias`               |
| Wait, show   | `jobs_wait`, then `job_display`                       | Result URL in the `jobs_wait` row      |
| Rig clip ids | `animation_actions`                                   | Free; shows preview GIFs               |
| Post-process | `generate_3d` with a rigging, remesh, retexture model | Takes `model_url`, never `medias`      |

Members split by job (live at authoring time; confirm with `list`):

- **One image**: Meshy, Tripo, and Hunyuan3D image-to-3D members, plus SAM 3D for lifting one object
  out of a busy photo (its `prompt` names the object).
- **Several views**: Meshy multi-image (1 to 4) and Tripo multiview (2 to 4 ordered views).
  Hunyuan3D takes one image or several.
- **Text only**: Meshy, Tripo, and Hunyuan3D text-to-3D members.
- **Human body**: SAM 3D Body reconstructs a person's shape and pose, not a game asset.
- **Finished mesh**: rigging, remesh, and retexture members take `model_url`.

## Worked example: game-ready treasure chest

1. **Concept.** `generate_image` with a single centered subject on a plain background.
   - A non-biped creature: eye level, side or three-quarter view, every leg visible and clear of the
     body. Top-down hides leg undersides and body height.
   - A biped headed for a rig: see Rigging below.
   - A user reference: upload it per the `doestaxx` skill and use its `media_id` instead.
2. **Pick.** `models_explore` `recommend` with `type: "3d"`, `input: "image"`, and the user's words
   ("game-ready textured treasure chest, about 20k triangles"). Then `get` on two candidates.
3. **Budget.** Target 10k to 50k triangles for this prop. Read the face field and its range off
   `get`; names differ per member (`target_polycount`, `face_limit`, `face_count`).
   - A member whose minimum sits above the target (Hunyuan3D started at 40k at authoring time):
     generate, then remesh down.
   - Quad caps sit lower than triangle caps on some members (Tripo P2 halved its cap with `quad`).
   - Never invent a face field. No field means remesh afterwards.
4. **Texture dials.** Read them before promising a look:
   - Meshy image-to-3D defaulted `should_texture` to false: a bare gray mesh unless set.
     `enable_pbr` needs `should_texture: true`.
   - Tripo members defaulted `pbr` to true, and PBR also enables textures.
   - `delight` (Tripo P2) strips lighting baked into the reference so the mesh relights in the
     engine. Keep it on unless painted shading is the art style.
   - Separate seeds (`seed`, `texture_seed`): hold `seed` and the image, vary `texture_seed` for
     texture variants on one shape.
   - `auto_size` scales to real-world meters, off by default. Set it for a real-scale import.
5. **Price, run, wait.** `generate_3d` with
   `params: {model, medias: [{role, value: <media_id>}], ...fields, get_cost: true}`. Copy the role
   from `get` (`image` on Meshy, `image_references` on Tripo and Hunyuan3D). Then run without
   `get_cost`, and `jobs_wait` on the job. A 3D job takes minutes: keep polling, never resubmit.
6. **Show and save.** `job_display` the job, then `curl -L -o chest.glb "<result url>"`.
7. **Inspect.** Check the file against the budget before delivering (snippet below).

**Text only.** When the user wants no concept to approve, use a text-to-3D member and describe the
object and its required parts in `prompt`. Meshy's text member has `mode: "preview"` (geometry only)
and `"full"` (textured): iterate on shape with preview, comparing `get_cost` quotes.

**Multi-view.** Pass every view of one subject in `medias`. Read the member's description for view
order: Tripo multiview wants ordered views, and a swapped left/right pair can fuse front and back
into one shell. Side labels follow the subject's own left, not the viewer's.

## Inspecting a GLB locally

No viewer needed. This stdlib snippet counts triangles and lists UVs, materials, skins, and clips.
Save it under a name that shadows no module (`glb_info.py`, never `inspect.py`):

```python
import json, struct, sys
d = open(sys.argv[1], "rb").read()
assert d[:4] == b"glTF", "not a GLB"
g = json.loads(d[20:20 + struct.unpack_from("<I", d, 12)[0]])
acc, tris = g.get("accessors", []), 0
for m in g.get("meshes", []):
    for p in m["primitives"]:
        k = p.get("indices", p["attributes"]["POSITION"])
        tris += acc[k]["count"] // 3
uv = any("TEXCOORD_0" in p["attributes"] for m in g.get("meshes", []) for p in m["primitives"])
print({"triangles": tris, "uvs": uv, "materials": len(g.get("materials", [])),
       "skins": len(g.get("skins", [])), "animations": [a.get("name") for a in g.get("animations", [])]})
```

- UVs present proves UVs exist, not a clean layout.
- Faces rendering dark or inside out are flipped normals; later steps inherit them.
- Scale and pivot can shift between steps. Confirm both in a DCC before rigging.

## Remesh, retexture, and the staged chain

Post-process members take `model_url`: the completed GLB's public HTTPS result URL, or the `url`
`media_upload` returned for an uploaded `.glb` (confirmed with `type: "file"`). Never its
`upload_url`, never a `job_id`.

A mesh headed for an engine usually goes further than one run:

1. **Geometry**: untextured where the member allows it (`should_texture: false`, or `texture: false`
   with `pbr: false` on Tripo).
2. **Remesh**: the remesh member sets `topology`, `target_polycount`, `resize_height`, and
   `origin_at` (`bottom` or `center`).
3. **Retexture**: `text_style_prompt` (600 characters at authoring time) or `image_style_url`, which
   wins when both are set. Keep `enable_original_uv: true` to keep the UVs the remesh made.
4. **Rig last**, on the topology that ships.

Each step is its own billed job: price it with `get_cost: true` once its input mesh exists. Inspect
every output before feeding it onward.

## Rigging and animation

- Rigging on Higgsfield is humanoid. The Meshy description warns non-bipeds (animals, objects) may
  rig poorly.
- Rig at generation time with `enable_rigging: true` on a Meshy member, or later with the rigging
  member on `model_url`. Set the height field (`rigging_height_meters` or `height_meters`, default
  1.7).
- Start a rigged biped from a T- or A-pose concept: full body, front view, arms clear of the torso.
  Meshy's `pose_mode` (`a-pose`, `t-pose`) asks for the canonical pose.
- A clip needs `enable_animation: true` plus `animation_action_id`. Find ids with
  `animation_actions` (`query`, `group`, or `category`). When several fit, show the user the
  `preview_url` GIFs and let them pick.
- Quads: glTF stores triangles only, so a GLB is triangulated. Ask for quad topology on a member
  that offers it (Tripo P2 can return FBX) and check face type in a DCC before promising quads.

## When Higgsfield cannot do it

Stop and give the user these options when the need is outside the catalog:

- **fal.ai or a direct model API**: check their live catalogs for a dedicated model before any
  workaround, and route per the `doestaxx` skill.
- **Non-biped rigs** (quadruped, avian, serpentine): rig in Blender through `doestaxx-blender`, or a
  ComfyUI graph through `doestaxx-workflows` if their server has rigging nodes.
- **UV unwrap or part segmentation as its own step**: Blender (`doestaxx-blender`) or a ComfyUI
  graph.
- **FBX, OBJ, or USD export from a GLB**: convert locally in Blender.
- **Another hosted 3D service** the user already pays for, with its own export.

Unattended, take the route the task allows and say which in the report.

## Common mistakes

- Expecting a texture from Meshy image-to-3D with defaults: `should_texture` starts false.
- Passing a URL in `medias` or a `job_id` in `model_url`: the two fields take opposite kinds.
- Sending a scene photo to a single-object member: SAM 3D wants its `prompt` to name the object.
- Promising a triangle count the member's range cannot reach: read the range, then remesh.
- Resubmitting a slow 3D job after a `jobs_wait` timeout: the job is still running.
- Hard-coding member ids in scripts: the catalog rotates. Re-discover with `models_explore`.
