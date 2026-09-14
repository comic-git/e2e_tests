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
- New-page filename collisions are observable through the resulting source tree.
- Exact-title and normalized-title collisions exercise the same unsafe Decap behavior.
- A collision is never silently accepted: the CMS must reject it or the engine must
  reject Decap's suffixed metadata artifact on rebuild, while a valid sibling page
  bundle is accepted and rebuilt.
- Candidate path-aware suffix behavior creates `<slug>-1/info.toml`, not
  `<slug>/info-1.toml`, for exact and normalized collisions.
- A uniquely titled page produces canonical source and survives a real rebuild.
- Saved CMS content can be rebuilt by the real engine.

## Known Issue

Decap 3.16.0 resolves exact and normalized new-page title collisions by writing
`info-1.toml` beside the existing `info.toml`. The engine now rejects that file
with an actionable build error. The stronger CMS-side prevention tests remain
expected failures against stock Decap until a supported collision policy is
available. Those tests add the proposed `slug_collision: reject` setting only
to their temporary admin config, so production output remains pinned to stock
Decap's supported configuration.

A separate expected-failure contract covers path-aware suffix placement. A
candidate fix should create `same-title-1/info.toml` and `a-b-1/info.toml`, then
successfully rebuild both pages without leaving numbered metadata beside the
original entry.
