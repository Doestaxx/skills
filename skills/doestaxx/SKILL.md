---
name: doestaxx
description: Use when connecting an AI agent to the Doestaxx creative pipeline on the Higgsfield MCP, or when a task involves generating images, video, 3D meshes, audio, textures, or game assets there. Also when picking a Higgsfield model, uploading reference media, waiting on generation jobs, pricing a run, checking credits, choosing a project folder, or hitting Higgsfield auth, unlim, or recovery_tool responses.
license: MIT
---

# Doestaxx on Higgsfield

## Overview

Doestaxx skills generate through the Higgsfield MCP server: images, video, audio, and 3D meshes from
one catalog, plus bundled recipes and a hosted 3D scene builder. This skill is the core loop every
sibling skill builds on. When Higgsfield cannot do a step, the sibling skill lists the other routes;
node-graph pipelines run on ComfyUI through `doestaxx-workflows`.

## Setup

- Endpoint and client config: [references/setup.md](references/setup.md). OAuth in the browser; no
  API key passes through the conversation.
- Never ask the user to paste, encode, or echo a secret.
- A previously working connection now failing: re-authenticate before debugging.
- Tool names below are bare (`generate_image`). Hosts prefix them (`mcp__Higgsfield__generate_image`).

## Quick reference

| Step             | Tool                                                     | Notes                                                   |
| ---------------- | -------------------------------------------------------- | ------------------------------------------------------- |
| Find a model     | `models_explore` `recommend` or `search`                 | Free; pass `type` and the user's own words              |
| Read constraints | `models_explore` `get` with `model_id`                   | Parameters, `medias[].roles`, aspect ratios             |
| Price            | `generate_*` with `get_cost: true`                       | No job is submitted                                     |
| Generate         | `generate_image`, `_video`, `_audio`, `_3d`              | All arguments inside `params`, beside `model`           |
| Batch            | `generate_image_batch`, `_video_batch`, `_audio_batch`   | 2 to 12 independent requests                            |
| Wait             | `jobs_wait`                                              | Up to 12 jobs, 15 s per call; poll until `all_terminal` |
| Show             | `show_generation_by_ids` (batch) or `job_display` (one)  | Once, after every job is terminal                       |
| Upload           | `media_upload`, PUT, `media_confirm`                     | Local file to `media_id`                                |
| Import a URL     | `media_import_url`                                       | Web media to `media_id`                                 |
| Destination      | `get_preferences`, `create_project`, `folder_id`         | Before the first generation in a conversation           |
| Recipes          | `get_workflow_instructions`, `get_preset_instructions`   | Load before the jobs they own                           |
| Credits          | `balance`, `transactions`                                | Read only                                               |

## Worked example

A textured game prop from a concept image:

1. **Destination.** Call `get_preferences` before the first generation of the conversation.
   - Create a project with `create_project` only when `auto_create_project` is true or the user asks
     for one. Reuse its `default_folder_id` as `folder_id` on every later generation.
   - An existing destination the user names wins. Never change saved preferences for a one-off
     request.
2. **Upload.** Local file the shell can read:
   - `media_upload` with `filename` (or `files[]`, up to 20).
   - PUT the raw bytes to each `upload_url` with `curl -T`, and check every PUT returned 200.
   - `media_confirm` with `media_id` (or `media_ids`) and `type` (`image`, `video`, `audio`).
   - A web URL goes through `media_import_url` instead. Only when the bytes are unreadable, call
     `media_upload_widget` as the only tool in that turn.
3. **Discover.** `models_explore` with `action: "recommend"`, `type: "3d"`, and a `query` holding the
   user's words plus input context ("textured PBR prop from one reference image").
   - `search` when the user names a model; `list` with `type` to browse.
   - Re-discover each time. Never hard-code a generative model id in a script or doc.
4. **Read the contract.** `models_explore` `get` on the pick. Copy parameter names verbatim and read
   `medias[].roles`: one model takes `image`, another `image_references`.
5. **Price.** The same call you will run, with `get_cost: true`. Show the user the credit cost
   unless they said cost does not matter.
6. **Run.** `generate_3d` with `params: {model, medias: [{role, value}], ...fields}`.
   - `medias[].value` is a `media_id` or a prior `job_id`. A URL there fails.
   - `count` (1 to 4) is variants of identical inputs. Independent prompts go to a batch tool.
   - Apply any `adjustments` the server returns. If it returns `recovery_tool`, call that tool at
     once, before explaining.
7. **Wait.** `jobs_wait` with `jobs: [{index, job_id}]`. When `all_terminal` is false, wait
   `poll_after_seconds` and call again. A timeout is not a failure and never justifies a re-run.
8. **Show and save.** One `show_generation_by_ids` for a batch, or `job_display` for one job. Save
   files with `curl -L` on the result URL `jobs_wait` returned.

## Paying for a run

- `use_unlim`: omit it and let the server decide. If it returns `unlim_choice`, put that question to
  the user, then call again with the same params plus their answer. Pass `true` only when the user
  asks to spend unlimited generations.
- `use_free_gens`: only when the user explicitly asks. A rejected free request never falls back to
  credits without approval.
- `balance` reports credits and plan. `show_plans_and_credits` opens the upgrade view; never buy,
  upgrade, or cancel anything yourself.

## Recipes and presets

- `get_workflow_instructions` with no argument lists Higgsfield's bundled recipes and their
  triggers. Load the matching one before its jobs (character sheets, product shots, thumbnails,
  websites).
- `get_preset_instructions` resolves slash commands. `/3d-jutsu` is the hosted 3D scene builder;
  `/use-blender` sets up the local Blender MCP. `doestaxx-blender` teaches both.
- These are fixed recipes, not editable graphs. Custom node graphs belong to `doestaxx-workflows`.

## When Higgsfield cannot do it

Check `models_explore` first: the catalog changes. When nothing fits, stop and give the user the
options instead of substituting silently:

- **ComfyUI** through `doestaxx-workflows`: any node graph the user's ComfyUI server can run.
- **Local tools**: Blender, ffmpeg, or a script on the user's machine, when the step is
  deterministic.
- **Another hosted service** the sibling skill names for that capability.

Unattended, take the first route the task already allows and say which in the report.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Errors and recovery

- **Transport timeout on a `generate_*` call**: the job may exist. Never resubmit automatically.
  Check `show_generations` for it, or ask, before any re-run.
- **`recovery_tool` in a response**: call it immediately with what it asks for.
- **Rejected opt-in** (`use_unlim` or `use_free_gens`): reported, never silently charged. Ask before
  retrying on credits.
- **Media role rejected**: re-read `medias[].roles` from `models_explore` `get`. The server coerces
  roles only when unambiguous.
- **3D tools taking `model_url`** (rigging, remesh, retexture): pass the completed GLB's public HTTPS
  URL, or the `url` `media_upload` returned for an uploaded `.glb` (confirmed as `type: "file"`).
  Never its `upload_url`, never a `job_id`.

## Common mistakes

- Putting a URL in `medias[].value`: it takes a `media_id` or `job_id` only.
- Arguments outside `params`: model fields sit beside `model` inside `params`.
- Calling `job_display` once per batch job: use one `show_generation_by_ids` for the set.
- Looping `jobs_wait` without reading `poll_after_seconds`, or passing more than 12 jobs.
- Generating before `get_preferences`: results land outside the user's project.
- Using the catalog's game-pipeline-only audio models for standalone audio: the `generate_audio`
  description names them.
- Asking the user to re-upload a file the shell can already read.
