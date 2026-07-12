# e2e_tests

This repo is a local end-to-end test harness for `comic_git_engine`.

Its job is to validate that the engine can:

- build a legacy-format `comic_git` site from realistic fixture content
- migrate that same content to TOML
- build the migrated site
- produce output that matches checked-in golden expectations

## Design Constraints

This repo is a harness repo, not a normal `comic_git` host repo.

Checked-in fixture inputs live under `test_cases/<case>/your_content/`. During a run, the harness stages the selected fixture into a temporary workspace as root-level `your_content/`, so the engine still sees a realistic host-repo layout without mutating checked-in fixture data.

Root-level `your_content/` and `build/` are ignored to avoid accidentally committing local manual runs.

## Expected Layout

```text
.
  test_cases/           # checked-in fixture inputs and manifests
  golden_builds/        # expected built site output grouped by test case
  golden_toml/          # expected migrated TOML output grouped by test case later
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
- test case inputs under `test_cases/<case>/your_content/`
- co-located test case manifests at `test_cases/<case>/manifest.toml`
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

[env]
GITHUB_REPOSITORY = "comic-git/e2e_tests"

[compare.build]
mode = "full"
absent = []
```

`compare.build.mode` can be `full` or `subset`. Full mode compares the entire build output against `golden_builds/<case>/`; subset mode compares only files present in the golden directory. `compare.build.absent` lists output paths that must not exist.

## Test Strategy

The intended validation flow is:

1. copy the repo to a temp workspace
2. stage `test_cases/<case>/your_content/` as `your_content/`
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

Use two kinds of golden test cases:

- one full parity test case that captures the whole built site
- smaller focused test cases that only include the files they care about

Subset test cases should compare only the files present in the selected golden directory. If a test case needs to prove a file should not exist, add an explicit absence assertion mechanism rather than forcing every test case to store a full site copy.

## Notes

- Raw file comparison is the default plan because output is expected to be deterministic.
- If any nondeterministic outputs appear later, they should be handled explicitly rather than weakening the whole harness.
- This repo is local-first for now, but the structure should stay CI-friendly.
