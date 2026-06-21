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
  golden_build/         # expected built site output
  golden_toml/          # expected migrated TOML output
  scripts/              # local harness scripts
  specs/                # plans and design notes for the harness
  comic_git_engine/     # local engine link/junction
```

Some of these folders may not exist yet. The harness can grow into this shape incrementally.

## Test Strategy

The intended validation flow is:

1. copy the repo to a temp workspace
2. run a legacy build
3. compare the built output to `golden_build/`
4. migrate legacy content to TOML
5. compare generated TOML to `golden_toml/`
6. run a TOML build
7. compare the built output to `golden_build/`

This gives two distinct guarantees:

- migration correctness
- rendering correctness after migration

## Notes

- Raw file comparison is the default plan because output is expected to be deterministic.
- If any nondeterministic outputs appear later, they should be handled explicitly rather than weakening the whole harness.
- This repo is local-first for now, but the structure should stay CI-friendly.
