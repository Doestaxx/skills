---
name: doestaxx-workflows
description: "Use when a task involves running a node-graph pipeline: a ComfyUI workflow, a saved app or multi-step generation graph, anything the user calls a workflow, or a step Higgsfield's catalog cannot do. Triggers include queueing a ComfyUI API-format graph, setting its inputs, uploading reference images to ComfyUI, waiting on a prompt_id, downloading outputs, node_errors, missing custom nodes, or chaining ComfyUI and Higgsfield. Creating or editing graphs is doestaxx-workflow-authoring."
license: MIT
---

# Doestaxx Workflows

## Overview

A workflow is a node graph run on a ComfyUI server through its HTTP API. ComfyUI runs whatever nodes
and model files the user's server holds, so it covers steps the Higgsfield catalog lacks: custom
LoRAs, ControlNet chains, 360 panorama models, splat or depth nodes. Higgsfield stays the route for
everything its catalog does, per the `doestaxx` skill. Creating and editing graphs:
`doestaxx-workflow-authoring`.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

[scripts/comfy_run.py](scripts/comfy_run.py) is the agent's tool for every step below: it checks
the server, uploads images, queues a graph with input overrides, waits, and downloads outputs. It
uses only the standard library. Run it with `python3`; `--help` prints its subcommands.

## Setup

- `COMFYUI_URL` in the shell's environment names the server (for example `http://127.0.0.1:8188`).
  Unset: ask the user for it, never guess a host.
- `COMFYUI_TOKEN`, optional, is sent as a bearer token for a server behind an auth proxy. Never ask
  for, print, or echo its value.
- A vanilla ComfyUI server has no authentication. Never suggest exposing its port to the internet;
  a reverse proxy with auth goes in front.
- A server on the user's own machine is unreachable from a cloud sandbox. Run the script on that
  machine (a linked device shell), or use a server the sandbox can reach.

## Quick reference

| Step              | Command or route                                           | Notes                                    |
| ----------------- | ---------------------------------------------------------- | ---------------------------------------- |
| Reach the server  | `comfy_run.py check`                                       | Version and devices from `/system_stats` |
| Check the graph   | `comfy_run.py check graph.json`                            | Every `class_type` in `/object_info`     |
| Upload an image   | `comfy_run.py upload ref.png`                              | Prints the `LoadImage` value             |
| Run               | `comfy_run.py run graph.json --set 6.text='"..."' --out d` | Queues, waits, downloads                 |
| Fixed recipe      | `get_workflow_instructions` (Higgsfield)                   | Bundled recipes, not editable            |

API routes behind the script: `POST /prompt` queues (`prompt_id`, or 400 with `node_errors`),
`GET /history/{prompt_id}` holds outputs once done, `GET /view` serves files, `POST /upload/image`
stores inputs, `POST /interrupt` stops the running prompt.

## Graph formats

- `/prompt` takes **API format**: an object keyed by node id, each `{class_type, inputs}`, links as
  `["node_id", output_index]`. The editor saves it with **Save (API Format)** (older builds need dev
  mode on).
- A UI-format save (a `nodes` list plus `links`) is rejected by the script with a pointer to
  `doestaxx-workflow-authoring`, which converts it.
- An input's key is `NODE_ID.INPUT_NAME`. Read ids and names from the graph file itself; node
  titles in the editor are not keys.

## Worked example: a ComfyUI graph inside a Higgsfield pipeline

The user has a ComfyUI graph that turns a reference photo into a stylized 360 panorama with their
LoRA, then wants a 3D prop on Higgsfield from the same photo.

1. `comfy_run.py check pano.json`. A non-empty `missing_class_types` names custom nodes the server
   lacks: stop and report them; installing nodes or model files is the user's call.
2. Read the graph locally (`jq 'to_entries[] | {id: .key, c: .value.class_type}' pano.json`), never
   pasted whole into the conversation. Find the `LoadImage`, prompt (`CLIPTextEncode`), seed, and
   save nodes.
3. `comfy_run.py upload photo.jpg`. Pass the printed `load_image_value` to the `LoadImage` node's
   `image` input.
4. `comfy_run.py run pano.json --set 10.image='"photo.jpg"' --set 6.text='"misty pine forest"' --set 3.seed=7 --out pano`.
   `--set` values parse as JSON first, so quote strings as JSON.
5. Exit codes: `0` saved files are listed in the printed JSON; `2` the server rejected the graph and
   printed `node_errors` per node; `3` timed out while queued or running; `4` the run failed.
   - On `2`, fix the named input. Never retry the same payload.
   - On `3`, never resubmit: the prompt is still queued. Check `/history/{prompt_id}` later or rerun
     with a longer `--timeout` only after it is gone from `/queue`.
6. Hand the result to Higgsfield when a later step runs there: `media_upload`, PUT, `media_confirm`
   per the `doestaxx` skill, then use the `media_id` in `generate_*`.
7. The reverse direction: save a Higgsfield result with `curl -L` on the URL `jobs_wait` returned,
   then `comfy_run.py upload` it.

## When neither ComfyUI nor Higgsfield covers it

Stop and give the user these options to choose from:

- **Install what is missing on their ComfyUI server**: the custom node pack or model file a missing
  `class_type` belongs to (ComfyUI Manager can do it). The user installs it.
- **A hosted ComfyUI**: Comfy's own cloud (`cloud.comfy.org`, API key in an `X-API-Key` header at
  authoring time; its API differs from a local server's) or a GPU host running ComfyUI. The user
  sets `COMFYUI_URL` to it.
- **Higgsfield's bundled recipes**: `get_workflow_instructions` lists them; one may already do the
  job as a fixed recipe.
- **A local tool**: Blender (`doestaxx-blender`), ffmpeg, or a script, for deterministic steps.

Unattended, take the first option the task already allows and say which in the report.

## Common mistakes

- Sending a UI-format save to `/prompt`: validation fails on every node.
- Retrying after `node_errors`: the same payload fails the same way.
- Resubmitting after a timeout: the first prompt still runs and both are billed in GPU time.
- Reading `/history/{id}` as failed when it returns `{}`: the prompt is not finished yet.
- Passing a Higgsfield result URL into a ComfyUI `LoadImage`: it reads files on the server only;
  upload first.
- Guessing a `LoadImage` value after uploading into a subfolder: it is `subfolder/name`, printed by
  the script.
- Pasting a whole graph JSON into the conversation: summarize it locally first.
