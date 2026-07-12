# e2e_tests

This repo is a local end-to-end test harness for `comic_git_engine`.

Its job is to validate that the engine can:

- build a legacy-format `comic_git` site from realistic fixture content
- migrate that same content to TOML
- build the migrated site
- produce output that matches checked-in golden expectations

## Design Constraints

This repo is a harness repo, not a normal `comic_git` host repo.

Checked-in fixture inputs live under `test_cases/<case>/your_content/`. During a run, the harness creates a minimal temporary host repo containing only the selected `your_content/` tree and the linked local engine, so the engine sees a realistic host-repo layout without mutating checked-in fixture data.

Root-level `your_content/` and `build/` are ignored to avoid accidentally committing local manual runs.

## Expected Layout

```text
.
  test_cases/           # checked-in fixture inputs, manifests, and case docs
  golden_builds/        # expected built site output grouped by test case
  golden_toml/          # expected migrated TOML output grouped by test case later
  scripts/              # local harness scripts
  specs/                # ignored agent scratch plans and design notes
  docs/                 # future durable harness documentation
  comic_git_engine/     # local engine link/junction
```

Some of these folders may not exist yet. The harness can grow into this shape incrementally.

## Current State

Implemented today:

- `scripts/run_e2e.py`
- `refresh-build` command
- `legacy-build` command
- minimal temp host execution
- test case inputs under `test_cases/<case>/your_content/`
- co-located test case manifests at `test_cases/<case>/manifest.toml`
- co-located human reference docs at `test_cases/<case>/TEST_CASE.md`
- byte-for-byte build comparison against `golden_builds/<case>/`
- full parity baseline test case at `golden_builds/baseline/`
- realistic legacy fixture content under `test_cases/baseline/your_content/`
- distinct generated fixture art for pages `002` through `010`

Current default test case behavior:

- test case name: `baseline`
- `GITHUB_REPOSITORY` is set by `test_cases/baseline/manifest.toml`
- the baseline test case should rely on GitHub Pages inference from `GITHUB_REPOSITORY`
- `Comic subdirectory` and `Comic domain` should be omitted from `test_cases/baseline/your_content/comic_info.ini`
- explicit `comic_info.ini` override cases should be modeled as separate test cases with their own goldens

## Test Case Manifests

Each test case has a co-located `manifest.toml`:

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

Every build-relevant environment variable must be listed explicitly in `[env]`. The runner warns when `TEST_CASE.md` is missing, but it does not parse that document for behavior.

`TEST_CASE.md` is a human-readable planning and review aid. Test behavior is defined by `manifest.toml`, `your_content/`, and the matching `golden_*` output.

## Test Strategy

The intended validation flow is:

1. create a minimal temp host repo
2. stage `test_cases/<case>/your_content/` as root `your_content/`
3. run a legacy build
4. compare the built output to `golden_builds/<case>/`
5. migrate legacy content to TOML
6. compare generated TOML to `golden_toml/<case>/`
7. run a TOML build
8. compare the built output to `golden_builds/<case>/`

This gives two distinct guarantees:

- migration correctness
- rendering correctness after migration

## Golden Strategy

Each test case has an independent full golden build output under `golden_builds/<case>/`. Focused test cases should stay small by keeping their input fixture small, not by weakening comparison scope.

`refresh-build` fully wipes and rewrites the selected `golden_builds/<case>/` output.

## Notes

- Raw file comparison is the default plan because output is expected to be deterministic.
- If any nondeterministic outputs appear later, they should be handled explicitly rather than weakening the whole harness.
- This repo is local-first and Windows-oriented for now. Linux/CI support is roadmap work.
