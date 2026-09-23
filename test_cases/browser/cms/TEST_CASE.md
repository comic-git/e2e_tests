# CMS Browser

## Purpose

Exercise the generated Decap administration surface against a fresh temporary
comic_git host repository. Browser actions may mutate the staged copy of this
fixture, but must never modify these checked-in files.

## Coverage Goals

- The production-generated admin configuration loads through Decap's local backend.
- Existing pages can be edited without changing their physical page folders.
- A representative page with ordered images and page-level metadata survives a
  Decap save without losing untouched TOML values.
- Page-level social-media metadata loads as a key/value map and saves back as a
  TOML table, including quoted keys such as `og:title`.
- Page transcripts load as language/text rows and preserve multiline transcript
  values when the CMS saves their TOML table.
- New-page filename collisions are observable through the resulting source tree.
- Exact-title and normalized-title collisions create valid sibling page bundles with
  the engine-vendored Decap runtime.
- A collision is never silently accepted: the CMS must reject it or the engine must
  reject Decap's suffixed metadata artifact on rebuild, while a valid sibling page
  bundle is accepted and rebuilt.
- Path-aware suffix behavior creates `<slug>-1/info.toml`, not
  `<slug>/info-1.toml`, for exact and normalized collisions.
- A uniquely titled page produces canonical source and survives a real rebuild.
- Saved CMS content can be rebuilt by the real engine.

## Known Issue

The vendored Decap runtime includes the path-aware suffix fix but not the
separate `slug_collision: reject` policy. The stronger CMS-side prevention tests
remain expected failures until that policy is available in a reviewed runtime.
Those tests add the proposed setting only to their temporary admin config.

The vendored runtime creates `same-title-1/info.toml` and `a-b-1/info.toml`,
then successfully rebuilds both pages without leaving numbered metadata beside
the original entry.
