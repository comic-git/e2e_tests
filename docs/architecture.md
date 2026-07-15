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
| Case manifest       | `test_cases/<case>/manifest.toml`             | Machine-readable inputs: case name, source format, check flags, tags, and environment variables. |
| Case documentation  | `test_cases/<case>/TEST_CASE.md`              | Human-readable intent, coverage, and expected behavior. Not parsed by the runner.              |
| Golden builds       | [`golden_builds/`](../golden_builds/)         | Expected full `build/` output, grouped by test case.                                           |
| TOML goldens        | `golden_toml/`                                | Expected migrated `your_content/` output grouped by test case.                                 |
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
description = "Full build parity coverage for the baseline realistic legacy INI fixture."
source_format = "legacy_ini"
tags = ["legacy-ini", "baseline", "github-pages-inference", "full-parity"]

[checks]
build = true
migration = false
migrated_build = false

[env]
GITHUB_REPOSITORY = "comic-git/baseline"
```

The runner currently requires:

- `name`
- `source_format`
- `[checks].build`
- `[checks].migration`
- `[checks].migrated_build`
- `[env].GITHUB_REPOSITORY`

The runner warns if `TEST_CASE.md` is missing, but the warning does not fail the test.

## Data Flow

Build output validation follows this flow:

1. Load `test_cases/<case>/manifest.toml`.
2. Warn if `test_cases/<case>/TEST_CASE.md` is missing.
3. Create a temporary workspace.
4. Copy `test_cases/<case>/your_content/` into the temp workspace as root `your_content/`.
5. Create a local `comic_git_engine/` junction in the temp workspace.
6. Run `comic_git_engine/src/build/build_site.py` from the temp workspace root.
7. Compare the produced `build/` tree against `golden_builds/<case>/` byte-for-byte.

Refresh follows the same build flow, then fully wipes and rewrites `golden_builds/<case>/`.

Migration output validation follows this flow:

1. Load `test_cases/<case>/manifest.toml`.
2. Create a temporary workspace and stage `your_content/`.
3. Create the local `comic_git_engine/` junction.
4. Run the migration script from the temp workspace root.
5. Compare the migrated temp workspace `your_content/` tree against `golden_toml/<case>/` byte-for-byte.

Migrated-build validation follows the migration flow, then runs `comic_git_engine/src/build/build_site.py` in the migrated temp workspace and compares the produced `build/` tree against `golden_builds/<case>/`.

The migrated-build comparison ignores the copied top-level `build/your_content/` tree. Migration intentionally changes source files there, such as replacing page-level `info.ini` with `info.toml`; the parity contract for this check is the rendered site output.

The default migration script path is `comic_git_engine/src/build/migrate_to_toml.py`. It can be overridden with `--migration-script` or a manifest `[migration].script` value.

`check-build --all`, `check-migration --all`, and `check-migrated-build --all` run every manifest-backed test case with the matching `[checks]` flag enabled. Refresh commands intentionally operate on one case at a time.

## Local Static Review

Every golden build should be viewable as a static website from a local web server.

The engine writes the same raw output tree regardless of base subdirectory. The base subdirectory only controls where that tree is mounted when hosted. GitHub Pages project sites mount repository output at `/<repo-name>/`, so local review must mirror that URL shape or root-relative CSS, JavaScript, image, and page links will 404.

Harness rule:

- If a test case has a non-empty base subdirectory, that subdirectory must equal the test case name.
- For those cases, serve `golden_builds/` and open `http://localhost:<port>/<case>/`.
- If a test case intentionally has a blank base subdirectory, serve `golden_builds/<case>/` directly and open `http://localhost:<port>/`.

Examples:

| Case                     | Base subdirectory        | Server root                         | Review URL                                        |
|--------------------------|--------------------------|-------------------------------------|---------------------------------------------------|
| `baseline`               | `baseline`               | `golden_builds/`                    | `http://localhost:<port>/baseline/`               |
| `explicit-url-overrides` | `explicit-url-overrides` | `golden_builds/`                    | `http://localhost:<port>/explicit-url-overrides/` |
| `blank-subdirectory`     | blank                    | `golden_builds/blank-subdirectory/` | `http://localhost:<port>/`                        |

## Design Decisions

### Minimal temp host repo

The temp workspace contains only the selected fixture input and the engine link. It does not copy the harness repo skeleton.

This keeps the test boundary clear: the engine can only observe the files that a real host repo would provide.

### Full goldens per test case

The harness compares full build output for each case. Focused tests should stay focused by using small fixture inputs, not by weakening comparison scope.

This makes refresh behavior simple: `refresh-build` always rewrites the complete golden output for the selected case.

### Migrated builds compare against existing build goldens

`check-migrated-build` compares migrated-build output against `golden_builds/<case>/`.

That keeps the contract direct: migrating a legacy fixture to TOML should not change the produced website. The copied source tree under `build/your_content/` is ignored because migration changes it by design. If the engine intentionally changes rendered website output, refresh the build golden deliberately with `refresh-build`.

### Explicit inputs over defaults

Environment variables, source format, and enabled checks are explicit in each manifest. Duplicate data across cases is acceptable because it makes test behavior reviewable and avoids hidden fallback behavior.

### Independent fixtures over inheritance

Test cases do not inherit from baseline. This avoids setup complexity and accidental coupling. If duplicated fixture data becomes painful later, revisit this decision with a concrete maintenance problem.

## Platform Scope

The current runner is local-first and Windows-oriented. It creates the engine link with `cmd /c mklink /J`.

Linux and CI support are roadmap work. When added, platform-specific engine linking should be isolated behind a small helper rather than spread through runner commands.
