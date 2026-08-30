# Structured Images

## Purpose

Focused 1.1 coverage for pages that own ordered structured comic images.

This case defines the full-build contract that unit tests cannot cover alone:
source parsing, image processing, metadata serialization, archive projection,
rendered anchors, RSS, Extra Comic identity, migration, and deployed schema
validation all need to agree.

## Inputs

- Source formats: flat legacy INI, sectioned legacy INI, and TOML `[[images]]`
- Checks: build output parity, migration output parity, and migrated-build parity
- Env: `GITHUB_REPOSITORY=comic-git/structured-images`
- Main archive: `Entry mode = Images`, `Use thumbnails = True`
- Extra Comic archive: `Entry mode = Pages`, `Use thumbnails = True`
- Main and Extra Comic deliberately reuse a page folder and image filename

## Fixture Shape

```text
test_cases/structured-images/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    comics/
      001/  # flat Filename/Filenames
      002/  # ordered [Image <label>] sections
      003/  # no-image page
      004/  # info.toml with [[images]]
    side-story/
      comic_info.ini
      comics/
        001/  # collides textually with main comic identity
```

Use real image files. Include:

- a conventional existing `_thumbnail.jpg`
- an explicitly configured page or image thumbnail
- an explicitly blank image thumbnail
- an omitted additional-image thumbnail that the engine generates

## Coverage Goals

- Flat `Filename` and `Filenames` remain valid without advanced image config.
- Ordered `[Image <label>]` sections preserve source order and reject mixed flat declarations.
- TOML accepts ordered image tables only; string-list image entries are not valid.
- Omitted image title and alt text inherit resolved page defaults.
- Explicit blank image title, alt text, and thumbnail suppress inheritance.
- Page/image identity includes the owning comic and normalized page-relative filename.
- Main and Extra Comic images with the same page folder and filename have different IDs and anchors.
- Reordering images would not alter filename-based identity or SHA-256-derived anchors.
- Page `_thumbnail.jpg` remains the first-image fallback.
- Explicit thumbnails remain user-owned and are not overwritten.
- Additional image thumbnails use deterministic identity-derived filenames.
- Main archive image mode emits one ordered thumbnail entry per image and links directly to image anchors.
- Main no-image pages remain visible as one page-only archive entry.
- Extra Comic page mode emits one thumbnail entry per page.
- Keeping thumbnails enabled across both archives proves entry mode varies independently.
- Comic HTML uses real `alt` attributes and stable image element IDs.
- Infinite scroll consumes supplied page/image URLs, alt text, page fragments, and image fragments.
- RSS remains one item per page, renders every image with its resolved alt text, and keeps no-image post content.
- Social previews use the resolved page thumbnail and first image alt text.

## Metadata And Schema Contract

Every generated `page_info_list.json`, including the Extra Comic document, must:

- contain top-level `schema_version`, `comic_git_engine_version`, `comic`, and `pages`
- expose resolved page/image values without configured-source or private `!` fields
- use ISO page dates and build-resolved URLs
- validate against `comic_git_engine/schemas/page_info_list.schema.json` deployed by that build

Semantic tests should assert entry counts and order, direct archive fragments,
resolved title/alt/thumbnail values, no-image visibility, and collision safety.

## Expected Behavior

- Build logs report `https://comic-git.github.io/structured-images`.
- Fresh output matches `golden_builds/structured-images/` byte-for-byte.
- Migrated content matches `golden_toml/structured-images/` byte-for-byte.
- Building the migrated content matches `golden_builds/structured-images/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/structured-images/`.

## Manual Visual Review

From the repository root, serve the shared golden-build root:

```powershell
cd golden_builds
python -m http.server 8000
# Open http://localhost:8000/structured-images/
```

- [ ] Page `001` renders `shared.png` followed by `flat-second.png`.
- [ ] Page `002` renders `ordered-b.png` followed by `ordered-a.png`; the first image intentionally has blank title and alt text.
- [ ] Page `003` is text-only but retains post content and working navigation.
- [ ] Page `004` renders `toml-first.png` followed by `toml-second.png`.
- [ ] Image overlays work, and each image has a stable fragment target.
- [ ] The main archive has seven ordered entries: two each for pages `001`, `002`, and `004`, plus one text-only entry for page `003`.
- [ ] Archive image entries link directly to the correct image fragment.
- [ ] The explicitly blank thumbnail for `ordered-b.png` produces a deliberate text-only archive entry rather than a broken image.
- [ ] Other archive entries show their explicit, conventional, or generated thumbnails.
- [ ] `side-story/archive/` contains one page-level thumbnail entry, not one entry per image.
- [ ] `side-story/comic/001/` uses the side-story path and image without colliding with main page `001`.
- [ ] Infinite scroll renders structured images in source order and image-fragment URLs start on the owning page.
- [ ] Root `feed.xml` has four page items, including the text-only page, and `side-story/feed.xml` has one side-story item.
