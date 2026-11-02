# Migrating skills to Doestaxx

- Converted skills are named `doestaxx` and `doestaxx-<topic>` and run on Doestaxx's providers
  (Higgsfield, fal.ai, direct model APIs, ComfyUI). The core loop lives in
  `skills/doestaxx/SKILL.md`; every converted skill follows it.
- Skills still named `scenario-*` are unconverted and still target the Scenario MCP. Convert one
  before relying on it.
- Where AGENTS.md names Scenario tools (`model_run`, `recommend`, `dry_run`), read them as the
  provider equivalents in the core skill: on Higgsfield `generate_*`, `models_explore`, `get_cost`;
  on fal.ai `scripts/fal_run.py` and the model page.
- A converted skill teaches the default route with Higgsfield tool names and lists fal.ai and direct
  model APIs among its options. Provider details live only in the core skill's references.
- The `doestaxx-studio` plugin is generated: every top-level `doestaxx*` skill joins it
  automatically. `python3 scripts/package_studio_plugin.py` builds the zip for Claude chat.
- Where no provider has a capability, a skill lists the alternatives for the user to choose from
  (ComfyUI through `doestaxx-workflows`, local tools, named services) instead of substituting
  silently.
