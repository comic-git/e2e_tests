# Baseline

## Purpose

Full build parity coverage for realistic legacy INI `comic_git` fixture content.

This case is intended to catch broad rendering regressions and preserve the current legacy INI build contract while more focused cases are added around it.

## Source Of Truth

This document is a human-readable planning and review aid. Test behavior is defined by:

- `manifest.toml`
- `your_content/`
- `golden_builds/baseline/`

## Inputs

- Env: `GITHUB_REPOSITORY=comic-git/baseline`
- Source format: legacy INI
- Check: build output parity
- Comparison: full byte-for-byte build output parity

## Coverage

- Page `001`: default title fallback, transcript discovery, tags, and characters
- Page `002`: common metadata fields
- Page `003`: explicit multi-image ordering
- Page `004`: automatic image discovery and hidden image exclusion
- Page `005`: singular `Filename` field and post text
- Page `006`: transcript precedence and multiple transcript languages
- Page `007`: page-level social metadata override
- Page `008`: custom metadata preservation for hooks and templates
- Page `009`: external transcripts folder
- Page `010`: future-dated page exclusion from public comic output

## Expected Behavior

- GitHub Pages base URL and `/baseline` subdirectory are inferred from `GITHUB_REPOSITORY`.
- `Comic subdirectory` and `Comic domain` are omitted from `comic_info.ini`.
- Future-dated page source content remains part of copied content, but no public comic page is emitted for it.
- Fresh build output matches `golden_builds/baseline/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/baseline/`.
