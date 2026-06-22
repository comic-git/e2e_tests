# e2e_tests

This repo is a local end-to-end test harness for `comic_git_engine`.

Its job is to validate that the engine can:

- build a legacy-format `comic_git` site from realistic fixture content
- migrate that same content to TOML
- build the migrated site
- produce output that matches checked-in golden expectations

## Design Constraints

This repo should continue to look like a normal `comic_git` host repo in all the ways that matter to the engine.

That means:

- all user-provided site content lives under `your_content/`
- `your_content/` should look like something a real user might create
- engine-facing fixture data should stay realistic and readable

Harness-specific artifacts should live outside `your_content/`.

## Expected Layout

```text
.
  your_content/         # realistic host-repo fixture content
  golden_builds/        # expected built site output grouped by scenario
  golden_toml/          # expected migrated TOML output grouped by scenario later
  scripts/              # local harness scripts
  specs/                # ephemeral plans and design notes for the harness
  comic_git_engine/     # local engine link/junction
```

Some of these folders may not exist yet. The harness can grow into this shape incrementally.

## Current State

Implemented today:

- `scripts/run_e2e.py`
- `refresh-build` command
- `legacy-build` command
- temp-workspace execution
- byte-for-byte build comparison against `golden_builds/<scenario>/`
- full parity baseline scenario at `golden_builds/e2e_tests/`
- realistic legacy fixture content under `your_content/`
- distinct generated fixture art for pages `002` through `010`

Current default scenario behavior:

- scenario name: `e2e_tests`
- `GITHUB_REPOSITORY` is set by the harness
- the baseline scenario should rely on GitHub Pages inference from `GITHUB_REPOSITORY`
- `Comic subdirectory` and `Comic domain` should be omitted from `your_content/comic_info.ini` in the baseline scenario
- explicit `comic_info.ini` override cases should be modeled as separate scenarios with their own goldens

## Test Strategy

The intended validation flow is:

1. copy the repo to a temp workspace
2. run a legacy build
3. compare the built output to `golden_builds/<scenario>/`
4. migrate legacy content to TOML
5. compare generated TOML to `golden_toml/<scenario>/`
6. run a TOML build
7. compare the built output to `golden_builds/<scenario>/`

This gives two distinct guarantees:

- migration correctness
- rendering correctness after migration

## Golden Strategy

Use two kinds of golden scenarios:

- one full parity scenario that captures the whole built site
- smaller focused scenarios that only include the files they care about

Subset scenarios should compare only the files present in the selected golden directory. If a scenario needs to prove a file should not exist, add an explicit absence assertion mechanism rather than forcing every scenario to store a full site copy.

## Notes

- Raw file comparison is the default plan because output is expected to be deterministic.
- If any nondeterministic outputs appear later, they should be handled explicitly rather than weakening the whole harness.
- This repo is local-first for now, but the structure should stay CI-friendly.
