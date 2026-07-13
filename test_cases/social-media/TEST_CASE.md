# Social Media

## Purpose

Focused E2E case for social preview metadata.

This validates site-level overrides, page-level overrides, fallback behavior, and generated Open Graph metadata across key page types.

## Scope

- Provides a site-level `your_content/social_media.json`.
- Provides a page-level `social_media.json` for comic page `002`.
- Includes two comic pages so fallback and override behavior can both be observed.
- Includes a standard `your_content/images/preview_image.png`.

## Coverage Goals

- Site pages emit site-level Open Graph metadata.
- Comic page `001` emits article-like preview metadata from the site-level `comic` template.
- Comic page `002` uses page-local `social_media.json` instead of the site-level `comic` template.
- Preview image URLs include the correct case subdirectory.
- Metadata remains present on home, latest, archive, and comic pages where expected.

## Fixture Shape

```text
test_cases/social-media/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    social_media.json
    images/
      preview_image.png
    comics/
      001/
      002/
        social_media.json
```

## Implementation Notes

- Keep this separate from webring because the failure modes and review surface are different.
- Use a non-empty base subdirectory matching the case name: `social-media`.
- Use distinctive metadata values so the golden diff clearly shows whether overrides are applied.

## Expected Behavior

- Build logs report `https://comic-git.github.io/social-media`.
- `index.html` uses site-level metadata from `your_content/social_media.json`.
- `comic/001/index.html` uses comic-level fallback metadata, including post text and generated thumbnail URL.
- `comic/002/index.html` uses page-local override values from `comics/002/social_media.json`.
- Generated preview image and thumbnail URLs include `/social-media/`.
- Fresh build output matches `golden_builds/social-media/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/social-media/`.
