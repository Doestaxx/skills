---
name: doestaxx-walkable-room
description: "Use when one interior photo, uploaded or generated on Higgsfield, should become a room a visitor walks into in a web browser and plays with: props lifted out of the photo and rebuilt as 3D objects to grab, throw, and hear land, inside a Gaussian splat world or a mesh room, or restyled variants of one room. Keywords: image-blaster, walkable room, photo to 3D room, clean plate, object cut-out, splat world, physics props, grab and throw, impact sounds, heightfield collision."
license: MIT
---

# Doestaxx Walkable Room

## Overview

One photo of a room becomes a place to walk into and touch: a 3D room (walls behind the camera
included) with its small objects rebuilt as real 3D models a visitor can pick up, throw, and hear
land. Restyle the photo first and the same room comes in several looks. The route follows the
open-source [image-blaster](https://github.com/neilsonnn/image-blaster) pipeline:

1. **Uncover**: describe the photo literally and list its single movable objects with a box, the
   surface each stands on, a size estimate, and materials. Pick two or three per room.
2. **Plate**: one removal-only image edit that erases those objects and nothing else.
3. **Cut-outs**: one image edit per object on the original photo, drawing it alone on white.
4. **Room**: a world built from the plate. Higgsfield has no single-image world model, so this step
   is a choice the user makes (see Room options).
5. **Objects**: image-to-3D on each cut-out, with PBR textures.
6. **Sounds**: a few short impact one-shots per object.
7. **Assembly**: level and scale the room, fit the lens, derive collision, put each object back where
   the photo had it, and show it all with a renderer and a physics engine.

Steps 1 and 7 are the agent's own work on downloaded files. Steps 2, 3, and 5 run on Higgsfield.
Connection, uploads, pricing, and the wait loop: see the `doestaxx` skill. Object meshes:
`doestaxx-3d`. Splat worlds and their options: `doestaxx-3d-worlds`. ComfyUI graphs:
`doestaxx-workflows`. If a sibling skill named here is missing from your available skills, ask the
user to install it from the Doestaxx skills repository (https://github.com/Doestaxx/skills);
unattended, proceed from tool schemas and flag the gap.

## Room options

Before the first paid step, put these to the user and let them pick:

- **(a) Splat world from an external service**, such as World Labs Marble (at authoring time): the
  original pipeline and the best match. The user runs the plate there and brings back the `.spz` or
  `.ply`. Calibrate per [references/calibration.md](references/calibration.md).
- **(b) ComfyUI**, through `doestaxx-workflows`, only if the user's server has a single-image world
  or splat node installed. Same calibration as (a).
- **(c) Higgsfield only: a mesh room** built in hosted 3D Jutsu. Load `get_preset_instructions` with
  `/3d-jutsu` and follow it: walls, floor, windows, and fixed furniture blocked out at meter scale
  from the plate, the delivery camera matched to the photo. Export with `scene_builder_3d_get_glb`.
  It reads as a modeled set, not a photographic room. Mesh-room calibration and viewing are in the
  same references, under their mesh sections.

Unattended, take (c) and say so in the report.

## Quick reference

Discover every paid stage's model with `models_explore` (`recommend`, then `get` for its
parameters and `medias[].roles`). Never hard-code a generative model id. Price each payload with
`get_cost: true` before running it.

| Step      | Tool                                         | What to send and check                                                    |
| --------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| Uncover   | none, read the photo yourself                | Single movable items, box, support, size, materials                       |
| Plate     | `generate_image`, photo as reference         | `remove the following from the image: ...` and nothing else               |
| Cut-out   | `generate_image_batch`, photo as reference   | One request per object, square, white background                          |
| Room      | per Room options                             | The plate; one fixed seed across restyles when the route has one          |
| Object    | `generate_3d`, one call per cut-out          | Textures and PBR on, about 50,000 faces                                   |
| Sound     | per Sounds below                             | One clip of about 6 s per object, several impacts separated by silence    |
| Calibrate | none, local                                  | [references/calibration.md](references/calibration.md)                    |
| Viewer    | none, local                                  | [references/viewer.md](references/viewer.md)                              |

Object rules and prompts: [references/objects.md](references/objects.md).

## Worked example: the user's living room, walkable, with things to throw

1. **Photo.** Upload the user's photo per the `doestaxx` skill (`media_upload`, PUT,
   `media_confirm`) and reuse the `media_id`. With no photo, generate a photoreal interior: a doorway
   view at about chest height, level and centered, wide lens, a few small objects on tables and the
   sofa. For several looks, edit that photo once per style, opening the prompt with the fixed
   architecture (windows, door, floor plan, camera, lens) before the new finishes, furniture, and
   light.
2. **Destination.** `get_preferences` before the first generation; reuse one `folder_id` for every
   job in the run.
3. **Uncover.** Look at each photo, describe it literally, and write the object list. Choose two or
   three objects per room: separate, unoccluded, one or two materials, standing on the floor, a
   table, or a seat.
4. **Room route.** Ask the Room options question now, so the plate is made once for the chosen
   route.
5. **Plate.** `models_explore` `recommend` with `type: "image"`, `input: "image"`, and "remove objects
   from a room photo, keep everything else". Read the reference role with `get`, price, then
   `generate_image` with the photo in `medias`:

   > remove the following from the image: the {object} on the {support}, {where}; the {object}
   > {where}

   Compare the plate with the photo. Removal edits sometimes recolor an object instead of erasing it,
   or take its neighbors too: re-run with a narrower list, or drop that object. `count: 2` gives two
   tries at one price check.

6. **Cut-outs.** One request per object in one `generate_image_batch`, each with the original photo
   (never the plate) as reference and the isolation prompt from
   [references/objects.md](references/objects.md). The batch takes no `get_cost`: price one request
   with `generate_image` first. Name anything resting on the object so it stays out. If the white
   background bleeds into the object, run `remove_background` on that job id.
7. **Room.** Build it on the chosen route. On (c), keep the plate open beside each 3D Jutsu render
   from the delivery camera and correct the largest visible mismatch before moving on.
8. **Objects.** `models_explore` `recommend` with `type: "3d"` and "textured PBR prop from a product
   cut-out". Read its texture, PBR, and face-count fields with `get` (the names differ per model),
   price, then one `generate_3d` per cut-out, passing the cut-out's `job_id` as `medias[].value`.
   Collect the jobs with `jobs_wait` (`index` per object), then download each GLB from the result
   URL with `curl -L`.
9. **Sounds.** `models_explore` `list` with `type: "audio"` and look for a sound-effect model not
   marked game pipeline only. At authoring time the only sound-effect member was game-pipeline only,
   which the `generate_audio` description forbids for standalone audio. With none available, offer:
   a ComfyUI text-to-audio graph through `doestaxx-workflows`, an external sound-effect service, or
   licensed library recordings the user supplies. The prompt for any generator:

   > Four separate one-shot impacts, each followed by a full second of silence: {the object, its
   > material} {knocked over / dropped} onto {the room's floor}, {the character of the sound}.
   > Close-miked, dry room, no music, no voices.

10. **Assemble.** Calibrate each room and place its objects per
    [references/calibration.md](references/calibration.md), then build the page per
    [references/viewer.md](references/viewer.md). Simplify the GLBs for the web (about 15,000 to
    20,000 triangles, 1K WebP textures, Meshopt) and load physics after the room is on screen.

## Common mistakes

- Treating a splat world as metric: it is not. Measure the camera's height above the fitted floor
  and compare the objects' projected heights with their estimated sizes; at authoring time that put
  the photo camera about 1 m above the floor in every room.
- Assuming every world shares the photo's lens: restyles of one photo came back with fields of view
  from about 50 to 76 degrees from the same world model. Fit the lens per world before projecting
  boxes.
- Picking the room route after making the plate: the mesh-room route needs the plate only as a
  modeling reference, so ask first.
- Cutting out from the plate: the object is no longer there. Cut-outs come from the original photo.
- Uncovering plants, glass, or objects holding other objects: image-to-3D closes foliage into a
  solid shell with leaves painted on. Skip them, or name and remove what they hold.
- Placing objects from the base of the box on the floor plane alone: objects on tables or seats
  float or sink. The surface right behind the bottom of the box is where each one stood.
- Dropping props into physics on page load: noisy supports send them tumbling. Start rigid props
  asleep where the photo had them; let only soft ones (cushions) settle.
- Playing a sound on every contact force: a resting object reports its own weight every step. Sound
  only when the object was moving into the contact.
- Trusting PBR metalness from image-to-3D: lacquer and glaze come back as metal and render as
  chrome. Keep metalness only on real metal.
- Resubmitting a 3D job after a transport timeout or a slow `jobs_wait`: the job may exist. Keep its
  `job_id` and keep polling; a timeout never justifies a second run.
- Using a game-pipeline-only audio model for the room's sounds.
- Running heavy local jobs in parallel (calibration, mesh conversion, splat level-of-detail builds):
  run them one or two at a time.
