# fal.ai: the queue API

fal hosts a large catalog of image, video, audio, and 3D models behind one queue API. The agent
reaches it with the skill's `scripts/fal_run.py`, which needs `FAL_KEY` in the environment and
outbound HTTPS to `queue.fal.run` and `fal.media`.

## Facts the script relies on

From fal's queue documentation at authoring time:

- Submit: `POST https://queue.fal.run/<model id>` with `Authorization: Key $FAL_KEY` and the model's
  input as the JSON body. The model id keeps its subpath (`fal-ai/flux/dev`).
- The submit response carries `request_id`, `status_url`, `response_url`, and `cancel_url`.
- Status values: `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`.
- Status and result URLs use only the owner and app (`fal-ai/flux`), not the full model id. Use the
  URLs the submit response returned; a hand-built one can answer 405.
- Output media URLs are public and expire. Download them right away.
- Inputs accept hosted URLs or base64 data URIs. fal recommends URLs for anything over a few KB.

## Procedure

1. **Find the model.** Read the model's page on fal.ai (its API tab) with a web fetch. Copy the
   input field names and the model id exactly. Never reuse an id from memory: the catalog changes.
2. **Price.** fal bills per request or per output unit, shown on the model page. Tell the user the
   price before the first run unless they said cost does not matter.
3. **Run.**

   ```bash
   python3 <skill dir>/scripts/fal_run.py run <model id> \
     --input '{"prompt": "a brass lantern, studio light"}' \
     --set num_images=2 --out out/lantern
   ```

   - `--set KEY=VALUE` parses JSON values and dotted keys (`--set image_size.width=1024`).
   - `--file image_url=ref.png` inlines a small local file as a data URI.
   - A large input goes in as a public URL: a result URL another provider returned works.

4. **Read the report.** The script prints the saved files and `result.json`. Show the user the
   result, then hand on the files.

## Exit codes

- `0`: done, files saved.
- `1`: usage or HTTP error. The message names the field or status.
- `3`: timed out while the request is still queued or running. Run
  `python3 <skill dir>/scripts/fal_run.py resume <out dir>`. Never resubmit: that pays twice.
- `4`: the run ended without a result. Read the message before changing the payload.

## Where it runs

- Claude Code, Cowork, or any shell with `FAL_KEY` set and network access to fal's hosts.
- Claude chat has no environment variables for keys. Never ask the user to paste a key into the
  conversation. In chat, use a fal connector if the user has one, or route the job to a connected
  provider.
