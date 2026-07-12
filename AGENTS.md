# AGENTS

## Purpose

`e2e_tests` is a realistic fixture and golden-output harness for `comic_git_engine`.

Use it to validate end-to-end behavior, especially around:

- legacy builds
- TOML migration
- TOML builds
- parity between legacy and migrated output

## Repo Rules

- Keep checked-in engine-facing user content under `test_cases/<case>/your_content/`.
- Treat each test case `your_content/` like a real user repo, not like a synthetic test-only tree.
- Put harness machinery outside each test case `your_content/`.
- Prefer realistic fixture content over minimal mock data when validating build behavior.
- Avoid changing fixture content casually; changes there redefine the golden contract.
- Root-level `your_content/` and `build/` are disposable local run artifacts and should stay ignored.

## Expected Top-Level Folders

- `test_cases/`: checked-in fixture inputs and co-located manifests
- `golden_builds/`: checked-in golden built site output grouped by test case
- `golden_toml/`: checked-in golden migrated TOML output grouped by test case
- `scripts/`: local harness runner scripts
- `specs/`: ephemeral harness plans and test design

## Current Harness Status

Current implemented pieces:

- `scripts/run_e2e.py`
- legacy build execution in a temporary copied workspace
- selected test case staging from `test_cases/<case>/your_content/`
- co-located test case manifests at `test_cases/<case>/manifest.toml`
- local `comic_git_engine` junction recreation inside the temp workspace
- `refresh-build` to regenerate `golden_builds/<case>/`
- `legacy-build` to compare a fresh build against `golden_builds/<case>/`
- strict byte-for-byte file comparison
- subset build comparison mode for focused goldens
- explicit absent-path assertions

Current baseline test case:

- test case name: `baseline`
- input fixture: `test_cases/baseline/your_content/`
- manifest: `test_cases/baseline/manifest.toml`
- full parity golden: `golden_builds/baseline/`
- harness sets `GITHUB_REPOSITORY` from the manifest by default
- baseline test case should test GitHub Pages inference by omitting `Comic subdirectory` and `Comic domain` from `test_cases/baseline/your_content/comic_info.ini`
- any explicit override behavior should live in separate test cases with separate goldens

## Validation Philosophy

When possible, keep comparisons strict:

- exact built output parity for legacy builds within a named test case
- exact TOML snapshot parity for migration
- exact built output parity for TOML builds within a named test case

If an output later proves nondeterministic, isolate that exception narrowly instead of weakening the whole harness.

## Golden Design Direction

The harness should support both:

- one full parity test case that captures the whole site
- focused test cases that compare only the files present in their golden directory

Do not model extra parent folders for local server emulation. The engine contract is the raw `build/` output tree. If a test case needs to assert a file should be absent, use the manifest's absence assertion mechanism rather than bloating the golden tree.

## Near-Term Next Steps

1. Add more focused `test_cases/<case>/` fixtures for explicit override behavior.
2. Refine refresh behavior for subset goldens if focused cases need generated refresh support.
3. Implement legacy-to-TOML migration output in `comic_git_engine`.
4. Add `golden_toml/<case>/` snapshots and TOML-build parity checks.

## Safety

- Run builds and migrations in temporary working copies, not directly in the checked-in repo tree, unless intentionally refreshing golden artifacts.
- If adding new fixture cases, document them in `specs/` first.
- Keep checked-in fixture data under `test_cases/`; root-level `your_content/` is for local manual runs only and should not be committed.
