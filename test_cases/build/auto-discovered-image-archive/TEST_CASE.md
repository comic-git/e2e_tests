# Auto-discovered Image Archive

## Purpose

Verify that a legacy page `info.ini` without `Filename`, `Filenames`, or
`[Image <label>]` declarations can auto-discover multiple images and list each
one separately in the Archive.

## Inputs

- One legacy INI page with two PNG images in its page folder
- `List images separately = True`
- `Image title fallback = Filename`
- No explicit image declarations or thumbnails

## Expected Behavior

- Both PNG files are auto-discovered in filename order.
- The Archive contains two entries linking to the two positional image anchors.
- Archive titles are `First image` and `Second image`.
- A conventional `_thumbnail.jpg` and one short identity-derived thumbnail are generated.
