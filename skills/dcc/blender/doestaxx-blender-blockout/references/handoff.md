# Hand-off sheet and the render-to-real pass

The sheet ships with the playblast, and the video prompt is written from it. Every number in it is
read off the built scene, never retyped from the brief.

## Sheet template

```markdown
# <scene> blockout hand-off

Format: <fps> fps, <W>x<H>, frames 1..<end> (<seconds> s). Playblast: <file>. Stills: <files>.

## Color legend

| Color  | Element        | Becomes (reference)                                 |
| ------ | -------------- | --------------------------------------------------- |
| red    | FIG_red (hero) | <role> in a red <garment you name>, @image1 panel 1 |
| yellow | FIG_mia (hero) | Mia's yellow raincoat, @image1 panel 2              |
| blue   | FIG_blue       | <role>                                              |

## Cut list (from B.cut_list())

| Shot | Camera     | Frames | Start | End   | Duration | Lens     | Move         |
| ---- | ---------- | ------ | ----- | ----- | -------- | -------- | ------------ |
| 1    | CAM_01_... | 1-87   | 0.000 | 3.625 | 3.625 s  | 28-28 mm | slow push-in |

## Cast (from K.cast())

| Figure  | Style    | Color | Height | Features       | Becomes          |
| ------- | -------- | ----- | ------ | -------------- | ---------------- |
| FIG_red | featured | red   | 1.55 m | goggles, scarf | <role>, the lead |

## Entities

- Blocked as proxies: <list, with what each mass is: "the boxes on the bench are luggage">.
- Text only, not in the clip: <extras, crowds, police>, with counting rules ("no more than four
  pedestrians").

## Artifacts, with timecodes

- <00:02.10-00:03.00> black frames: gap for invented content (<what>).
- Floor grid: motion-tracking aid, replace, never inherit.

## Motion states

- <element>: <creeps forward | stands perfectly still | rolls at walking pace>.

## Tie-breaks

- The clip defines the whole camera path; nothing else about the camera is inherited.
- If text and clip disagree about motion or position, the clip wins.
- Every placeholder becomes the real object its position and size imply.
```

Exact times go here (7.792 s), approximations belong only in the brief. A slow proxy move is
ambiguous on screen, so write its state in words; the same motion has been read as rolling and as
standing still.

## Prompt grammar: motion first

A prompt that names the proxies' shapes ("the box figure becomes", "each cone is") anchors the model
on those shapes and it renders them as they are. Describe the finished shot instead, as if it
already existed. This grammar is for Seedance-style reference models; a 3D-to-video model that asks
what each proxy stands for takes the replacement-map grammar in [levels](levels.md).

1. **Rehearsal header.** "The reference video is rehearsal footage: stand-ins walked the scene so
   camera, timing and movement could be locked. The final shot replaces every stand-in with the real
   cast and set. Take from the video only the camera path and framing, the timing of every action,
   and each element's screen position, path, ground contact and scale. No shape, proportion,
   silhouette or surface in the video belongs in the final frame."
2. **Cast list by role and motion**, one line per moving element, then the set: "A woman in a teal
   wax jacket walks down the corridor toward camera." Take roles from the object names; keep the
   names and shapes out of the prompt.
3. **Proportion license.** "Where a stand-in's proportions differ from the real object's, keep its
   path, timing and ground contact and give the real object its true proportions."
4. **No geometry words** about the video's contents after the header: no box, cone, sphere, proxy,
   dummy, mannequin, blockout. Real object names stay allowed when they describe the finished scene
   (a traffic cone, a boxing ring). One exception: a capsule cast gets one stand-in clause saying
   the capsules only mark position, height, pace and heading, and a gait clause ([cast](cast.md)).
5. **Short exclusion tail.** "No blocky placeholder geometry, no mannequin figures, no untextured
   surfaces."
6. **Style from a board.** Declare it: "The reference image is a style board of four separate
   panels: take its art style, palette, materials and lighting, nothing else. Its subjects,
   compositions and angles are not part of the shot; never copy a panel's layout and never draw its
   gutters or a grid."
7. **Style block last**: the treatment by name, the palette as hex values with roles, sky,
   background falloff, every light source.

A volume that must become an effect stays a cast line too: "steam rises from a flush iron floor
grate, widest at the base" refills a cone's volume without naming it.

This full prompt is for the video pass below. Name each reference's role in words as well as by any
tag the model's guidance defines: the clip governs camera, motion and layout, the board style only.

## Style board

One 16:9 image holding a 2x2 board, four panels in one identical style at deliberately different
angles and croppings: a character portrait (the cast's identity), a wide of the environment from
another camera height, a prop macro, a set-dressing detail. A single restyled frame of the shot
carries its own composition and shapes into the video; panels at angles the clip never uses transfer
identity without a layout to copy. Generate it with `generate_image` (see the `doestaxx` skill),
then gate it as strictly as a final render: any primitive that survives into it, a box head above
all, is rendered into the video. Check heads and faces explicitly.

## Tested limits (observed at authoring time)

- Shorter clips hold layout better: in one audit of 28 renders, 10 to 15 s clips kept the camera and
  layout, 20 to 30 s clips drifted (lost figures, invented close-ups). Several short captures beat
  one long one. Read the reference-video length cap from the model's schema.
- A bare gray mannequin playblast was refused by a provider's input screen, and re-encoding did not
  help; saturated identity colors, or a strong color tint over the whole clip, passed. The clip only
  contributes camera, motion and layout, so a tint costs nothing. For a refusal on output, read the
  whole error, then change the prompt or the input, never resend the same payload.
- A failed job's real reason can sit in its error detail rather than the headline message: read the
  whole error before changing the payload.
- Pick the frame to restyle by content, not position: frame 1 is often an empty establishing hook.
  Below a useful amount of detail, generate a pure style image instead.
- When a vision check compares a restyled frame with the blockout, say the frames should differ, or
  it fails frames for succeeding. Blocking checks: surviving primitives (textured primitives
  included), flipped facing, unrelated subject. Camera and layout drift in a style frame is
  advisory, since the video takes layout from the clip. Cap retries at three and log the best
  attempt.
- Image models recast photographic and character briefs reliably and resist abstract ones (colored
  cylinders, mannequins at a table); expect to pick or author those style frames by hand.

## The video pass on Higgsfield

For the full-resolution playblast from `bx_review.playblast` (cuts follow the bound markers; its
Workbench render shows the Material colors). Prices are shown to the user and spent only after they
approve the exact credit cost.

1. Upload the MP4 and the style board: `media_upload` with both filenames, PUT each file to its
   `upload_url`, then `media_confirm` (`type: "video"` for the clip, `"image"` for the board). Keep
   both `media_id`s.
2. Discover a model that takes a reference video: `models_explore` with `action: "recommend"`,
   `type: "video"`, and the brief's words plus "reference video for camera and motion". Read `get`
   on the pick for its media roles (`video_references`, `image_references`), its `mode` options and
   its `duration` range.
   - An omni-reference model takes the clip and the board together; set its reference `mode` when
     the schema has one.
   - A motion-transfer model copies the clip's motion onto subjects in reference images: it fits a
     single-hero shot, not a set.
3. Build `params` from that contract: `model`, `prompt` (the grammar above), `medias` with the clip
   under `video_references` and the board under `image_references`, `duration` set to the clip's
   length when the schema has the field (rounded into its range), resolution and aspect ratio from
   the hand-off sheet.
4. `generate_video` with `get_cost: true`, show the credits, then run after approval. `jobs_wait`
   until terminal, `job_display`, and save the file from the result URL with `curl -L`.

A timed-out `generate_video` is never resent: check `show_generations` for the job first.

## When Higgsfield cannot do it

Stop and give the user the options when no Higgsfield model takes a reference clip, the clip runs
past every model's length cap, or the model refuses the input:

- Split the playblast into shots under the cap and render each, then join them with
  `doestaxx-workflows` or ffmpeg.
- A ComfyUI video-to-video graph the user runs, through `doestaxx-workflows`.
- The original Scenario for Blender extension's Render Video lane, if the user keeps a Scenario
  account (github.com/scenario-labs/blender-plugin).
- Another hosted render-to-real service the user names.

Unattended, take the first option the task allows and say which in the report.

## Judge the pass

Put the playblast and the render side by side at the same height and sweep the result rather than
spot-checking it:

```bash
ffmpeg -i playblast.mp4 -i render.mp4 -filter_complex "[0:v]scale=-2:540[a];[1:v]scale=-2:540[b];[a][b]hstack" side_by_side.mp4
ffmpeg -i side_by_side.mp4 -vf "fps=2,scale=800:-2,tile=4x6" sheet_%02d.png
```

Check per shot: camera path, framing and cut frames match; every colored element became its role at
its position and scale; no primitive survived; facing held; the ending held. A miss in geometry goes
back to the blockout; a miss in identity or look goes back to the prompt or the board.
