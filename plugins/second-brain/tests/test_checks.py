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
"""Unit tests for checks.py.

Tests the validation logic against synthetic wiki structures without
needing to run the full claude -p integration runner.

Usage:
    python3 -m pytest test_checks.py -v
    # or
    python3 test_checks.py
"""

import os
import shutil
import tempfile
import unittest

from checks import (
    Results,
    parse_frontmatter,
    check_wiki_directory_structure,
    check_index_exists,
    check_connections_exists,
    check_source_summaries,
    check_concept_articles,
    check_index_has_entries,
    check_backlinks,
    check_concept_has_visual,
    check_diagram_style,
    check_output_exists,
    check_output_frontmatter,
    check_output_required_elements,
    check_links_collected,
    check_ownership_recorded,
)


class TestParseFrontmatter(unittest.TestCase):
    def test_valid_frontmatter(self):
        content = "---\ntitle: Test\ndate: 2026-04-09\n---\nBody here"
        fm, body = parse_frontmatter(content)
        self.assertIn("title: Test", fm)
        self.assertEqual(body, "Body here")

    def test_no_frontmatter(self):
        content = "# Just a heading\nSome text"
        fm, body = parse_frontmatter(content)
        self.assertIsNone(fm)
        self.assertEqual(body, content)

    def test_empty_content(self):
        fm, body = parse_frontmatter("")
        self.assertIsNone(fm)
        self.assertEqual(body, "")

    def test_none_content(self):
        fm, body = parse_frontmatter(None)
        self.assertIsNone(fm)
        self.assertEqual(body, "")


class WikiTestBase(unittest.TestCase):
    """Base class that creates and tears down a temporary wiki project."""

    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="wiki-test-")

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def make_dirs(self, *paths):
        for p in paths:
            os.makedirs(os.path.join(self.project_dir, p), exist_ok=True)

    def write_file(self, rel_path, content):
        full = os.path.join(self.project_dir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)


class TestDirectoryStructure(WikiTestBase):
    def test_missing_wiki_dir(self):
        r = Results()
        check_wiki_directory_structure(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_complete_structure(self):
        self.make_dirs("wiki/sources", "wiki/concepts")
        r = Results()
        check_wiki_directory_structure(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertEqual(r.passed, 3)  # wiki/, sources/, concepts/

    def test_missing_concepts(self):
        self.make_dirs("wiki/sources")
        r = Results()
        check_wiki_directory_structure(self.project_dir, r)
        self.assertEqual(r.failed, 1)  # missing concepts


class TestIndexExists(WikiTestBase):
    def test_missing_index(self):
        self.make_dirs("wiki")
        r = Results()
        check_index_exists(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_empty_index(self):
        self.write_file("wiki/index.md", "")
        r = Results()
        check_index_exists(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_valid_index(self):
        self.write_file("wiki/index.md", "# Wiki Index\n\n- [Concept A](concepts/a.md)")
        r = Results()
        check_index_exists(self.project_dir, r)
        self.assertEqual(r.failed, 0)


class TestConnectionsExists(WikiTestBase):
    def test_missing_connections(self):
        self.make_dirs("wiki")
        r = Results()
        check_connections_exists(self.project_dir, r)
        self.assertEqual(r.warnings, 1)
        self.assertEqual(r.failed, 0)  # warn, not fail

    def test_present_connections(self):
        self.write_file("wiki/connections.md", "# Connections\n\nTheme: cost optimization")
        r = Results()
        check_connections_exists(self.project_dir, r)
        self.assertEqual(r.passed, 1)


class TestSourceSummaries(WikiTestBase):
    def test_no_sources_dir(self):
        r = Results()
        check_source_summaries(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_empty_sources_dir(self):
        self.make_dirs("wiki/sources")
        r = Results()
        check_source_summaries(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_has_source(self):
        self.write_file("wiki/sources/sample-architecture.md", "# Summary\n\nExample Platform is...")
        r = Results()
        check_source_summaries(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertGreater(r.passed, 0)

    def test_verbose_source_warns(self):
        self.write_file("wiki/sources/verbose.md", "x" * 6000)
        r = Results()
        check_source_summaries(self.project_dir, r)
        self.assertGreater(r.warnings, 0)


class TestConceptArticles(WikiTestBase):
    def test_no_concepts_dir(self):
        r = Results()
        check_concept_articles(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_has_concept(self):
        self.write_file("wiki/concepts/example-platform.md", "# Example Platform\n\nA resource management subsystem.")
        r = Results()
        check_concept_articles(self.project_dir, r)
        self.assertEqual(r.failed, 0)


class TestIndexHasEntries(WikiTestBase):
    def test_no_links_in_index(self):
        self.write_file("wiki/index.md", "# Index\n\nNo links here, just text.")
        r = Results()
        check_index_has_entries(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_markdown_links(self):
        self.write_file("wiki/index.md", "# Index\n\n- [Example Platform](concepts/example-platform.md)")
        r = Results()
        check_index_has_entries(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_wiki_links(self):
        self.write_file("wiki/index.md", "# Index\n\n- [[example-platform]] — resource management")
        r = Results()
        check_index_has_entries(self.project_dir, r)
        self.assertEqual(r.failed, 0)


class TestBacklinks(WikiTestBase):
    def test_no_concepts(self):
        r = Results()
        check_backlinks(self.project_dir, r)
        self.assertGreater(r.warnings, 0)

    def test_concept_with_wiki_backlink(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\nSee [[sample-architecture]] for details."
        )
        r = Results()
        check_backlinks(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertGreater(r.passed, 0)

    def test_concept_with_markdown_backlink(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\nSource: [architecture](../sources/sample-architecture.md)"
        )
        r = Results()
        check_backlinks(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_concept_without_backlinks(self):
        self.write_file("wiki/concepts/pm.md", "# PM\n\nJust text, no links.")
        r = Results()
        check_backlinks(self.project_dir, r)
        self.assertGreater(r.failed, 0)


class TestConceptHasVisual(WikiTestBase):
    def test_concept_with_mermaid(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n```mermaid\nflowchart TD\n    A --> B\n```\n"
        )
        r = Results()
        check_concept_has_visual(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_concept_with_callout(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n> [!abstract] TL;DR\n> PM manages resources.\n"
        )
        r = Results()
        check_concept_has_visual(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_concept_with_table(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n| Component | Role |\n|---|---|\n| Core | Control plane |\n"
        )
        r = Results()
        check_concept_has_visual(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_concept_without_visual(self):
        self.write_file("wiki/concepts/pm.md", "# PM\n\nJust prose. No diagrams or callouts.")
        r = Results()
        check_concept_has_visual(self.project_dir, r)
        self.assertGreater(r.failed, 0)


class TestDiagramStyle(WikiTestBase):
    def test_clean_diagram(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n```mermaid\nflowchart TD\n    A[Core] --> B[Workers]\n```\n"
        )
        r = Results()
        check_diagram_style(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertGreater(r.passed, 0)

    def test_diagram_with_fill(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n```mermaid\nflowchart TD\n    A[Core] --> B[Workers]\n    style A fill:#ff0000\n```\n"
        )
        r = Results()
        check_diagram_style(self.project_dir, r)
        self.assertGreater(r.failed, 0)

    def test_no_diagrams(self):
        self.write_file("wiki/concepts/pm.md", "# PM\n\nNo diagrams.")
        r = Results()
        check_diagram_style(self.project_dir, r)
        self.assertGreater(r.warnings, 0)

    def test_output_diagram_also_checked(self):
        self.make_dirs("wiki")
        self.write_file(
            "output/qa.md",
            "---\nquestions:\n  - test\n---\n\n```mermaid\nflowchart TD\n    A --> B\n    style A fill:#bad\n```\n"
        )
        r = Results()
        check_diagram_style(self.project_dir, r)
        self.assertGreater(r.failed, 0)


class TestOutputExists(WikiTestBase):
    def test_no_output_dir(self):
        r = Results()
        result = check_output_exists(self.project_dir, r)
        self.assertFalse(result)

    def test_empty_output_dir(self):
        self.make_dirs("output")
        r = Results()
        result = check_output_exists(self.project_dir, r)
        self.assertFalse(result)

    def test_has_output(self):
        self.write_file("output/answer.md", "---\nquestions:\n  - what?\n---\nAnswer")
        r = Results()
        result = check_output_exists(self.project_dir, r)
        self.assertTrue(result)


class TestOutputFrontmatter(WikiTestBase):
    def test_complete_frontmatter(self):
        self.write_file("output/answer.md", (
            "---\n"
            "questions:\n"
            "  - What is PM?\n"
            "date: 2026-04-09\n"
            "labels:\n"
            "  - architecture\n"
            "sources:\n"
            "  - wiki/concepts/pm.md\n"
            "---\n"
            "Body"
        ))
        r = Results()
        check_output_frontmatter(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        # 1 for exists + 4 for fields
        self.assertEqual(r.passed, 5)

    def test_missing_labels(self):
        self.write_file("output/answer.md", (
            "---\n"
            "questions:\n"
            "  - What?\n"
            "date: 2026-04-09\n"
            "sources:\n"
            "  - wiki/concepts/pm.md\n"
            "---\n"
            "Body"
        ))
        r = Results()
        check_output_frontmatter(self.project_dir, r)
        self.assertEqual(r.failed, 1)  # missing labels

    def test_no_frontmatter(self):
        self.write_file("output/answer.md", "# Answer\n\nJust text.")
        r = Results()
        check_output_frontmatter(self.project_dir, r)
        self.assertGreater(r.failed, 0)


class TestOutputRequiredElements(WikiTestBase):
    def test_complete_output(self):
        self.write_file("output/answer.md", (
            "---\nquestions:\n  - What?\n---\n\n"
            "> [!abstract] TL;DR\n"
            "> PM manages resources.\n\n"
            "```mermaid\nflowchart TD\n    A --> B\n```\n\n"
            "## References\n\n"
            "- [[example-platform]]\n"
        ))
        r = Results()
        check_output_required_elements(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertEqual(r.passed, 3)  # tldr, mermaid, references

    def test_missing_tldr(self):
        self.write_file("output/answer.md", (
            "---\nquestions:\n  - What?\n---\n\n"
            "No callout here.\n\n"
            "```mermaid\nflowchart TD\n    A --> B\n```\n\n"
            "## References\n"
        ))
        r = Results()
        check_output_required_elements(self.project_dir, r)
        self.assertEqual(r.failed, 1)

    def test_missing_mermaid(self):
        self.write_file("output/answer.md", (
            "---\nquestions:\n  - What?\n---\n\n"
            "> [!abstract] TL;DR\n> Summary.\n\n"
            "Just text.\n\n"
            "## References\n"
        ))
        r = Results()
        check_output_required_elements(self.project_dir, r)
        self.assertEqual(r.failed, 1)

    def test_missing_references(self):
        self.write_file("output/answer.md", (
            "---\nquestions:\n  - What?\n---\n\n"
            "> [!abstract] TL;DR\n> Summary.\n\n"
            "```mermaid\nflowchart TD\n    A --> B\n```\n\n"
            "No references section.\n"
        ))
        r = Results()
        check_output_required_elements(self.project_dir, r)
        self.assertEqual(r.failed, 1)


class TestLinksCollected(WikiTestBase):
    def test_links_with_urls(self):
        self.write_file("raw/links.yaml", (
            "- url: https://wiki.example.com/pages/viewpage.action?pageId=789012\n"
            "  type: wiki\n"
            "  page_id: '789012'\n"
            "  found_in: raw/sample-architecture.md\n"
        ))
        r = Results()
        check_links_collected(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertGreater(r.passed, 0)

    def test_empty_links(self):
        self.write_file("raw/links.yaml", "# No links yet\n")
        r = Results()
        check_links_collected(self.project_dir, r)
        self.assertGreater(r.warnings, 0)


class TestOwnershipRecorded(WikiTestBase):
    def test_ownership_in_source(self):
        self.write_file(
            "wiki/sources/sample.md",
            "---\nowner: Jane Doe\nteam: Example Platform\n---\n# Summary"
        )
        r = Results()
        check_ownership_recorded(self.project_dir, r)
        self.assertEqual(r.failed, 0)
        self.assertGreater(r.passed, 0)

    def test_ownership_in_concept(self):
        self.write_file(
            "wiki/concepts/pm.md",
            "# PM\n\n## Ownership\n\n- **Tech Lead**: Jane Doe\n- **Team**: Example Platform"
        )
        r = Results()
        check_ownership_recorded(self.project_dir, r)
        self.assertEqual(r.failed, 0)

    def test_no_ownership(self):
        self.write_file("wiki/concepts/pm.md", "# PM\n\nJust technical content.")
        r = Results()
        check_ownership_recorded(self.project_dir, r)
        self.assertGreater(r.warnings, 0)


class TestResultsReport(unittest.TestCase):
    def test_all_pass(self):
        r = Results()
        r.ok("test1")
        r.ok("test2")
        self.assertTrue(r.report())

    def test_failure_returns_false(self):
        r = Results()
        r.ok("test1")
        r.fail("test2", "broke")
        self.assertFalse(r.report())

    def test_warnings_still_pass(self):
        r = Results()
        r.ok("test1")
        r.warn("test2", "maybe")
        self.assertTrue(r.report())


if __name__ == "__main__":
    unittest.main()
