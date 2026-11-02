# Session channel: tools and limits

The session channel for this skill is the Higgsfield use Blender MCP server,
`higgsfield-use-blender` (`fnf-blender-mcp`). It runs one dedicated background Blender per MCP
connection; setup is in the `doestaxx-blender` skill. Read each tool's input schema from the
server's tool list before its first call.

| Need                           | Tool                                                                |
| ------------------------------ | ------------------------------------------------------------------- |
| Start and check the session    | `bl_health` (version, PID, `background: true`, active file, scene)  |
| Load the user's saved file     | `bl_open_project`                                                   |
| Probe before building          | `bl_get_scene_summary`                                              |
| Scene guidance from the server | `bl_get_skill` with `name: "blender-scene"`, before the first edit  |
| Build, key, audit              | the server's Python tool: fill `result` with what you need back     |
| Look through the shot camera   | `bl_render` (set the frame and resolution in Python first)          |
| A call still running           | `bl_job_status` with its `job_id`                                   |
| Save                           | `bl_save_project` to a new path unless the user allowed `overwrite` |

- It never attaches to a Blender window, and there is no viewport screenshot. Unsaved work in the
  user's window is unreachable: they save it, then `bl_open_project` loads it.
- Scene datablocks persist between calls; Python local variables do not. Re-import the toolkit and
  look objects up by name in every call.
- A timeout neither cancels nor repeats a command: poll `bl_job_status`. Other execution tools
  refuse calls while that job runs; status tools stay usable.
- Send one stage piece per call (a set section, one figure, one rig, one audit), so a failure is
  small. Errors can leave partial changes: read the scene before sending a call again.
- Reconnecting, stopping the server or a crash loses unsaved state; nothing restarts by itself. Run
  `B.stage_backup(label)` after each stage and `bl_save_project` at milestones.
- Long renders and playblasts: raise the client's tool timeout above 300 s, or run them headless on
  a saved copy.
