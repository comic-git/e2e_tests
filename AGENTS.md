# AGENTS

## Purpose

`e2e_tests` is a realistic host-repo fixture and golden-output harness for `comic_git_engine`.

Use it to validate end-to-end behavior, especially around:

- legacy builds
- TOML migration
- TOML builds
- parity between legacy and migrated output

## Repo Rules

- Keep all engine-facing user content under `your_content/`.
- Treat `your_content/` like a real user repo, not like a synthetic test-only tree.
- Put harness machinery outside `your_content/`.
- Prefer realistic fixture content over minimal mock data when validating build behavior.
- Avoid changing fixture content casually; changes there redefine the golden contract.

## Expected Top-Level Folders

- `your_content/`: user-owned fixture content
- `golden_builds/`: checked-in golden built site output grouped by scenario
- `golden_toml/`: checked-in golden migrated TOML output
- `scripts/`: local harness runner scripts
- `specs/`: ephemeral harness plans and test design

## Current Harness Status

Current implemented pieces:

- `scripts/run_e2e.py`
- legacy build execution in a temporary copied workspace
- local `comic_git_engine` junction recreation inside the temp workspace
- `refresh-build` to regenerate `golden_builds/<scenario>/`
- `legacy-build` to compare a fresh build against `golden_builds/<scenario>/`
- strict byte-for-byte file comparison

Current baseline scenario:

- scenario name: `e2e_tests`
- full parity golden: `golden_builds/e2e_tests/`
- harness sets `GITHUB_REPOSITORY` directly
- baseline scenario should test GitHub Pages inference by omitting `Comic subdirectory` and `Comic domain` from `your_content/comic_info.ini`
- any explicit override behavior should live in separate scenarios with separate goldens

## Validation Philosophy

When possible, keep comparisons strict:

- exact built output parity for legacy builds within a named golden scenario
- exact TOML snapshot parity for migration
- exact built output parity for TOML builds within a named golden scenario

If an output later proves nondeterministic, isolate that exception narrowly instead of weakening the whole harness.

## Golden Design Direction

The harness should support both:

- one full parity scenario that captures the whole site
- focused scenarios that compare only the files present in their golden directory

Do not model extra parent folders for local server emulation. The engine contract is the raw `build/` output tree. If a scenario needs to assert a file should be absent, add an explicit absence-assertion mechanism rather than bloating the golden tree.

## Near-Term Next Steps

1. Remove explicit `Comic subdirectory` from the baseline `your_content/comic_info.ini` and refresh the `e2e_tests` golden if the inferred output matches.
2. Add scenario metadata or manifest support for focused subset goldens and absence assertions.
3. Implement legacy-to-TOML migration output in `comic_git_engine`.
4. Add `golden_toml/<scenario>/` snapshots and TOML-build parity checks.

## Safety

- Run builds and migrations in temporary working copies, not directly in the checked-in repo tree, unless intentionally refreshing golden artifacts.
- If adding new fixture cases, document them in `specs/` first.
- Keep the repo usable as a normal `comic_git` host repo with a linked local engine.
