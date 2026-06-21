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
- `golden_build/`: checked-in expected built site output
- `golden_toml/`: checked-in expected migrated TOML output
- `scripts/`: local harness runner scripts
- `specs/`: harness plans and test design

## Validation Philosophy

When possible, keep comparisons strict:

- exact built output parity for legacy builds
- exact TOML snapshot parity for migration
- exact built output parity for TOML builds

If an output later proves nondeterministic, isolate that exception narrowly instead of weakening the whole harness.

## Safety

- Run builds and migrations in temporary working copies, not directly in the checked-in repo tree, unless intentionally refreshing golden artifacts.
- If adding new fixture cases, document them in `specs/` first.
- Keep the repo usable as a normal `comic_git` host repo with a linked local engine.
