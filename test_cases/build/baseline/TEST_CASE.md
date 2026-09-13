# Baseline

## Purpose

Full build parity coverage for realistic legacy INI `comic_git` fixture content.

This case is intended to catch broad rendering regressions and preserve the current legacy INI build contract while more focused cases are added around it.

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
- Multi-image pages render ordered structured images with resolved alt text and stable image anchors.
- `comic/page_info_list.json` uses the versioned page/image hierarchy and validates against
  `comic_git_engine/schemas/page_info_list.schema.json` from the same build.
- Fresh build output matches `golden_builds/baseline/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/baseline/`.

## Manual Visual Review

From the repository root, serve the shared golden-build root so `/baseline/` is the URL mount point:

```powershell
cd golden_builds
python -m http.server 8000
# Open http://localhost:8000/baseline/
```

- [ ] Home, archive, latest, infinite-scroll, tagged, and comic pages are styled and load without unexpected asset errors.
- [ ] First, previous, next, and latest navigation moves through the published pages correctly.
- [ ] The archive has Chapter 1 and Chapter 2 sections with working thumbnails and links.
- [ ] Page `003` renders `panel-b.png` before `panel-a.png`, and its image-fragment links land on the correct image.
- [ ] Page `004` renders `alpha.png` and `beta.png`, while `_hidden.png` is absent.
- [ ] Page `005` shows its post text.
- [ ] Transcript controls and content work on pages `001`, `006`, and `009`; page `006` exposes both languages.
- [ ] Page `010` is absent from archive, latest, navigation, and public comic output.
- [ ] Infinite scroll loads published pages and their images in the expected order.
