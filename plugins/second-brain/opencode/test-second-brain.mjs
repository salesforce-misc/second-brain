/*
 * Copyright (c) 2026, Salesforce, Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"
import * as plugin from "./second-brain.js"

const skillsPath = resolve(dirname(fileURLToPath(import.meta.url)), "..", "skills")
const instructionsPath = resolve(dirname(fileURLToPath(import.meta.url)), "instructions.md")
const doctorSkillPath = resolve(skillsPath, "second-brain-doctor", "SKILL.md")
const input = {
  client: {},
  project: {},
  directory: "/tmp",
  worktree: "/tmp",
  serverUrl: new URL("http://localhost"),
  $: () => {},
}

test("preserves configuration and adds each plugin path once", async () => {
  assert.deepEqual(Object.keys(plugin), ["default"])
  const adapter = await plugin.default(input)
  const cfg = {
    skills: { paths: ["/other/skills"], urls: ["https://example.test/skills"] },
    instructions: ["AGENTS.md"],
    unrelated: true,
  }

  adapter.config(cfg)
  adapter.config(cfg)

  assert.deepEqual(cfg, {
    skills: {
      paths: ["/other/skills", skillsPath],
      urls: ["https://example.test/skills"],
    },
    instructions: ["AGENTS.md", instructionsPath],
    unrelated: true,
  })
})

test("ships the shared skills and activation instruction", () => {
  assert.ok(existsSync(skillsPath))
  assert.ok(existsSync(instructionsPath))
  assert.ok(existsSync(doctorSkillPath))
  assert.equal(
    readFileSync(instructionsPath, "utf8"),
    "Use `second-brain` to operate an Obsidian knowledge base. Use `second-brain-setup` to bootstrap or update one brain. Use `second-brain-doctor` to diagnose or migrate project instructions to AGENTS.md.\n",
  )
})

test("normalizes malformed configuration without losing unrelated keys", async () => {
  const adapter = await plugin.default(input)
  const cfg = {
    skills: { paths: "invalid", extra: true },
    instructions: "AGENTS.md",
    unrelated: true,
  }

  adapter.config(cfg)

  assert.deepEqual(cfg, {
    skills: { paths: [skillsPath], extra: true },
    instructions: [instructionsPath],
    unrelated: true,
  })
})
