# Blank Subdirectory

## Purpose

Focused build parity coverage for a legacy INI site with an explicit domain and a blank `Comic subdirectory`.

This case exists to verify the local-review exception where the generated site is mounted at `/` rather than at `/<case>/`.

## Inputs

- Source format: legacy INI
- Check: build output parity
- Env: `GITHUB_REPOSITORY=ignored/example-repo`
- Config override: `Comic domain = example.test`
- Config override: `Comic subdirectory =`

## Coverage

- Blank `Comic subdirectory` produces root-relative URLs without a case-name prefix.
- Explicit `Comic domain` avoids GitHub Pages repository-name inference.
- The raw build output remains directly under `golden_builds/blank-subdirectory/`.

## Expected Behavior

- Build logs report `https://example.test` with an empty base subdirectory.
- Fresh build output matches `golden_builds/blank-subdirectory/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/blank-subdirectory/` and opening `/`.
