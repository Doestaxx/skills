# Direct model APIs

Some jobs go straight to the company that built the model: OpenAI or Google for images and video,
ElevenLabs for voice and sound, Runway for video, Meshy or Tripo for 3D (examples at authoring
time). Each vendor has its own API, key, and pricing, so this file holds rules, not endpoints.

## Pick the route

1. **A connector.** If the vendor's MCP connector is connected, use its tools. Connectors work in
   Claude chat, Cowork, and Claude Code alike.
2. **The vendor's documented REST API.** Only from a shell that holds the key in an environment
   variable and can reach the vendor's host.
3. **Neither.** Say so, and offer the providers that are connected instead.

## Before the first call

- Read the vendor's current API reference with a web fetch: endpoint, model id, input fields, size
  limits, and whether the job is synchronous or polled. Never rebuild an endpoint from memory.
- Read the price from the vendor's pricing page and tell the user before the first run.
- Confirm the key's environment variable is set without printing it: `test -n "$OPENAI_API_KEY"`.
  Never echo, log, or ask the user to paste a key.

## Making the call

- Send the key only in the header the vendor documents, and only to the vendor's own host.
- A polled job: save its id to a file before waiting, so an interrupted wait resumes instead of
  resubmitting.
- Save every returned file to disk at once; signed result URLs expire.
- A connection error after the request was sent may still have created a job. Check the vendor's job
  list or ask before any re-run.

## Handing results on

- To another provider: upload the saved file through that provider's upload route (Higgsfield's
  `media_upload`, a public URL for fal, `/upload/image` for ComfyUI).
- Into Blender or Unreal: import the saved file locally with the matching expert skill.
