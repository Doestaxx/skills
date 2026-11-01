---
name: doestaxx-skyboxes
description: Use when a task needs a skybox, 360 panorama, equirectangular image, environment map, HDRI-style backdrop, or VR backdrop made through the Higgsfield MCP. Triggers include text-to-skybox, turning a photo into a 360 environment, fixing a panorama's wrap seam or poles, upscaling a panorama, restyling its mood, or exporting equirectangular or cubemap layouts for Unity, Unreal, or Godot.
license: MIT
---

# Doestaxx Skyboxes and 360 Panoramas

## Overview

Higgsfield has no dedicated skybox model at authoring time. A skybox here is built in steps: a 2:1
image from a general image model, a local seam repair, pole cleanup, an upscale, then a local
cubemap export. Seam and pole quality are not guaranteed the way a purpose-built skybox model
guarantees them, so every result gets the free seam check before delivery. Say this to the user
before the first paid run.

Check `models_explore` `search` for "360 panorama skybox" first: if a dedicated member has appeared,
use it instead. Connection and the core loop: the `doestaxx` skill. A panorama on the way to a
walkable scene: `doestaxx-3d-worlds`.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Quick reference

| Step          | Tool                                                    | Notes                                         |
| ------------- | ------------------------------------------------------- | --------------------------------------------- |
| Find a 2:1    | `models_explore` `list`, `type: "image"`                | Keep members whose `aspect_ratios` has `2:1`  |
| Generate      | `generate_image`, `aspect_ratio: "2:1"`                 | `get_cost: true` first                        |
| Widen to 2:1  | `generate_image` with an outpaint member                | Per-side pixel expansion; exact width         |
| Seam repair   | Local roll, then `generate_image` masked inpaint        | Members with a `mask` role                    |
| Upscale       | `upscale_image` or an exact-size upscaler member        | Re-check the seam afterwards                  |
| Cubemap       | `ffmpeg -vf v360=e:c3x2` or `v360=e:c6x1`               | Local, free                                   |
| Seam check    | Local column comparison                                 | Free; run on every delivered file             |

## Worked example: stylized forest skybox

1. **Pick a 2:1 member.** `models_explore` `list` with `type: "image"`. Keep members whose
   `aspect_ratios` include `"2:1"` (FLUX 3 Image, Grok Image, and Ideogram 4.5 did at authoring
   time). `get` the pick for its resolution field.
2. **Generate.** `generate_image` with `aspect_ratio: "2:1"`, the highest resolution tier, and a
   prompt that names the projection:

   > equirectangular 360 degree panorama, full spherical environment, horizon exactly at vertical
   > center, ancient pine forest at dawn, mist between trunks, god rays, no people, no text, no
   > frame

   Price with `get_cost: true`, then run with `count: 2`. `jobs_wait`, `job_display`, and save both
   with `curl -L`.
3. **Check the seam** (free, snippet below). A seamless panorama scores a ratio near zero (under
   0.01 on a seamless test image at authoring time); an unrepaired one scores near or above 1. Most
   generic outputs fail.
4. **Repair the seam.** Roll the image half a turn so the seam sits in the middle, inpaint a narrow
   vertical strip there, then roll back:
   - Run the roll snippet below to write `rolled.png` and `mask.png` (white strip, 6% of the width,
     centered).
   - Upload both per the `doestaxx` skill.
   - `models_explore` `get` on a member whose `medias[].roles` include `mask` (Nano Banana 2 and
     Ideogram 4.5 at authoring time). Set its inpaint flag where one exists (`is_inpaint: true`).
   - `generate_image` with the rolled image under its reference role, the mask under `mask`, and the
     prompt "continue the forest seamlessly across the masked strip, same light, same horizon".
   - Download, roll back by the same half width, and re-check the seam.
5. **Clean the poles.** Generic models smear the top and bottom rows, which pinch to a point in the
   engine. Feather the top and bottom 3% of rows toward each row's mean color (snippet below). A
   ground plane or fog in the engine hides the bottom pole on most game skies.
6. **Upscale.** Two routes, priced with `get_cost: true`:
   - `upscale_image` (`2k` or `4k`; pass the source `width` and `height`).
   - An upscaler member that takes exact `output_width` and `output_height` (Topaz at authoring
     time), which keeps exactly 2:1. Prefer the non-generative member over the generative one:
     invented detail breaks the wrap.

   Re-run the seam check on the upscaled file. Repeat step 4 if it fails.
7. **Export.** Equirectangular PNG for engines that take it. Cubemaps locally:
   - `ffmpeg -i sky.png -vf v360=e:c3x2 cube_3x2.png` (a 2048x1024 input gave 1536x1024).
   - `ffmpeg -i sky.png -vf v360=e:c6x1 cube_strip.png` (3072x512 from the same input).

## Local snippets

Seam check, roll, and mask (Pillow and NumPy):

```python
import sys, numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
seam = abs(a[:, 0] - a[:, -1]).mean()
quarter = abs(a[:, 0] - a[:, a.shape[1] // 4]).mean()
print("seam", round(seam, 2), "quarter", round(quarter, 2), "ratio", round(seam / quarter, 3))
w = a.shape[1]
Image.fromarray(np.roll(a, w // 2, axis=1).astype("uint8")).save("rolled.png")
m = np.zeros(a.shape[:2], "uint8"); s = int(w * 0.03); m[:, w // 2 - s:w // 2 + s] = 255
Image.fromarray(m).save("mask.png")
```

Roll back with `np.roll(b, -(w // 2), axis=1)`, where `w` is the repaired image's width.

Pole feather:

```python
import numpy as np
from PIL import Image
a = np.asarray(Image.open("sky.png").convert("RGB")).astype(float); h = a.shape[0]; n = int(h * 0.03)
for i in range(n):
    t = 1 - i / n
    for r in (i, h - 1 - i):
        a[r] = a[r] * (1 - t) + a[r].mean(axis=0) * t
Image.fromarray(a.astype("uint8")).save("sky_poles.png")
```

## From a photo of a place

No member turns one photo into a 360 sphere. The closest path:

1. Outpaint the photo to 2:1 with an outpaint member's per-side pixel fields (`expand_left`,
   `expand_right`, `expand_top`, `expand_bottom` on FLUX.2 Pro Outpaint at authoring time). Compute
   the expansion so the width is exactly twice the height.
2. Repair the seam and poles as above.

The result is a wide extension of one view, not a captured sphere: the back of the scene is
invented. Tell the user so.

## When Higgsfield cannot do it

When the user needs guaranteed seams and poles, or a true sphere from a photo, give them these
options and let them choose:

- **A rendered panorama, seamless by construction**: model the environment in a hosted 3D Jutsu
  scene or local Blender (`doestaxx-blender`) and render an equirectangular panoramic camera.
  Query the camera's panorama properties first; they move between Blender versions.
- **ComfyUI** through `doestaxx-workflows`: a 360 panorama graph with a seam-aware sampler or a
  panorama LoRA, if the user's server has those nodes.
- **A dedicated skybox service** (Blockade Labs Skybox AI at authoring time), with its own export.

Unattended, take the route the task allows and say which in the report.

## Common mistakes

- Calling a generic 2:1 image a skybox without the seam check: the edges almost never match.
- `outpaint_image` for the 2:1 step: its enum stops at `21:9`. Use an outpaint member with per-side
  pixel fields through `generate_image`.
- Inpainting the seam on the unrolled image: the seam is split across both edges, so the mask cannot
  cover it.
- Rolling back by a different width after an upscale: roll by half of the current width.
- A generative upscale at high creativity: it invents detail that breaks the wrap.
- Asking for 21:9 and expecting equirectangular: 360 viewing needs exactly 2:1.
