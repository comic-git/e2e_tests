<!-- Audience: AI agents and developers modifying the harness.
     Purpose: Known sharp edges and behaviors that can silently confuse test work. -->

# Gotchas

### Root `your_content/` is not checked-in fixture data

Fixture inputs live under `test_cases/<case>/your_content/`.

Root-level `your_content/` is ignored. If you create one during manual testing, the harness will not use it.

### `TEST_CASE.md` is documentation, not configuration

The runner warns if `TEST_CASE.md` is missing, but never parses it.

Behavior comes from `manifest.toml`, `your_content/`, and the matching golden output. Keep the doc accurate, but do not treat it as a source of truth.

### Refresh rewrites the whole selected golden

`refresh-build` fully deletes and rewrites `golden_builds/<case>/`.

Review refreshed output carefully before committing because golden changes redefine the expected engine contract.

### Engine error banners matter

When `GITHUB_REPOSITORY` is set, the engine can print its fatal error banner without returning a nonzero process exit.

The harness captures engine output and fails if it sees that banner. Do not remove that check unless the engine entry point starts returning nonzero exit codes for those failures.

### The current engine link is Windows-specific

The runner currently creates a temp `comic_git_engine/` junction with `cmd /c mklink /J`.

That is appropriate for local Windows development, but CI/Linux support will need a platform-aware link or copy strategy.

### The build may mutate staged fixture content

The engine can write derived files under `your_content/` during a build, such as thumbnails.

This is why the harness stages fixture input into a temp workspace instead of building directly from checked-in `test_cases/` data.
