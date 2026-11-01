# Porting a graph from another node tool into ComfyUI

A graph built in Scenario, Weavy, or another node editor does not import into ComfyUI. It is
translated: read the source, map each node onto ComfyUI nodes or onto a Higgsfield step, write an
API-format graph, check it, and report what did not map. The result reproduces the pipeline's shape.
Per-node output differs because the models differ, so never promise parity with the source's
renders.

## Read the source as a table

Every node editor exports a node list (type, parameters), a connection list, and the nodes exposed as
inputs and outputs. Field names differ per tool and version, so locate all three in the file:

- Scenario: `editor_info` with `nodes`, `edges` (persisted consumer to producer, the reverse of the
  data flow), and `inputKeys`.
- Weavy: a JSON with nodes and edges.

Reduce the file locally, with a script, to one row per node: source id, kind, model or operation,
parameters, incoming connections. Exports run to thousands of lines; never paste one into the
conversation.

## Map each row

- **Text constant, prompt box**: `CLIPTextEncode` text, or a primitive string node when several
  nodes share it. Exposed inputs become input keys the caller sets (`6.text`).
- **Image input, file upload**: `LoadImage`. The file is uploaded with `comfy_run.py upload` at run
  time.
- **Prompt template, concatenation**: a string-concatenate node if the server has one (custom packs
  differ), else build the text before queueing and set it with `--set`.
- **LLM prompt writer or captioner**: keep it only if the user's server has an LLM node pack. Else
  run that step outside ComfyUI and pass its text in. Never add an enhancement step the source
  lacked.
- **Generator** (text-to-image, image-to-image, upscale): the checkpoint, LoRA, sampler, and decode
  chain for that model family, with the server's exact model file names from `/models/{folder}`.
  Transfer `seed`, `steps`, size, and batch only where the target input has the same meaning.
- **Video, 3D, audio, or a hosted vendor model** (a Kling, Seedream, or Meshy member): usually not on
  a ComfyUI server. Map it to a Higgsfield `generate_*` step outside the graph, per the `doestaxx`
  skill, and chain the two per `doestaxx-workflows`.
- **Branch, switch, condition**: a switch node from a custom pack if installed, else split into
  separate graphs the agent chooses between.
- **Loop, for-each**: no core loop node. Run the graph once per item with different `--set` values.
- **Preview, save, output**: `SaveImage` (or the pack's save node for video and audio). A preview
  node writes temp files the script skips unless `--include-temp`.
- **Approval or human review**: no ComfyUI equivalent. Stop between runs and show the user.
- **Code, HTTP request, webhook, plugin**: unmapped. List it for the user.

## Emit, check, report

1. Write the API-format graph per the main skill.
2. `comfy_run.py check graph.json`. Missing `class_type` values are custom packs the server lacks:
   list them with the pack the user would install, or remap to core nodes.
3. A low-cost run (few steps, small size) surfaces wiring errors as `node_errors`.
4. Report per source node: the ComfyUI nodes or Higgsfield step it became, parameters that did not
   transfer, nodes that did not map, and what the user finishes by hand.

## Common mistakes

- Keeping one ComfyUI node per source node: a source "generator" node expands into a loader,
  encoders, a sampler, and a decoder.
- Reading Scenario's persisted edge direction as data flow: it is reversed.
- Copying a setting because its number fits: `cfg` and `guidance` mean different things across
  families. Transfer a value only when the meaning matches; otherwise keep the default and list it.
- Forcing a hosted vendor model into ComfyUI: route it to Higgsfield instead.
