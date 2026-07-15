# Publishing Filtering

## Purpose

Focused E2E case for page discovery, scheduling, and public output filtering.

Baseline already covers several of these paths, but this case keeps the same risks isolated in a small fixture.

## Scope

- Published page using explicit `Filename`.
- Published page using automatic image discovery.
- Hidden image file beginning with `_`.
- Future-dated page.
- Page-level private metadata beginning with `!`.

## Coverage Goals

- Future-dated pages are excluded from public comic output by default.
- Auto-discovery includes expected images.
- Auto-discovery excludes hidden `_` image files.
- Explicit filenames override auto-discovery.
- Generated page order and `page_info_list.json` stay stable.
- Private or internal metadata filtering remains correct.

## Fixture Shape

```text
test_cases/publishing-filtering/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    home page.html
    comics/
      001/
      002/
      003/
```

## Implementation Notes

- Use a non-empty base subdirectory matching the case name: `publishing-filtering`.
- Page `001` uses explicit `Filename`.
- Page `002` relies on auto-discovery and includes `_hidden.png`, which should not become a comic image.
- Page `003` is scheduled for January 1, 2999 and should not produce a public comic page in normal builds.

## Expected Behavior

- Build logs report `https://comic-git.github.io/publishing-filtering`.
- `comic/001/index.html` is generated for the explicit `Filename` page.
- `comic/002/index.html` is generated for the auto-discovery page.
- `comic/003/index.html` is absent because page `003` is future-dated.
- `comic/page_info_list.json` contains pages `001` and `002` in stable order.
- `comic/page_info_list.json` does not contain private `!` metadata.
- Page `002` renders `alpha.png` and `beta.png`, but not `_hidden.png`.
- `_hidden.png` and future page source content remain in copied `your_content/`.
- Fresh build output matches `golden_builds/publishing-filtering/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/publishing-filtering/`.
