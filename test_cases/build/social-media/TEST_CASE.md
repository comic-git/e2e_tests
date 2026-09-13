# Social Media

## Purpose

Focused E2E case for social preview metadata.

This validates site-level overrides, page-level overrides, fallback behavior, and generated Open Graph metadata across key page types.

## Scope

- Provides a site-level `your_content/social_media.json`.
- Provides a page-level `social_media.json` for comic page `002`.
- Includes three comic pages so thumbnail, site-preview fallback, and page override behavior can all be observed.
- Includes a standard `your_content/images/preview_image.png`.

## Coverage Goals

- Site pages emit site-level Open Graph metadata.
- Comic page `001` emits article-like preview metadata from the site-level `comic` template.
- Comic page `002` uses page-local `social_media.json` instead of the site-level `comic` template.
- Preview image URLs include the correct case subdirectory.
- Default comic previews use the resolved page thumbnail and first image alt text.
- A page without a usable thumbnail would fall back to `your_content/images/preview_image.png`.
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
      003/
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
- `comic/003/index.html` uses comic-level metadata and the site preview image because the no-image page
  explicitly disables its page thumbnail.
- Generated preview image and thumbnail URLs include `/social-media/`.
- Fresh build output matches `golden_builds/social-media/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/social-media/`.

## Manual Visual Review

From the repository root, serve the shared golden-build root. Use page source or browser developer tools to inspect `<head>` metadata that is not visible in the rendered page:

```powershell
cd golden_builds
python -m http.server 8000
# Open http://localhost:8000/social-media/
```

- [ ] Home and archive are styled and list all three comic pages.
- [ ] Page `001` displays its comic normally and uses its generated thumbnail and first-image alt text in Open Graph metadata.
- [ ] Page `002` displays normally and its `<head>` contains the distinctive page-local title, description, site name, and image alt text.
- [ ] Page `003` is intentionally text-only and does not show a broken comic image.
- [ ] Page `003` and latest use `your_content/images/preview_image.png` as `og:image`.
- [ ] Home uses the site-level `Social Fixture Site` metadata and site preview image.
- [ ] All generated preview and thumbnail URLs include `/social-media/`.
