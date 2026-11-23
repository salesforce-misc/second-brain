#!/usr/bin/env python3
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
"""Assertion checker for the wiki-ingest test runner.

Validates that the skill produced correct wiki structure, frontmatter,
backlinks, and output format after running ingest and ask scenarios.

Usage:
    python3 checks.py <wiki_project_dir>
"""

import os
import re
import sys
import glob as globmod

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Results tracker
# ---------------------------------------------------------------------------


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def ok(self, name, msg=""):
        self.passed += 1
        self.details.append(("PASS", name, msg))

    def fail(self, name, msg):
        self.failed += 1
        self.details.append(("FAIL", name, msg))

    def warn(self, name, msg):
        self.warnings += 1
        self.details.append(("WARN", name, msg))

    def report(self):
        print(f"\n{BOLD}{'=' * 60}")
        print(f"  wiki-ingest Test Results")
        print(f"{'=' * 60}{RESET}\n")

        for status, name, msg in self.details:
            if status == "PASS":
                icon = f"{GREEN}PASS{RESET}"
            elif status == "FAIL":
                icon = f"{RED}FAIL{RESET}"
            else:
                icon = f"{YELLOW}WARN{RESET}"
            line = f"  {icon}  {name}"
            if msg:
                line += f"\n         {msg}"
            print(line)

        print(f"\n{BOLD}Summary:{RESET} {GREEN}{self.passed} passed{RESET}, ", end="")
        print(f"{RED}{self.failed} failed{RESET}, ", end="")
        print(f"{YELLOW}{self.warnings} warnings{RESET}")
        print()
        return self.failed == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_file(path):
    """Read a file and return its content, or None if it doesn't exist."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None


def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content.

    Returns the frontmatter string (without delimiters) and the body.
    """
    if not content or not content.startswith("---"):
        return None, content or ""
    end = content.find("---", 3)
    if end == -1:
        return None, content
    fm = content[3:end].strip()
    body = content[end + 3:].strip()
    return fm, body


def find_files(directory, pattern="*.md"):
    """Recursively find files matching a glob pattern."""
    return globmod.glob(os.path.join(directory, "**", pattern), recursive=True)


# ---------------------------------------------------------------------------
# Structure checks
# ---------------------------------------------------------------------------


def check_wiki_directory_structure(project_dir, results):
    """Wiki directory structure exists with required subdirectories."""
    wiki_dir = os.path.join(project_dir, "wiki")
    if not os.path.isdir(wiki_dir):
        results.fail("wiki/ directory exists", f"Not found: {wiki_dir}")
        return

    results.ok("wiki/ directory exists")

    for subdir in ["sources", "concepts"]:
        path = os.path.join(wiki_dir, subdir)
        if os.path.isdir(path):
            results.ok(f"wiki/{subdir}/ exists")
        else:
            results.fail(f"wiki/{subdir}/ exists", f"Not found: {path}")


def check_index_exists(project_dir, results):
    """wiki/index.md exists and is non-empty."""
    index_path = os.path.join(project_dir, "wiki", "index.md")
    content = read_file(index_path)
    if content is None:
        results.fail("wiki/index.md exists", "File not found")
        return
    if len(content.strip()) < 10:
        results.fail("wiki/index.md has content", f"File is nearly empty ({len(content)} chars)")
        return
    results.ok("wiki/index.md exists and has content")


def check_connections_exists(project_dir, results):
    """wiki/connections.md exists."""
    path = os.path.join(project_dir, "wiki", "connections.md")
    if os.path.exists(path):
        results.ok("wiki/connections.md exists")
    else:
        results.warn("wiki/connections.md exists", "Not created — may be fine if no cross-cutting themes found")


# ---------------------------------------------------------------------------
# Ingest checks
# ---------------------------------------------------------------------------


def check_source_summaries(project_dir, results):
    """At least one source summary was created in wiki/sources/."""
    sources_dir = os.path.join(project_dir, "wiki", "sources")
    if not os.path.isdir(sources_dir):
        results.fail("source summaries created", "wiki/sources/ directory missing")
        return

    sources = find_files(sources_dir, "*.md")
    if not sources:
        results.fail("source summaries created", "No .md files found in wiki/sources/")
        return

    results.ok("source summaries created", f"Found {len(sources)} source(s)")

    # Check that source summaries are brief (1-2 paragraphs as per rules)
    for src in sources:
        content = read_file(src)
        if content and len(content) > 5000:
            name = os.path.basename(src)
            results.warn(f"source summary brevity: {name}", f"{len(content)} chars — rule says 1-2 paragraphs")


def check_concept_articles(project_dir, results):
    """At least one concept article was created in wiki/concepts/."""
    concepts_dir = os.path.join(project_dir, "wiki", "concepts")
    if not os.path.isdir(concepts_dir):
        results.fail("concept articles created", "wiki/concepts/ directory missing")
        return

    concepts = find_files(concepts_dir, "*.md")
    if not concepts:
        results.fail("concept articles created", "No .md files found in wiki/concepts/")
        return

    results.ok("concept articles created", f"Found {len(concepts)} concept(s)")


def check_index_has_entries(project_dir, results):
    """wiki/index.md contains links to source summaries and concept articles."""
    index_path = os.path.join(project_dir, "wiki", "index.md")
    content = read_file(index_path)
    if not content:
        results.fail("index has entries", "wiki/index.md missing or empty")
        return

    # Check for links (either markdown links or wiki links)
    has_links = bool(
        re.search(r"\[.*?\]\(.*?\)", content) or  # markdown links
        re.search(r"\[\[.*?\]\]", content)          # wiki links
    )
    if has_links:
        results.ok("index has entries with links")
    else:
        results.fail("index has entries with links", "No markdown or wiki links found in index.md")


def check_backlinks(project_dir, results):
    """Concept articles contain backlinks to sources (or vice versa)."""
    concepts_dir = os.path.join(project_dir, "wiki", "concepts")
    concepts = find_files(concepts_dir, "*.md") if os.path.isdir(concepts_dir) else []

    if not concepts:
        results.warn("backlinks present", "No concept articles to check")
        return

    has_backlinks = False
    for concept_path in concepts:
        content = read_file(concept_path)
        if not content:
            continue
        # Look for links to sources or other concepts
        if re.search(r"\[\[.*?\]\]", content) or re.search(r"\[.*?\]\(.*?sources/.*?\)", content):
            has_backlinks = True
            break

    if has_backlinks:
        results.ok("backlinks present in concept articles")
    else:
        results.fail("backlinks present in concept articles", "No links to sources or other concepts found")


def check_concept_has_visual(project_dir, results):
    """Concept articles contain at least one visual element (diagram or callout)."""
    concepts_dir = os.path.join(project_dir, "wiki", "concepts")
    concepts = find_files(concepts_dir, "*.md") if os.path.isdir(concepts_dir) else []

    if not concepts:
        results.warn("concept visual elements", "No concept articles to check")
        return

    for concept_path in concepts:
        content = read_file(concept_path)
        if not content:
            continue
        name = os.path.basename(concept_path)
        has_mermaid = "```mermaid" in content
        has_callout = re.search(r">\s*\[!(?:note|info|tip|warning|danger|abstract|question|bug|example)", content)
        has_table = re.search(r"\|.*\|.*\|", content)

        if has_mermaid or has_callout or has_table:
            results.ok(f"visual element in {name}")
        else:
            results.fail(f"visual element in {name}", "No Mermaid diagram, callout, or table found")


def check_diagram_style(project_dir, results):
    """Mermaid diagrams follow Dracula theme rules (no fill: styles)."""
    all_md = find_files(os.path.join(project_dir, "wiki"), "*.md")
    all_md += find_files(os.path.join(project_dir, "output"), "*.md") if os.path.isdir(os.path.join(project_dir, "output")) else []

    checked = 0
    for md_path in all_md:
        content = read_file(md_path)
        if not content or "```mermaid" not in content:
            continue

        checked += 1
        name = os.path.relpath(md_path, project_dir)

        # Extract mermaid blocks
        blocks = re.findall(r"```mermaid\s*\n(.*?)```", content, re.DOTALL)
        for i, block in enumerate(blocks):
            if re.search(r"\bfill:", block):
                results.fail(
                    f"diagram style: {name} block {i + 1}",
                    "Contains 'fill:' — Dracula theme rule says no fill styles"
                )
            else:
                results.ok(f"diagram style: {name} block {i + 1} — no fill")

    if checked == 0:
        results.warn("diagram style check", "No Mermaid diagrams found to check")


# ---------------------------------------------------------------------------
# Output (Q&A) checks
# ---------------------------------------------------------------------------


def check_output_exists(project_dir, results):
    """output/ directory exists with at least one file."""
    output_dir = os.path.join(project_dir, "output")
    if not os.path.isdir(output_dir):
        results.warn("output/ directory exists", "Not found — Q&A scenario may not have run")
        return False

    outputs = find_files(output_dir, "*.md")
    if not outputs:
        results.warn("output files exist", "No .md files in output/")
        return False

    results.ok("output files exist", f"Found {len(outputs)} output(s)")
    return True


def check_output_frontmatter(project_dir, results):
    """Output files have required YAML frontmatter fields."""
    output_dir = os.path.join(project_dir, "output")
    if not os.path.isdir(output_dir):
        return

    outputs = find_files(output_dir, "*.md")
    required_fields = ["questions", "date", "labels", "sources"]

    for output_path in outputs:
        content = read_file(output_path)
        if not content:
            continue

        name = os.path.basename(output_path)
        fm, _ = parse_frontmatter(content)

        if fm is None:
            results.fail(f"output frontmatter: {name}", "No YAML frontmatter found (must start with ---)")
            continue

        results.ok(f"output frontmatter exists: {name}")

        for field in required_fields:
            if re.search(rf"^{field}:", fm, re.MULTILINE):
                results.ok(f"output field '{field}': {name}")
            else:
                results.fail(f"output field '{field}': {name}", f"Missing required field '{field}' in frontmatter")


def check_output_required_elements(project_dir, results):
    """Output files contain TL;DR callout, Mermaid diagram, and references section."""
    output_dir = os.path.join(project_dir, "output")
    if not os.path.isdir(output_dir):
        return

    outputs = find_files(output_dir, "*.md")

    for output_path in outputs:
        content = read_file(output_path)
        if not content:
            continue

        name = os.path.basename(output_path)
        _, body = parse_frontmatter(content)

        # TL;DR callout
        if re.search(r">\s*\[!abstract\]", body) or re.search(r">\s*\[!tldr\]", body, re.IGNORECASE):
            results.ok(f"output TL;DR callout: {name}")
        else:
            results.fail(f"output TL;DR callout: {name}", "Missing > [!abstract] TL;DR callout at top")

        # Mermaid diagram
        if "```mermaid" in body:
            results.ok(f"output Mermaid diagram: {name}")
        else:
            results.fail(f"output Mermaid diagram: {name}", "Missing Mermaid diagram (required in every output)")

        # References section
        if re.search(r"##?\s*[Rr]eferences?", body):
            results.ok(f"output references section: {name}")
        else:
            results.fail(f"output references section: {name}", "Missing References section at bottom")


# ---------------------------------------------------------------------------
# Link collection check
# ---------------------------------------------------------------------------


def check_links_collected(project_dir, results):
    """raw/links.yaml was updated with discovered links from source documents."""
    links_path = os.path.join(project_dir, "raw", "links.yaml")
    content = read_file(links_path)
    if not content:
        results.warn("links collected", "raw/links.yaml missing or empty")
        return

    # The sample doc has wiki and dashboard URLs that should be collected
    if "url:" in content or "- url" in content:
        results.ok("links collected in raw/links.yaml")
    else:
        results.warn("links collected", "No 'url:' entries found — source doc has URLs that should be collected")


# ---------------------------------------------------------------------------
# People / ownership check
# ---------------------------------------------------------------------------


def check_ownership_recorded(project_dir, results):
    """At least one article records team/owner information."""
    all_md = find_files(os.path.join(project_dir, "wiki"), "*.md")

    for md_path in all_md:
        content = read_file(md_path)
        if not content:
            continue
        # Look for ownership indicators
        if re.search(r"(?i)(owner|team|tech lead|oncall|stakeholder)", content):
            name = os.path.relpath(md_path, project_dir)
            results.ok("ownership recorded", f"Found in {name}")
            return

    results.warn("ownership recorded", "No ownership/team information found in any wiki article")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wiki_project_dir>")
        sys.exit(1)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"{RED}Directory not found: {project_dir}{RESET}")
        sys.exit(1)

    print(f"Checking wiki project at: {project_dir}\n")

    results = Results()

    # Structure
    check_wiki_directory_structure(project_dir, results)
    check_index_exists(project_dir, results)
    check_connections_exists(project_dir, results)

    # Ingest
    check_source_summaries(project_dir, results)
    check_concept_articles(project_dir, results)
    check_index_has_entries(project_dir, results)
    check_backlinks(project_dir, results)
    check_concept_has_visual(project_dir, results)
    check_diagram_style(project_dir, results)
    check_links_collected(project_dir, results)
    check_ownership_recorded(project_dir, results)

    # Output (Q&A)
    has_output = check_output_exists(project_dir, results)
    if has_output:
        check_output_frontmatter(project_dir, results)
        check_output_required_elements(project_dir, results)

    success = results.report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
