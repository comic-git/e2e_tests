<!-- Audience: AI agents and human developers.
     Purpose: Describe the harness structure, data flow, and design rationale.
     Read this first before changing test case layout or runner behavior. -->

# Architecture

## Overview

`e2e_tests` is a local end-to-end harness for `comic_git_engine`.

The harness validates real engine behavior by staging complete fixture inputs into a temporary host repo, running the real engine entry point, and comparing the produced `build/` tree against checked-in golden output.

This repo is not intended to be a normal `comic_git` host repo. Checked-in fixture inputs live under `test_cases/`, and root-level `your_content/` is ignored so local manual runs are not committed accidentally.

## Components

| Component           | Location                                      | Responsibility                                                                                 |
|---------------------|-----------------------------------------------|------------------------------------------------------------------------------------------------|
| Runner              | [`scripts/run_e2e.py`](../scripts/run_e2e.py) | Creates temp host workspaces, stages fixtures, runs the engine, refreshes or compares goldens. |
| Test cases          | [`test_cases/`](../test_cases/)               | Complete independent fixture inputs and per-case metadata.                                     |
| Case manifest       | `test_cases/<case>/manifest.toml`             | Machine-readable inputs: case name, mode flags, tags, and environment variables.               |
| Case documentation  | `test_cases/<case>/TEST_CASE.md`              | Human-readable intent, coverage, and expected behavior. Not parsed by the runner.              |
| Golden builds       | [`golden_builds/`](../golden_builds/)         | Expected full `build/` output, grouped by test case.                                           |
| Future TOML goldens | `golden_toml/`                                | Expected migration output once legacy-to-TOML migration exists.                                |
| Local engine link   | `comic_git_engine/`                           | Local symlink or junction to the engine repo under test.                                       |

## Test Case Model

Each test case is independent and explicit.

```text
test_cases/
  baseline/
    manifest.toml
    TEST_CASE.md
    your_content/
```

The source of truth for behavior is:

- `manifest.toml`
- `your_content/`
- the matching `golden_*` output

`TEST_CASE.md` explains the case for humans. It should summarize what the fixture is intended to cover, but it must not be treated as executable configuration or parsed by the runner.

## Manifest Contract

Manifests should list all behavior-relevant inputs explicitly.

```toml
name = "baseline"
description = "Full legacy build parity coverage for the baseline realistic fixture."
tags = ["legacy-build", "baseline", "github-pages-inference", "full-parity"]

[modes]
legacy_build = true
migration = false
toml_build = false

[env]
GITHUB_REPOSITORY = "comic-git/e2e_tests"
```

The runner currently requires:

- `name`
- `[modes].legacy_build`
- `[modes].migration`
- `[modes].toml_build`
- `[env].GITHUB_REPOSITORY`

The runner warns if `TEST_CASE.md` is missing, but the warning does not fail the test.

## Data Flow

Legacy build validation follows this flow:

1. Load `test_cases/<case>/manifest.toml`.
2. Warn if `test_cases/<case>/TEST_CASE.md` is missing.
3. Create a temporary workspace.
4. Copy `test_cases/<case>/your_content/` into the temp workspace as root `your_content/`.
5. Create a local `comic_git_engine/` junction in the temp workspace.
6. Run `comic_git_engine/src/build/build_site.py` from the temp workspace root.
7. Compare the produced `build/` tree against `golden_builds/<case>/` byte-for-byte.

Refresh follows the same build flow, then fully wipes and rewrites `golden_builds/<case>/`.

## Design Decisions

### Minimal temp host repo

The temp workspace contains only the selected fixture input and the engine link. It does not copy the harness repo skeleton.

This keeps the test boundary clear: the engine can only observe the files that a real host repo would provide.

### Full goldens per test case

The harness compares full build output for each case. Focused tests should stay focused by using small fixture inputs, not by weakening comparison scope.

This makes refresh behavior simple: `refresh-build` always rewrites the complete golden output for the selected case.

### Explicit inputs over defaults

Environment variables and enabled modes are explicit in each manifest. Duplicate data across cases is acceptable because it makes test behavior reviewable and avoids hidden fallback behavior.

### Independent fixtures over inheritance

Test cases do not inherit from baseline. This avoids setup complexity and accidental coupling. If duplicated fixture data becomes painful later, revisit this decision with a concrete maintenance problem.

## Platform Scope

The current runner is local-first and Windows-oriented. It creates the engine link with `cmd /c mklink /J`.

Linux and CI support are roadmap work. When added, platform-specific engine linking should be isolated behind a small helper rather than spread through runner commands.
