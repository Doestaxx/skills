---
name: doestaxx
description: Use when a task involves generating images, video, 3D meshes, audio, textures, or game assets for Doestaxx, or choosing which provider runs a job: Higgsfield, fal.ai, a direct model API (OpenAI, Google, ElevenLabs, Runway, Meshy, Tripo), or ComfyUI. Also when pricing a run, uploading reference media, waiting on jobs, handing files between providers, or setting up a provider connection or API key.
license: MIT
---

# Doestaxx

## Overview

Doestaxx is the creative front end; the generation runs on API providers. This skill picks the
provider for each job and holds the rules every provider shares. Every sibling skill follows it.

| Provider          | Reached through                                          | Good for                                         | Details                                                |
| ----------------- | -------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| Higgsfield        | Its MCP connector                                        | Images, video, audio, 3D meshes, hosted 3D scene | [references/higgsfield.md](references/higgsfield.md)   |
| fal.ai            | [scripts/fal_run.py](scripts/fal_run.py), or a connector | Large open-model catalog, newest releases        | [references/fal.md](references/fal.md)                 |
| Direct model APIs | The vendor's connector, or its REST API                  | One vendor's own model, at the source            | [references/direct-apis.md](references/direct-apis.md) |
| ComfyUI           | `doestaxx-workflows`                                     | Custom node graphs, local models                 | The `doestaxx-workflows` skill                         |
| Doestaxx API      | Planned, not available yet                               | Will become the first choice once it ships       | None yet                                               |

Read the provider's reference file before its first job in a session. Connection setup:
[references/setup.md](references/setup.md).

## Choosing the provider

Take the first rule that decides:

1. **The user named one.** Use it, even when another is cheaper.
2. **A saved preference** for this kind of job. Apply it silently.
3. **Only one available provider can do it.** Use it.
4. **Several can.** Default to the connected MCP provider (Higgsfield) for a routine job. Offer the
   choice when the difference matters: a model only one provider hosts, a large price gap, or a
   quality bar the user set. Show each option's price.
5. **None can.** Stop and list the routes for the user to choose: another provider that has a
   dedicated model, a ComfyUI graph, a local tool (Blender, ffmpeg), or a service outside Doestaxx.
   Never substitute a weaker method silently.

Unattended, take the first route the task allows and name it in the report.

## Where each provider works

- **Connectors** (Higgsfield, any vendor connector) work in Claude chat, Cowork, and Claude Code.
- **Scripts** (`fal_run.py`, `comfy_run.py`, direct REST calls) need a shell with the key in an
  environment variable and network access to the provider's host. That means Claude Code, Cowork, or
  a chat whose code execution can reach that host.
- In chat, never ask the user to paste an API key. Route to a connected provider instead, and say
  which provider a key would unlock.

## Quick reference

| Step     | Every provider                                                                       |
| -------- | ------------------------------------------------------------------------------------ |
| Discover | Read the live catalog or model page; never reuse a model id from memory              |
| Contract | Copy field names and input roles exactly from the model's own schema                 |
| Price    | Price the exact request before running it, unless the user said cost does not matter |
| Run      | One request per independent job; record its job or request id before waiting         |
| Wait     | Poll the provider's own way; a timeout is never a reason to resubmit                 |
| Deliver  | Save outputs to disk at once (result URLs expire), show them, then hand the files on |

## Worked example: a concept sketch to a rigged, walking character

The user asks for "my knight sketch as a 3D character that walks".

1. **Route.** The user named no provider and there is no saved preference. Higgsfield is connected
   and has image-to-3D with rigging and an animation library, so it can do every step: rule 4,
   default route. Open [references/higgsfield.md](references/higgsfield.md).
2. **Prepare the input.** The sketch is a local file: upload it the provider's way (Higgsfield:
   `media_upload`, PUT, `media_confirm`).
3. **Discover and price.** Find an image-to-3D model with rigging in the live catalog, read its
   fields, and price the exact request with rigging and the walk clip on. Show the price.
4. **Run and wait.** Submit once, record the job id, and wait with the provider's polling tool until
   the job is terminal.
5. **Deliver.** Save the GLB, show it, and hand it on. For Blender or Unreal, the matching expert
   skill imports it. A mesh check belongs to `doestaxx-3d`.

Had the user asked for "the newest open 3D model on fal", rule 1 applies: open
[references/fal.md](references/fal.md), read the model page, and run `fal_run.py` from a shell with
`FAL_KEY` set. In a chat without a shell key, say that, and offer Higgsfield instead.

## Handing files between providers

- Every provider takes inputs its own way: Higgsfield a `media_id`, fal a public URL or small data
  URI, ComfyUI a filename on its server, a vendor API whatever its docs say.
- So save each output to disk first, then upload it to the next provider. Never pass one provider's
  signed URL or id to another and assume it resolves.

## Sibling skills

If a sibling skill named here is missing from your available skills, ask the user to install it from
the Doestaxx skills repository (https://github.com/Doestaxx/skills); unattended, proceed from tool
schemas and flag the gap.

## Common mistakes

- Asking for, echoing, or logging an API key. Keys live in environment variables only.
- Resubmitting after a timeout or a dropped connection: check whether the job exists first.
- Reusing a model id from memory. Catalogs change on every provider.
- Passing a URL where Higgsfield wants a `media_id`, or a local path where fal wants a URL.
- Leaving outputs at their result URLs. They expire; save them.
- Switching provider mid-job without saying so. A route change is the user's call.
