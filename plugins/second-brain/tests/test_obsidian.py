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
"""Tests for the second-brain Obsidian helper."""

from contextlib import redirect_stderr
import importlib.util
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "obsidian.py"
SPEC = importlib.util.spec_from_file_location("second_brain_obsidian", SCRIPT)
obsidian = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(obsidian)


class ObsidianTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="second-brain-obsidian-")).resolve()

    def tearDown(self):
        shutil.rmtree(self.project)

    def make_brain(self, relative: str) -> None:
        path = self.project / relative / "wiki" / "index.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"# {relative or 'root'}\n")

    def test_single_root_brain_preserves_existing_portable_settings(self):
        self.make_brain("")
        settings = self.project / ".obsidian" / "app.json"
        settings.parent.mkdir()
        settings.write_text('{"user-setting": true}\n')

        target = obsidian.prepare(self.project, None, False)

        self.assertEqual(target, self.project / "wiki" / "index.md")
        self.assertEqual(json.loads(settings.read_text()), {"user-setting": True})
        graph = json.loads((self.project / "config/obsidian/graph.json").read_text())
        self.assertEqual(
            [group["query"] for group in graph["colorGroups"]],
            ["path:wiki", "path:raw", "path:output"],
        )
        self.assertTrue((self.project / ".obsidian/core-plugins.json").is_file())

    def test_multiple_nested_brains_open_generated_hub(self):
        self.make_brain("brains/drb")
        self.make_brain("brains/team-a/project-x")

        target = obsidian.prepare(self.project, None, False)

        self.assertEqual(target, self.project / "brains" / "index.md")
        hub = target.read_text()
        self.assertIn("[[brains/drb/wiki/index|drb]]", hub)
        self.assertIn("[[brains/team-a/project-x/wiki/index|team-a/project-x]]", hub)
        runtime = self.project / ".obsidian/graph.json"
        self.assertEqual(runtime.read_text(), (self.project / "config/obsidian/graph.json").read_text())
        self.assertIn(".obsidian/workspace.json", (self.project / ".gitignore").read_text())

    def test_selected_brain_and_graph_merge_preserve_user_values(self):
        self.make_brain("brains/a/shared")
        self.make_brain("brains/b/shared")
        graph = self.project / "config/obsidian/graph.json"
        graph.parent.mkdir(parents=True)
        graph.write_text(json.dumps({"showTags": True, "colorGroups": [{"query": "tag:#keep"}]}))

        target = obsidian.prepare(self.project, "brains/a/shared", False)

        self.assertEqual(target, self.project / "brains/a/shared/wiki/index.md")
        merged = json.loads(graph.read_text())
        self.assertTrue(merged["showTags"])
        self.assertEqual(merged["colorGroups"][0], {"query": "tag:#keep"})
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            obsidian.select_brain(self.project, obsidian.discover_brains(self.project), "shared")

    def test_existing_runtime_graph_seeds_canonical_config(self):
        self.make_brain("")
        runtime = self.project / ".obsidian/graph.json"
        runtime.parent.mkdir()
        runtime.write_text(
            json.dumps({"showTags": True, "colorGroups": [{"query": "tag:#keep"}]})
        )

        obsidian.prepare(self.project, None, False)

        canonical = json.loads((self.project / "config/obsidian/graph.json").read_text())
        self.assertTrue(canonical["showTags"])
        self.assertEqual(canonical["colorGroups"][0], {"query": "tag:#keep"})
        self.assertEqual(json.loads(runtime.read_text()), canonical)

    def test_discovery_excludes_template_path_segments(self):
        self.make_brain("brains/real")
        self.make_brain("brains/_template")
        self.make_brain("brains/team/_template/example")

        brains = obsidian.discover_brains(self.project)

        self.assertEqual([obsidian.brain_name(self.project, brain) for brain in brains], ["real"])

    def test_hub_update_preserves_user_content(self):
        self.make_brain("brains/one")
        self.make_brain("brains/two")
        hub = self.project / "brains/index.md"
        hub.write_text("User notes.\n")
        obsidian.prepare(self.project, None, False)
        self.make_brain("brains/three")

        obsidian.prepare(self.project, None, False)

        content = hub.read_text()
        self.assertTrue(content.startswith("User notes."))
        self.assertEqual(content.count(obsidian.HUB_START), 1)
        self.assertIn("[[brains/three/wiki/index|three]]", content)

    def test_enabled_open_uses_encoded_obsidian_url(self):
        self.make_brain("brains/team one")

        with mock.patch.object(obsidian.sys, "platform", "darwin"), mock.patch.object(
            obsidian.subprocess, "run"
        ) as run:
            target = obsidian.prepare(self.project, "team one", True)

        expected_url = "obsidian://open?path=" + str(target).replace(" ", "%20")
        run.assert_called_once_with(["open", expected_url], check=True)

    def test_open_uses_each_platform_launcher(self):
        path = Path("/tmp/Vault Note.md")
        url = "obsidian://open?path=/tmp/Vault%20Note.md"
        cases = [
            ("darwin", "posix", ["open", url]),
            ("linux", "posix", ["xdg-open", url]),
            ("win32", "nt", ["cmd", "/c", "start", "", url]),
        ]

        for platform, os_name, command in cases:
            with self.subTest(platform=platform), mock.patch.object(
                obsidian.sys, "platform", platform
            ), mock.patch.object(obsidian.os, "name", os_name), mock.patch.object(
                obsidian.subprocess, "run"
            ) as run:
                obsidian.open_in_obsidian(path)
                run.assert_called_once_with(command, check=True)

    def test_main_reports_launcher_failure(self):
        self.make_brain("")
        error = subprocess.CalledProcessError(1, ["open"])
        stderr = StringIO()

        with mock.patch.object(
            obsidian.sys, "argv", ["obsidian.py", "--project", str(self.project)]
        ), mock.patch.object(obsidian, "open_in_obsidian", side_effect=error), redirect_stderr(
            stderr
        ), self.assertRaises(SystemExit) as raised:
            obsidian.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("returned non-zero exit status 1", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
