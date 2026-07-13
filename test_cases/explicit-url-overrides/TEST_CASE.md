# Explicit URL Overrides

## Purpose

Focused build parity coverage for explicit `Comic domain` and `Comic subdirectory` settings in legacy INI content.

This case pairs with `baseline`, which intentionally omits those settings and relies on GitHub Pages inference.

## Inputs

- Source format: legacy INI
- Check: build output parity
- Env: `GITHUB_REPOSITORY=ignored/example-repo`
- Config override: `Comic domain = example.test`
- Config override: `Comic subdirectory = explicit-url-overrides`

## Coverage

- Explicit `Comic domain` overrides any domain inferred from `GITHUB_REPOSITORY`.
- Explicit `Comic subdirectory` overrides any repository-name subdirectory inferred from `GITHUB_REPOSITORY`.
- Generated URLs and root-relative asset paths use `/explicit-url-overrides`.

## Expected Behavior

- Build logs report `https://example.test/explicit-url-overrides`.
- Fresh build output matches `golden_builds/explicit-url-overrides/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/explicit-url-overrides/`.
