---
name: doestaxx-workflow-authoring
description: "Use when a task involves creating or editing a ComfyUI workflow graph: building a node graph from a brief, adding or rewiring nodes, converting a UI-format workflow JSON to API format, porting a graph from Scenario, Weavy, or another node tool, finding the right node or input names, or turning a prompt chain into a reusable graph. Running a graph is doestaxx-workflows. Keywords: ComfyUI, API format, object_info, class_type, node graph."
license: MIT
---

# Doestaxx Workflow Authoring

## Overview

A ComfyUI graph is authored as a JSON file in **API format** and run by `doestaxx-workflows`. There
are no per-node editing calls: every change is read, modify, write of the file, then a check against
the server. The editor's UI-format save holds layout and is not runnable; convert it or ask for an
API-format save.

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Quick reference

| Step             | Route                                   | Notes                                            |
| ---------------- | --------------------------------------- | ------------------------------------------------ |
| Node contract    | `GET /object_info/{class_type}`         | Input names, types, enum values, outputs         |
| All nodes        | `GET /object_info`                      | Large: save to a file, query it with `jq`        |
| Model files      | `GET /models/{folder}`                  | Exact names for `ckpt_name`, `lora_name`, others |
| Write the graph  | Edit the JSON file                      | API format, per below                            |
| Check            | `comfy_run.py check graph.json`         | Script ships with `doestaxx-workflows`           |
| Validate and run | `comfy_run.py run graph.json`           | `node_errors` names the bad input                |

Fetch routes with `curl -s "$COMFYUI_URL/object_info/KSampler"` (add the bearer header when
`COMFYUI_TOKEN` is set, without echoing it).

## API format

```json
{
  "4": { "class_type": "CheckpointLoaderSimple", "inputs": { "ckpt_name": "model.safetensors" } },
  "6": { "class_type": "CLIPTextEncode", "inputs": { "text": "a red lantern", "clip": ["4", 1] } },
  "9": { "class_type": "SaveImage", "inputs": { "images": ["8", 0], "filename_prefix": "out" } }
}
```

- Keys are node ids as strings. Ids need not be contiguous or ordered.
- A link is `["source_node_id", output_index]` on the consuming node's input. The index counts the
  source node's outputs as `/object_info` lists them (`output`), from 0.
- Widget values (seed, steps, text) are plain values on the same `inputs` object.
- A graph needs at least one output node (`output_node: true` in `/object_info`, such as
  `SaveImage`); without one the server rejects it.
- Enum inputs take one of the strings `/object_info` lists. Model names must match the server's
  files exactly, folder prefix included.
- `_meta.title` is optional and ignored at run time. Give key nodes a title so a later reader finds
  them.

## Worked example: a text-to-image graph with a LoRA

1. `GET /models/checkpoints` and `GET /models/loras` for exact file names. Ask the user which to use
   when several fit.
2. Read `/object_info` for `CheckpointLoaderSimple`, `LoraLoader`, `CLIPTextEncode`, `KSampler`,
   `EmptyLatentImage`, `VAEDecode`, `SaveImage`. Note each node's `input.required` names and its
   `output` list.
3. Write the graph: checkpoint `["4", 0]` (model) and `["4", 1]` (clip) into `LoraLoader`; its
   outputs feed `KSampler.model` and both `CLIPTextEncode.clip`; positive and negative encoders into
   `KSampler`; `EmptyLatentImage` into `latent_image`; `KSampler` into `VAEDecode` with
   `["4", 2]` as `vae`; `VAEDecode` into `SaveImage`.
4. `comfy_run.py check graph.json`, then a run at low steps and small size. A `node_errors` entry
   names node id and input: fix that input only.
5. Hand the file to `doestaxx-workflows` with the input keys a caller sets (`6.text`, `3.seed`).

## Converting a UI-format save

A UI-format file has `nodes` (each with `id`, `type`, `inputs`, `outputs`, `widgets_values`) and
`links` (`[link_id, from_node, from_slot, to_node, to_slot, type]`). Convert locally with a script,
never by retyping the file:

1. For each node, `class_type` is its `type`. Skip UI-only nodes (`Note`, `MarkdownNote`,
   `Reroute`: resolve a reroute to the link behind it) and muted or bypassed ones (`mode` 2 or 4;
   a bypassed node's input passes through to its consumer).
2. Linked inputs: for each `links` row, set the consumer's input named by its `to_slot` to
   `[str(from_node), from_slot]`.
3. Widget values: zip `widgets_values` with that node's widget input names in `/object_info` order.
   Some widgets add a UI-only control value (`control_after_generate` after a seed): drop it.
4. Group and subgraph nodes: expand them, or ask the user for an API-format save.
5. Run `check`; mismatches surface as `node_errors`. When conversion is ambiguous, ask the user to
   re-export with Save (API Format).

## Porting a graph from another tool

Scenario, Weavy, and other node tools have no ComfyUI import. Translate node by node:
[references/foreign-graph-import.md](references/foreign-graph-import.md) holds the mapping table and
the report the user gets. Read it before touching such an export.

## Common mistakes

- Wiring outputs by name: links use the output's index.
- Guessing model file names: the server matches them exactly.
- Leaving the `control_after_generate` value in a converted widget list: every later widget shifts
  by one.
- Pasting `/object_info` into the conversation: it runs to megabytes. Save it, query with `jq`.
- Editing a graph and not re-running `check`: a renamed custom node fails at queue time.
- Building a step in ComfyUI that Higgsfield's catalog already does well: keep the graph for what
  only ComfyUI does, per `doestaxx-workflows`.
