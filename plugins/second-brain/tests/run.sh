#!/bin/bash
# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -euo pipefail

# ---------------------------------------------------------------------------
# second-brain skill test runner
#
# Creates a temporary wiki project from fixtures, runs ingest and ask
# scenarios through `claude -p`, then checks the resulting wiki structure
# for correctness.
#
# Usage:
#   ./run.sh              # run all scenarios
#   ./run.sh --check-only <dir>  # skip scenarios, just check an existing dir
# ---------------------------------------------------------------------------

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$TESTS_DIR")"
FIXTURES_DIR="$TESTS_DIR/fixtures"
CHECK_SCRIPT="$TESTS_DIR/checks.py"

# Temp project directory — cleaned up on exit unless --keep
WORK_DIR=""
KEEP=false

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[96m"
RESET="\033[0m"

info()  { echo -e "${CYAN}▸${RESET} $*"; }
step()  { echo -e "\n${BOLD}=== $* ===${RESET}"; }

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
CHECK_ONLY=false
CHECK_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check-only)
            CHECK_ONLY=true
            if [[ -n "${2:-}" && ! "$2" =~ ^-- ]]; then
                CHECK_DIR="$2"
                shift
            fi
            shift
            ;;
        --keep)
            KEEP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--check-only <dir>] [--keep]"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Setup / teardown
# ---------------------------------------------------------------------------

cleanup() {
    if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
        if $KEEP; then
            step "Keeping work directory"
            info "$WORK_DIR"
        else
            step "Cleanup"
            rm -rf "$WORK_DIR"
            info "Removed $WORK_DIR"
        fi
    fi
}

trap cleanup EXIT

setup() {
    step "Setup"

    WORK_DIR="$(mktemp -d /tmp/second-brain-test.XXXXXX)"
    info "Work directory: $WORK_DIR"

    # Copy fixtures
    cp -r "$FIXTURES_DIR/raw" "$WORK_DIR/raw"
    mkdir -p "$WORK_DIR/wiki/sources" "$WORK_DIR/wiki/concepts" "$WORK_DIR/output"

    # Create minimal index.md so the skill can find and update it
    cat > "$WORK_DIR/wiki/index.md" << 'EOF'
# Wiki Index

*Master index of all articles.*
EOF

    info "Fixtures installed"
    info "Ready"
}

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

run_scenario() {
    local name="$1"
    local prompt="$2"

    step "Scenario: $name"
    echo -e "${DIM}Prompt: ${prompt:0:120}...${RESET}"

    if claude -p "$prompt" \
        --dangerously-skip-permissions \
        --verbose 2>&1 | tail -10; then
        info "Scenario completed"
    else
        info "Scenario exited with non-zero (may be ok)"
    fi
    echo ""
}

run_scenarios() {
    run_scenario "Ingest raw documents" \
        "Use the /second-brain skill. The wiki project directory is $WORK_DIR. Run the ingest workflow: read the documents in $WORK_DIR/raw/, create source summaries in $WORK_DIR/wiki/sources/, identify concepts and create concept articles in $WORK_DIR/wiki/concepts/, add backlinks between sources and concepts, update $WORK_DIR/wiki/index.md with new entries, create $WORK_DIR/wiki/connections.md if cross-cutting themes emerge, and collect any URLs found in source documents into $WORK_DIR/raw/links.yaml. Every concept article must have at least one Mermaid diagram or visual callout. Follow Dracula theme diagram rules (no fill: styles)."

    run_scenario "Ask a question" \
        "Use the /second-brain skill. The wiki project directory is $WORK_DIR. Answer this question against the wiki: 'What is Example Platform and how does it handle cost attribution?' Save the answer as a markdown file in $WORK_DIR/output/. The output MUST have YAML frontmatter with questions, date, labels, and sources fields. The body MUST contain a > [!abstract] TL;DR callout at the top, at least one Mermaid diagram, and a References section at the bottom. Follow Dracula theme diagram rules (no fill: styles)."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if $CHECK_ONLY; then
    step "Check-only mode"
    if [[ -z "$CHECK_DIR" ]]; then
        echo "Usage: $0 --check-only <wiki_project_dir>"
        exit 1
    fi
    if [[ ! -d "$CHECK_DIR" ]]; then
        echo "Directory not found: $CHECK_DIR"
        exit 1
    fi
    python3 "$CHECK_SCRIPT" "$CHECK_DIR"
    exit $?
fi

setup
run_scenarios

step "Checking results"
python3 "$CHECK_SCRIPT" "$WORK_DIR"
