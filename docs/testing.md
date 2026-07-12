<!-- Audience: AI agents and developers running or adding harness tests.
     Purpose: Explain how to run the harness, refresh goldens, and add test cases correctly. -->

# Testing

## Running Tests

Run commands from the `e2e_tests` repo root.

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

## Refreshing Goldens

Refresh is deliberate and destructive for the selected golden output.

```powershell
python scripts/run_e2e.py refresh-build --case baseline
```

Refresh one case at a time. `refresh-build --all` is intentionally unsupported so broad golden rewrites stay deliberate.

This command:

1. Builds the selected case in a temp host repo.
2. Deletes `golden_builds/<case>/`.
3. Copies the fresh build output into `golden_builds/<case>/`.

Only refresh a golden after confirming the new output is the intended behavior.

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
- Keep `manifest.toml` machine-readable and explicit.
- Keep `TEST_CASE.md` human-readable; do not encode behavior there.
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
7. Run `python scripts/run_e2e.py check-build --all`.

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

Only `build` is implemented today. Migration and migrated-build checks should use the same principles: complete fixture input, explicit manifest inputs, temp workspace execution, and strict golden comparison.
