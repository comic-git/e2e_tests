# Theme Overrides

## Purpose

Focused E2E case for theme and presentation override behavior.

This should protect the user-owned presentation layer: configured theme selection, template overrides, CSS layering, homepage content, and copied theme assets.

## Inputs

- Source format: legacy INI
- Check: build output parity
- Env: `GITHUB_REPOSITORY=comic-git/theme-overrides`
- Date format: `%Y-%m-%d`
- Theme: `focused-theme`
- Template override: `themes/focused-theme/templates/index.tpl`
- Theme CSS: `themes/focused-theme/css/*.css`

## Scope

- Configure a non-default theme in `comic_info.ini`.
- Include custom theme CSS.
- Include at least one template override.
- Include homepage content.
- Include one comic page to verify comic-page template behavior.

## Coverage Goals

- The configured theme is selected.
- Theme CSS is copied and linked.
- Engine CSS still layers with user theme CSS where expected.
- Template override output appears in generated HTML.
- Homepage content is rendered through the expected path.
- Generated asset paths include the correct case subdirectory.

## Fixture Shape

```text
test_cases/theme-overrides/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    home page.html
    themes/
      focused-theme/
        css/
        templates/
    comics/
      001/
```

## Implementation Notes

- Use a non-empty base subdirectory matching the case name: `theme-overrides`.
- Keep the override obvious but small, such as a unique marker in a template and a unique CSS filename or rule.
- Avoid turning this into a broad visual regression case; the golden should mostly prove override wiring.

## Expected Behavior

- Build logs report `https://comic-git.github.io/theme-overrides`.
- Generated pages link to `your_content/themes/focused-theme/css/...`.
- `index.html` contains `focused-theme-index-marker`.
- `index.html` contains homepage content from `home page.html`.
- Fresh build output matches `golden_builds/theme-overrides/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/theme-overrides/`.

## Migration Coverage

- Migration output writes `comics/001/info.toml`.
- Migration deletion removes page-level `comics/001/info.ini`.
- Migration output writes `comic_info.toml` and deletes root `comic_info.ini`.
- Migrated-build parity is intentionally disabled until TOML pages without page-level social metadata preserve default social metadata.
