# Extra Comics RSS

## Purpose

Focused E2E case covering Extra Comic behavior and RSS behavior together.

This case protects feature boundaries that commonly interact during refactors: multi-comic discovery, inherited settings, per-comic RSS overrides, feed generation, and generated URLs.

## Scope

- Main comic with RSS enabled.
- Two Extra Comics listed in `Extra comics`.
- `side-story` has its own `comic_info.ini` and combines into the main feed.
- `solo-story` has its own `comic_info.ini` and gets its own standalone feed.
- Distinct page IDs, titles, and date values so feed item ownership is easy to inspect.

## Coverage Goals

- Extra Comic content is discovered from its own folder.
- Extra Comic inherits sensible defaults from the main comic.
- Extra Comic can override settings through its own `comic_info.ini`.
- Main `feed.xml` is generated at the expected location.
- `solo-story/feed.xml` is generated for a standalone Extra Comic feed.
- `side-story/feed.xml` is not generated when `Combine with Main RSS Feed = True`.
- Combined `side-story` RSS items appear in the main feed when configured.
- Feed item links use the correct site subdirectory and comic path.
- RSS title formatting follows the comic that owns the post.

## Fixture Shape

```text
test_cases/extra-comics-rss/
  manifest.toml
  TEST_CASE.md
  your_content/
    comic_info.ini
    comics/
      001/
    side-story/
      comic_info.ini
      comics/
        101/
    solo-story/
      comic_info.ini
      comics/
        201/
```

## Implementation Notes

- Keep the visual fixture small; RSS output is the main contract.
- Use a non-empty base subdirectory matching the case name: `extra-comics-rss`.
- Use two Extra Comics so one case covers both combined-feed and standalone-feed behavior cleanly.

## Expected Behavior

- Build logs report `https://comic-git.github.io/extra-comics-rss`.
- The build writes main comic page output under `comic/001/`.
- The build writes combined Extra Comic output under `side-story/comic/101/`.
- The build writes standalone Extra Comic output under `solo-story/comic/201/`.
- Root `feed.xml` contains `[Extra Comics RSS Fixture] Main RSS Page`.
- Root `feed.xml` contains `Side Story RSS: Combined Side Story Page`.
- Root `feed.xml` links the combined side-story item to `/extra-comics-rss/side-story/comic/101/`.
- `side-story/feed.xml` is absent.
- `solo-story/feed.xml` contains `Solo Story RSS: Standalone Solo Story Page`.
- Fresh build output matches `golden_builds/extra-comics-rss/` byte-for-byte.
- The golden can be reviewed by serving `golden_builds/` and opening `/extra-comics-rss/`.
