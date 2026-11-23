# Installing second-brain

Second-brain is one shared skill package for Claude Code, Codex, and OpenCode. It
ingests source documents into an Obsidian wiki, answers grounded questions, and
maintains wiki health.

## Step 0: Validate prerequisites

Before proceeding, check each requirement. Stop and help the user fix any that fail.

1. **Obsidian** (optional) - the wiki renders in Obsidian. It is not required for ingest, compile, ask, or lint.

2. **Slack MCP tools** (optional) - needed for Slack query ingestion (`slack-queries.yaml`). Verify `slack_search_public_and_private` is callable. If not available, Slack ingestion will be skipped.

3. **Document exports** (optional) - needed only for documents from platforms with no built-in fetcher. Export them as markdown or PDF into `raw/extras/`, or use a fetch tool your runtime already provides.

4. **`curl`** - required for fetching web links:
   ```bash
   which curl
   ```

5. **`git`** - required for `raw/pull-all.sh`:
   ```bash
   which git
   ```

6. **Node** (optional) - required only for the OpenCode adapter source test.

## Claude Code

```bash
claude plugin marketplace add OWNER/REPO
claude plugin install second-brain@second-brain-marketplace
```

`OWNER/REPO` is the GitHub repository that contains this checkout's
`.claude-plugin/marketplace.json`. Claude Code also accepts a local clone path
in place of `OWNER/REPO`.

Claude Code exposes `/second-brain`, `/second-brain-setup`, and
`/second-brain-doctor` as skill shorthand.

Enable the built-in `agents-md@builtin` plugin through `/plugin`. In `/config`, keep
**Project instructions** at its default, `claude-md-or-agents-md`, for repositories
that use only `AGENTS.md`.

The default loads `AGENTS.md` only when the project has no `CLAUDE.md`,
`.claude/CLAUDE.md`, or `CLAUDE.local.md` from the project root through the working
directory. If those files must coexist during a migration, select
`claude-md-and-agents-md` in `/config`. Claude Code reads this plugin option from
user settings (`~/.claude/settings.json`), `--settings`, or managed settings. It does
not read the option from a project's `.claude/settings.json`.

As a transition, replace independent project instructions in `CLAUDE.md` with this
compatibility wrapper after you move the full content to `AGENTS.md`:

```markdown
@AGENTS.md

```

The default mode loads this wrapper, which imports the canonical file. Use
`claude-md-and-agents-md` only when `CLAUDE.md` still contains independent
instructions.

## Codex

The native Codex manifest loads the same `skills/` tree:

```bash
codex plugin marketplace add OWNER/REPO
codex plugin add second-brain@second-brain-marketplace
codex plugin list --json
```

Codex reads `.agents/plugins/marketplace.json` from the same repository root.

Ask Codex to use `second-brain` or `second-brain-setup` with the needed command.
Use `second-brain-doctor` to diagnose an existing repository before migration.

## OpenCode

OpenCode loads local plugin files from `~/.config/opencode/plugins/` or the project
`.opencode/plugins/` directory. Link the adapter from a persistent checkout:

```bash
mkdir -p ~/.config/opencode/plugins
ln -s /path/to/second-brain/opencode/second-brain.js \
  ~/.config/opencode/plugins/second-brain.js
```

The adapter adds the absolute shared `skills/` path and the activation instruction.
It preserves unrelated OpenCode configuration and uses no npm package. Start a new
session and verify it:

```bash
opencode debug config
node --test /path/to/second-brain/opencode/test-second-brain.mjs
```

## Initialize a wiki project (optional)

If the user wants to start a new wiki project, run the setup skill in the target directory:

```
/second-brain-setup
```

This creates the directory structure, starter files, and a bounded section in the
brain's `AGENTS.md`. It preserves unrelated instructions. It is
idempotent. In a multi-brain repository, supply the brain path, for example
`/second-brain-setup team-a/project-x`. Setup uses the sole discovered brain automatically
and asks for a target when several exist.

For an existing repository with `CLAUDE.md`, run `second-brain-doctor`. It reports
conflicts and blockers before it proposes changes. It requires explicit consent
before it moves canonical content or replaces `CLAUDE.md` with the transition
wrapper.

## Configure Obsidian (optional)

If the user uses Obsidian:

1. Change to the project root.
2. Run `/second-brain obsidian`.
3. In a multi-brain repository, omit the brain to open the generated hub or supply a
   name such as `/second-brain obsidian team-a/project-x`.

The workflow opens the project directory as one vault. It preserves existing
portable settings and uses only Obsidian core plugins. Shared graph settings live in
`config/obsidian/graph.json`. Device and session state stays ignored under
`.obsidian/`.

## Verify

Start a new session in the wiki project directory and invoke `second-brain ingest`.
Claude Code shorthand is:

```
/second-brain ingest
```

For a single brain, the skill should read `raw/links.yaml`, process sources in
`raw/`, and begin building the wiki. For several brains, supply the brain name.

## Cleanup

If you cloned to a temp directory in step 1:

```bash
rm -rf "$TMPDIR"
```
