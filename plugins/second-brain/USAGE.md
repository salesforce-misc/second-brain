# second-brain

Operate an LLM-powered knowledge base rendered in Obsidian.

Claude Code uses the slash-command shorthand below. Codex and OpenCode invoke the
same shared skill by name and pass the same command and optional brain.

## Commands

```
/second-brain-setup [brain] # Bootstrap or update one root or named brain
/second-brain-doctor        # Diagnose or migrate project instructions
/second-brain ingest    # Ingest raw/ documents into wiki/
/second-brain compile   # Full consistency pass across the wiki
/second-brain ask       # Answer a question grounded in wiki content
/second-brain lint      # Health check - find gaps, orphans, contradictions
/second-brain obsidian  # Configure Obsidian and open a brain or the hub
```

A brain can live at the project root or under `brains/<name>/`. `ask` and `lint`
inspect all brains by default. `ingest` and `compile` require a brain name when the
project contains several.

Setup uses the sole discovered brain automatically. Supply a brain path when several
exist or when creating a named brain, such as `/second-brain-setup team-a/project-x`.

Use `/second-brain obsidian [brain]` to create missing portable core settings,
refresh path-based graph groups, and open the selected index. If several brains exist
and no name is supplied, it opens `brains/index.md`.

## Tests

```bash
# Unit tests (fast, no claude needed)
cd tests && python3 -m unittest -v

# Integration runner (runs claude -p against fixtures)
cd tests && ./run.sh

# Check an existing wiki project
cd tests && ./run.sh --check-only /path/to/project
```
