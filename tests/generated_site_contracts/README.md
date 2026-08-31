# Generated Site Contract Tests

These tests treat checked-in `golden_builds/` as deployed public artifacts and
validate semantic contracts across those artifacts. They complement, rather
than replace, the byte-for-byte comparisons in `tests/test_goldens.py`.

Use this suite for assertions such as:

- generated metadata validates against the schema shipped in the same site
- public fields exclude private configuration and retain required values
- URLs, image order, and anchors agree across metadata and rendered pages
- archives, feeds, social metadata, and Extra Comics remain mutually consistent

Do not use this suite for:

- whole-file equality, whitespace, or copied-asset checks covered by goldens
- Python implementation details internal to `comic_git_engine`
- template or JavaScript source-string assertions better owned by engine tests
- literal fixture values that do not express a public relationship or invariant

Run only this category from the repository root with:

```powershell
venv\Scripts\python.exe -m pytest tests\generated_site_contracts
```

An intentional golden refresh may require a matching contract-test update, but
the contract should be reviewed independently rather than accepted as a side
effect of refreshing snapshots.
