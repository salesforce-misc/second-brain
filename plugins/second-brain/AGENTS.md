# second-brain

`AGENTS.md` is canonical. `CLAUDE.md` imports it for Claude Code compatibility
during the transition.

## File management

- The main skill is at `skills/second-brain/SKILL.md`
- Setup/bootstrap skill is at `skills/second-brain-setup/SKILL.md`
- Migration doctor is at `skills/second-brain-doctor/SKILL.md`
- Visual formatting reference: `reference.md` at the plugin root
- Obsidian setup helper: `scripts/obsidian.py`

## Testing

- Unit tests: `cd tests && python3 -m unittest -v`
- OpenCode adapter: `node --test opencode/test-second-brain.mjs`
- Integration runner: `cd tests && ./run.sh`
- Check existing wiki: `cd tests && ./run.sh --check-only /path/to/project`

## Plugin structure

- `.claude-plugin/plugin.json` - plugin metadata
- `.codex-plugin/plugin.json` - native Codex metadata for the shared skills
- `opencode/` - OpenCode adapter, activation instruction, and direct Node test
- `skills/second-brain/SKILL.md` - main operator skill (ingest, compile, ask, lint, Obsidian)
- `skills/second-brain-setup/SKILL.md` - project bootstrap and bounded instruction management
- `skills/second-brain-doctor/SKILL.md` - safe instruction diagnosis and migration
- `scripts/obsidian.py` - discovers brains and prepares one shared Obsidian vault
- `reference.md` - Obsidian visual formatting guide
- `tests/` - integration and unit tests

## Obsidian contracts

- Support one root brain and nested `brains/<name>/` brain roots. Exclude `_template`
  path segments from discovery.
- Preserve existing portable settings. Create only missing core settings.
- Keep `config/obsidian/graph.json` shared and generated runtime state ignored.
- Use Python standard library code and Obsidian core plugins only.
- Setup must resolve one brain before it creates `raw/`, `wiki/`, or `output/`.
- Keep both skills provider-neutral. Claude Code slash commands are shorthand only.
- Keep workflow logic in `skills/`. Runtime manifests and adapters only expose it.
- Setup owns only its bounded section in a project `AGENTS.md` file.
- Claude Code support depends on its enabled `agents-md@builtin` plugin. Its default
  mode requires the project to have no project `CLAUDE.md`, `.claude/CLAUDE.md`, or
  `CLAUDE.local.md` on the active path.
- Setup must reject symlinked, non-regular, or out-of-brain instruction files.
- Doctor diagnoses before changes, requires consent for moves and replacements, and
  preserves conflicting instruction files.
