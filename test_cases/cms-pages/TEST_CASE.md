# CMS Pages

## Purpose

Focused full-build coverage for the engine-generated Decap CMS admin surface.

The fixture uses only page data that the first CMS vertical slice can round-trip
safely: date-only TOML posts, explicit titles, optional text, and ordered image
tables. It includes a main comic and an Extra Comic so the generated collection
paths and labels are exercised together.

## Coverage Goals

- A CMS-enabled TOML site generates marked `admin/index.html` and `admin/config.yml`.
- Production backend settings use the manifest repository and configured OAuth URL.
- The main comic collection appears before the Extra Comic collection.
- A multi-image page retains its explicit image order.
- A text-only page remains a valid CMS entry and a valid rendered comic page.
- Extra Comic pages use their own collection folder.
- Normal site output remains valid alongside the admin surface.
