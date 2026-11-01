# Migration to Higgsfield

- Converted skills are named `doestaxx` and `doestaxx-<topic>` and run on Higgsfield. The core loop
  lives in `skills/doestaxx/SKILL.md`; every converted skill follows it.
- Skills still named `scenario-*` are unconverted and still target the Scenario MCP. Convert one
  before relying on it.
- Where the rules below name Scenario tools (`model_run`, `recommend`, `dry_run`), read them as the
  Higgsfield equivalents in the core skill (`generate_*`, `models_explore`, `get_cost`).
- Where Higgsfield lacks a capability, a skill lists the alternatives for the user to choose from
  (ComfyUI through `doestaxx-workflows`, local tools, named services) instead of substituting
  silently.

