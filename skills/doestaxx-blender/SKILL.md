---
name: doestaxx-blender
description: "Use when an agent works in Blender alongside Higgsfield generation: setting up the Higgsfield use Blender local MCP server (fnf-blender-mcp, higgsfield-use-blender, bl_* tools, /use-blender), opening, editing, rendering and saving .blend projects in a background Blender, turning a camera render into a Higgsfield image, mesh or video placed at the 3D cursor, keying camera paths, or building a hosted 3D Jutsu scene (scene_builder_3d tools, /3d-jutsu) with GLB and .blend export."
license: MIT
---

# Doestaxx for Blender

## Overview

Two routes put Higgsfield next to Blender. Prefer the local one.

- **Local: Higgsfield use Blender.** The `higgsfield-use-blender` MCP server (`fnf-blender-mcp`)
  runs a dedicated background Blender on the user's computer, one per MCP connection. It edits,
  renders and saves `.blend` files. Generation goes through the Higgsfield MCP, and the agent
  imports the results with Python.
- **Hosted: 3D Jutsu.** A revision-controlled Blender scene in Higgsfield's cloud, edited through
  the `scene_builder_3d_*` tools. Nothing is installed. It imports only curated catalog models,
  never the user's own files or a fresh generation.

Connection, uploads, pricing and jobs: the `doestaxx` skill. Meshes: `doestaxx-3d`. Modeling,
sculpting, rigging, shading and engine export through bpy: `doestaxx-blender-expert`. If a sibling
skill named here is missing from your available skills, ask the user to install it from the Doestaxx
skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool schemas and
flag the gap.

## Setup: local route

`get_preset_instructions` with `{preset: "/use-blender"}` holds the current procedure, and its
`/use-blender/references/installation` and `/use-blender/references/verification` hold the details.
At authoring time:

- Needs Node.js 24+ with npm and Blender 4.2+ on the user's computer. No add-on and no open window.
- Install needs a shell on that computer: a local agent session, never a cloud sandbox. From a cloud
  session, ask the user to run the setup from a local one.
- Check `npm view fnf-blender-mcp@latest version` is 0.2.0 or newer (0.1.0 needs the old add-on),
  then install into a persistent folder (`$HOME/.higgsfield/blender-mcp`) and run the CLI's `doctor`
  and `config --format json` with `--blender <absolute path>`.
- `config` prints the entry; it registers nothing. Claude Code, with the printed paths:

  ```sh
  claude mcp add --scope user higgsfield-use-blender --env BLENDER_EXECUTABLE=<absolute-blender-path> -- <absolute-node> <absolute-server-arg>
  ```

  Keep `--env` after the server name. Reuse a matching existing entry; never overwrite one.
- Start a fresh conversation, then verify: `bl_health` returns the version, PID and
  `background: true`. A passing `doctor` proves nothing about the conversation's tools.

## Quick reference: local route

| Step              | Tool                                   | Notes                                         |
| ----------------- | -------------------------------------- | --------------------------------------------- |
| Start, check      | `bl_health`                            | First call starts the process                 |
| Load a saved file | `bl_open_project`                      | Guards unsaved session changes                |
| Read the scene    | `bl_get_scene_summary`                 | This session's scene only                     |
| Scene guidance    | `bl_get_skill` `name: "blender-scene"` | Before the first edit                         |
| Run bpy           | the server's Python tool               | Read its name and schema from the tool list   |
| Look              | `bl_render` through a camera           | No viewport screenshot exists                 |
| Long call         | `bl_job_status` with `job_id`          | A timeout neither cancels nor repeats         |
| Save              | `bl_save_project`                      | Refuses to overwrite unless `overwrite: true` |

- It never attaches to an open Blender window. The user saves their work; `bl_open_project` loads
  it.
- Datablocks persist between calls; Python locals do not. Look objects up by name.
- Reconnecting, stopping the server or a crash loses unsaved state. Save deliverables before
  closing, to a new path unless the user allowed replacement.
- Python has the process's filesystem rights and bypasses the typed tools' guards: write only paths
  the task names.

## Worked example: camera view to a prop at the 3D cursor

"Turn what this camera sees into a 3D prop and put it at my 3D cursor."

1. `bl_health`, then `bl_open_project` on the user's saved file. `bl_get_scene_summary` names the
   cameras; read `scene.cursor.location` with Python.
2. Python: set the shot camera active and a 1024 px square resolution, then `bl_render` to a new PNG
   path in the project folder. Look at the image before spending.
3. Upload it (`doestaxx`): `media_upload`, PUT, `media_confirm` with `type: "image"`.
4. Usually the render shows the whole set: isolate the prop first with `generate_image` (an edit
   model, the render as reference: "the {prop} alone, centered, plain white background, full view").
   The mesh copies only what is in the image.
5. `models_explore` `recommend` with `type: "3d"` and "textured prop from one image"; `get` for its
   `medias[].roles` and texture or PBR fields. Price with `get_cost: true` and wait for the user's
   yes. Unattended, report the quote and stop.
6. `generate_3d` with the image's `job_id` (or `media_id`) under the model's image role. `jobs_wait`
   until terminal, then `curl -L` the GLB result URL into the project folder.
7. Python: `bpy.ops.import_scene.gltf(filepath=...)`, move the imported root to the cursor, set its
   real height (glTF is Y up and meters; Blender is Z up), and parent it under one named empty.
8. `bl_render` again through the shot camera and compare with step 2. Then `bl_save_project` to a
   new path and tell the user where it is.

The same hand-off covers other outputs. A texture or material image goes onto a node tree by Python.
A video from a render uses `generate_video` with the render as `start_image`. A panorama for the
World: `doestaxx-skyboxes`.

## Camera paths

No tool keys a camera for you. In Python, key the camera's location and a Track To target, or
parent it to a dolly on a curve (`doestaxx-blender-blockout` has `B.rail_camera`). Set the frame
range to the shot, smooth the keys, and render the first, middle and last frames to check. For an
orbit around a static subject: an empty at the subject, the camera parented to it, the empty's Z
rotation keyed 0 to 360 degrees with linear interpolation.

## Hosted route: 3D Jutsu

Load `get_preset_instructions` with `{preset: "/3d-jutsu"}` before the first call; it owns the
runtime limits and links the scene-building references.

- **Project**: `scene_builder_3d_list_projects`, or `scene_builder_3d_create_project` once. Every
  call takes `projectId`.
- **Loop**: `scene_builder_3d_get_project` or `scene_builder_3d_query_python` for the guards, then
  `scene_builder_3d_run_python` with `revision`, `expectedSceneSequence` and a stable
  `operationId`. One mutation at a time; poll `scene_builder_3d_get_operation` while one is active.
  On a stale-state conflict, query again and send new code under a new id; never replay.
- **Look**: render inside a query, publish with `artifacts.file(name=..., media_type="image/png")`
  and `target.publish()`, fetch with `scene_builder_3d_get_artifact`, and inspect the image.
- **Models**: `scene_builder_3d_search_assets`, then `scene_builder_3d_import_asset` with the
  result's `importArguments`. Catalog only.
- **Deliver**: `scene_builder_3d_show_scene` once with the final revision;
  `scene_builder_3d_get_glb` or `scene_builder_3d_get_blend` when the user wants files. AI images or
  video from a render (`scene_builder_3d_generate_angles`, `scene_builder_3d_generate_video`) spend
  credits.
- Runtime at authoring time: Blender 5.2, headless, about five minutes per operation, no network.

## When Higgsfield cannot do it

Stop and give the user the options:

- A generated mesh inside a hosted scene: 3D Jutsu imports catalog models only. Use the local route,
  or build the shape in bpy inside 3D Jutsu.
- Interactive work in the user's open window (brushes, weight painting, a live viewport capture):
  a Blender MCP add-on that attaches to the window, such as the original Scenario for Blender
  extension.
- A generation step Higgsfield lacks (a 360 panorama, a splat world, a node graph): ComfyUI through
  `doestaxx-workflows`.

## Common mistakes

- Expecting the local server to see unsaved work in the user's window: it starts its own process.
- Installing from a cloud session: the server must live on the computer that runs Blender.
- Overwriting the user's `.blend`: save to a new path unless they authorized replacement.
- Resending a command after a client timeout: poll `bl_job_status` first.
- Passing a file path or URL to a Higgsfield `medias` value: upload first and pass the `media_id`.
- Importing a GLB at the origin unscaled: generated meshes come back at arbitrary size; set real
  height and put the pivot at the base.
- Replaying a 3D Jutsu edit after a conflict, or importing twice to poll: both can duplicate work.
- Calling `scene_builder_3d_show_scene` before the last mutation settled, or more than once for one
  revision.
