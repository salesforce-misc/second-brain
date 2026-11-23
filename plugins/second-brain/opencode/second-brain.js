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
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

function pluginSkillsPath(moduleUrl = import.meta.url) {
  return resolve(dirname(fileURLToPath(moduleUrl)), "..", "skills")
}

function pluginInstructionsPath(moduleUrl = import.meta.url) {
  return resolve(dirname(fileURLToPath(moduleUrl)), "instructions.md")
}

function addPluginSkillsPath(cfg, moduleUrl = import.meta.url) {
  const skillsPath = pluginSkillsPath(moduleUrl)
  const skills = cfg.skills && typeof cfg.skills === "object" && !Array.isArray(cfg.skills) ? cfg.skills : {}
  const paths = Array.isArray(skills.paths) ? skills.paths : []

  cfg.skills = {
    ...skills,
    paths: paths.includes(skillsPath) ? paths : [...paths, skillsPath],
  }
  return skillsPath
}

function addPluginInstructionsPath(cfg, moduleUrl = import.meta.url) {
  const instructionsPath = pluginInstructionsPath(moduleUrl)
  const instructions = Array.isArray(cfg.instructions) ? cfg.instructions : []

  cfg.instructions = instructions.includes(instructionsPath)
    ? instructions
    : [...instructions, instructionsPath]
  return instructionsPath
}

export default async () => ({
  config(cfg) {
    addPluginSkillsPath(cfg)
    addPluginInstructionsPath(cfg)
  },
})
