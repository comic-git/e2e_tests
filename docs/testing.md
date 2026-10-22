<!-- Audience: AI agents and developers running or adding harness tests.
     Purpose: Explain how to run the harness, refresh goldens, and add test cases correctly. -->

# Testing

## SFTP deployment tests

Run the real-build SFTP cases with `python -m pytest tests/test_sftp_deployment.py`.
Use a Python environment with the harness and engine dependencies installed.
These tests stage the independent `test_cases/deployment/sftp` fixture, execute
the build CLI, and check final hidden-file filtering, scheduled-page removal,
source preservation and portable deployment artifacts. They need no credentials.

For real OpenSSH/lftp coverage, prepare two portable packages (cleanup on/off):

```sh
python -m e2e_harness.sftp artifacts/sftp-run
```

Choose a new output directory each time. On a disposable Linux VM with Python 3,
`openssh-server`, `openssh-client`, and `lftp` installed, copy the package and run:

```sh
sudo python3 artifacts/sftp-run/check_sftp_transfer.py artifacts/sftp-run
```

Only `clean/downloaded/`, `keep/downloaded/` and `check_sftp_transfer.py` are needed
on that VM; engine dependencies are not needed there. Run the script from a
trusted checkout. It requires root to create a temporary local account and a
localhost-only SSH server. It removes the account, process, keys and test files
on exit. It does not connect to an existing SFTP service or use cloud credentials.

The transfer test uses the exact generated standalone runner and lftp script.
It verifies password/key authentication, strict host-key rejection, missing
destination failure, same-size updates despite newer remote timestamps, default
cleanup, cleanup disabled, hidden-file publication and preserved exclusions.
The disposable server forces internal-sftp, so remote shell commands cannot make
the test pass accidentally. It is intentionally separate from normal pytest,
which must not silently create OS accounts or require root.

Validated with the SFTP engine commit `228fd42`: both build variants and all real
transfer checks passed on 2026-10-18. This does not replace a provider-specific
DreamHost smoke test or the full release regression pass.

## Running Tests

Run commands from the `e2e_tests` repo root.

For normal validation, run the pytest wrapper suite:

```powershell
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest
```

Pytest reports each enabled check for each test case independently. Disabled manifest checks are reported as skipped.

Generated-site public contracts can be run independently:

```powershell
venv\Scripts\python.exe -m pytest tests\generated_site_contracts
```

These tests validate semantic relationships across committed generated artifacts,
including deployed schema conformance and agreement between metadata, HTML,
archives, feeds, and social values. See
`tests/generated_site_contracts/README.md` for the category boundary.

The harness CLI remains available for targeted checks and golden refreshes:

```powershell
# Validate the default baseline case
python scripts/run_e2e.py check-build

# Validate a named case
python scripts/run_e2e.py check-build --case baseline

# Validate every build-enabled case
python scripts/run_e2e.py check-build --all

# Keep the temp workspace for debugging
python scripts/run_e2e.py check-build --case baseline --keep-temp
```

`python` launches the harness script. The harness then defaults engine execution to `venv/Scripts/python.exe` when that venv exists.

Migration commands are available for cases whose manifests enable them:

```powershell
# Compare migrated your_content/ against golden_toml/<case>/
python scripts/run_e2e.py check-migration --case baseline

# Run migration, then build, then compare build/ against golden_builds/<case>/
python scripts/run_e2e.py check-migrated-build --case baseline
```

The harness defaults the migration script path to `comic_git_engine/src/build/migrate_to_toml.py`. If the engine lands a different script name, pass `--migration-script <path-from-comic_git_engine-root>` or set `[migration].script` in the case manifest.

Install migration-only engine dependencies into the harness venv before running migration checks:

```powershell
venv\Scripts\python.exe -m pip install -r comic_git_engine\requirements_migration.txt
```

## Refreshing Goldens

Refresh is deliberate and destructive for the selected golden output or outputs.

```powershell
# Refresh one case
python scripts/run_e2e.py refresh-build --case baseline

# Refresh every build-enabled case
python scripts/run_e2e.py refresh-build --all
```

Use `--all` when reviewing how an engine change affects every generated site. Because the goldens are tracked, review the resulting `git diff -- golden_builds` before committing.

This command:

1. Builds each selected, build-enabled case in a temp host repo.
2. Deletes its `golden_builds/<case>/`.
3. Copies the fresh build output into `golden_builds/<case>/`.
4. Normalizes recognized text files in each refreshed golden to LF line endings.

Only refresh goldens after confirming the new output is the intended behavior.

Migration snapshots are refreshed separately:

```powershell
python scripts/run_e2e.py refresh-migration --case baseline
```

This stages the selected fixture, runs the migration script, then rewrites `golden_toml/<case>/` from the migrated temp workspace's `your_content/`.

Migration goldens use the same text line-ending normalization as build goldens.

## Test Case Structure

Each case is self-contained.

```text
test_cases/
  <case>/
    manifest.toml
    TEST_CASE.md
    your_content/
```

Rules:

- Keep all engine-facing fixture input under `your_content/`.
- Keep `manifest.toml` machine-readable and explicit; this is executable test input.
- Keep `TEST_CASE.md` human-readable; do not encode behavior there or treat it as test data.
- Keep focused cases small rather than using subset comparisons.
- For local review, any non-empty base subdirectory must match the test case name.
- Do not rely on root-level `your_content/`; it is ignored and only for local manual runs.

## Adding A Test Case

1. Create `test_cases/<case>/manifest.toml`.
2. Create `test_cases/<case>/TEST_CASE.md`.
3. Add a complete `test_cases/<case>/your_content/` fixture.
4. Run `python scripts/run_e2e.py refresh-build --case <case>`.
5. Inspect `golden_builds/<case>/`.
6. Run `python scripts/run_e2e.py check-build --case <case>`.
7. Run `venv\Scripts\python.exe -m pytest`.

## Baseline Case

The baseline case is a broad full-parity fixture. It should remain realistic and cover common legacy INI behavior.

Focused cases should not keep adding complexity to baseline by default. Prefer a new small independent case when validating a specific edge case or config combination.

## Explicit URL Override Case

`explicit-url-overrides` is the first focused case. It uses a tiny legacy INI fixture to verify that explicit `Comic domain` and `Comic subdirectory` settings override `GITHUB_REPOSITORY` inference.

## Blank Subdirectory Case

`blank-subdirectory` is a focused case for root-mounted output. It is the explicit exception to the case-name subdirectory rule and should be served from `golden_builds/blank-subdirectory/` directly.

## Manual Visual Review

For cases with a non-empty base subdirectory:

```powershell
cd golden_builds
python -m http.server 8000
# open http://localhost:8000/baseline/
# open http://localhost:8000/explicit-url-overrides/
```

For the blank-subdirectory case:

```powershell
cd golden_builds/blank-subdirectory
python -m http.server 8001
# open http://localhost:8001/
```

The local server root matters because generated pages use root-relative URLs.

## Future Checks

The manifest already has check flags for:

- `build`
- `migration`
- `migrated_build`

Harness support exists for all three flags.

- `build`: run `build_site.py` and compare `build/` to `golden_builds/<case>/`
- `migration`: run the migration script and compare migrated `your_content/` to `golden_toml/<case>/`
- `migrated_build`: run the migration script, then `build_site.py`, and compare `build/` to `golden_builds/<case>/`

Enable `migration` and `migrated_build` only when a case has reviewed TOML and build goldens.

## Structured Images Case

`structured-images` exercises flat and sectioned legacy page metadata, native TOML
`[[images]]`, image/page archive modes, Extra Comic identity, RSS, schema validation,
and migration parity.

In addition to byte-for-byte goldens, the generated-site contract suite validates
every `page_info_list.json` against the schema deployed in the matching build and
asserts cross-output structured-image semantics.
