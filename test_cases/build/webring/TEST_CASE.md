# Webring

## Purpose

Focused E2E case for local webring behavior.

This validates the user-facing contract around local webring JSON loading and generated previous/home/next navigation output without depending on a network endpoint.

## Scope

- Enables `[Webring]` in `comic_info.ini`.
- Uses `Endpoint = local`.
- Provides `your_content/webring.json`.
- Configures the current member ID as the middle member so previous/next behavior is deterministic.
- Includes three members to exercise previous, current, and next selection.
- Renders one previous member without an image and one next member with an image.

## Coverage Goals

- Local endpoint mode loads `your_content/webring.json`.
- Current member ID selects the correct member from the JSON list.
- Previous and next links render with the expected URLs.
- Home link renders from the JSON `home` object.
- Member image fallback behavior renders both text-only and image-based links.
- Generated page asset paths include the correct case subdirectory.

## Fixture Shape

```text
test_cases/webring/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    webring.json
    comics/
      001/
```

## Implementation Notes

- Keep this separate from social media. Webring failures are mostly data-contract and navigation failures, while social media failures are metadata/template failures.
- Use a non-empty base subdirectory matching the case name: `webring`.
- Prefer local endpoint mode so the harness remains deterministic and offline.
- Leave full-member-list rendering for a separate focused case if that path needs E2E coverage later.

## Expected Behavior

- Build logs report `https://comic-git.github.io/webring`.
- Build logs do not attempt a network request for the webring endpoint.
- `index.html` and `comic/001/index.html` contain the `Harness Webring` header.
- The previous link points to `https://previous.example.test/` and renders as text.
- The home link points to `https://example.test/webring/` and renders as text.
- The next link points to `https://next.example.test/` and renders an image from `https://next.example.test/icon.png`.
- Fresh build output matches `golden_builds/webring/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/webring/`.

## Manual Visual Review

From the repository root, serve the shared golden-build root:

```powershell
cd golden_builds
python -m http.server 8000
# Open http://localhost:8000/webring/
```

- [ ] Home and comic page both show the `Harness Webring` section.
- [ ] Previous is a text link to `https://previous.example.test/`.
- [ ] Home is a text link to `https://example.test/webring/`.
- [ ] Next is an image link to `https://next.example.test/` with image URL `https://next.example.test/icon.png`.
- [ ] The current member is not incorrectly rendered as previous or next.
- [ ] Normal site navigation and comic rendering remain unaffected by the webring.

The intentionally fake external next-image host may not resolve during local review. Confirm the generated `<img>` URL in browser developer tools rather than treating that network failure as a golden-build failure.
