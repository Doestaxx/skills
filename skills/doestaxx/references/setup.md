# Connecting to the Higgsfield MCP server

- Endpoint: `https://mcp.higgsfield.ai/mcp` (HTTP transport, at authoring time). Confirm it against
  Higgsfield's own documentation if a connection fails.
- Auth: browser OAuth on first use. No API key is pasted into the conversation.

## Claude Code

```bash
claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp
```

Run `/mcp` inside a session to finish the browser sign-in.

## Other clients

Any client that supports remote HTTP MCP servers with OAuth takes the same URL. Add it as a remote
or "connector" server, then sign in when the client opens the browser.

## Re-authenticating

- A connection that worked and now fails with an auth error: remove the server's stored token in the
  client and sign in again before debugging anything else.
- Several Higgsfield workspaces: `list_workspaces`, then `select_workspace`. Generations land in the
  selected workspace.

## Optional: ComfyUI

The `doestaxx-workflows` skill runs node graphs on a ComfyUI server over its HTTP API. Set
`COMFYUI_URL` (for example `http://127.0.0.1:8188`) in the environment that runs the agent's shell.
A server needing a token reads it from `COMFYUI_TOKEN`; the agent never asks for its value.
