<!-- Audience: AI agents and developers running or adding harness tests.
     Purpose: Explain how to run the harness, refresh goldens, and add test cases correctly. -->

# Testing

## Running Tests

Run commands from the `e2e_tests` repo root.

```powershell
# Validate the default baseline case
python scripts/run_e2e.py legacy-build

# Validate a named case
python scripts/run_e2e.py legacy-build --case baseline

# Keep the temp workspace for debugging
python scripts/run_e2e.py legacy-build --case baseline --keep-temp
```

`python` launches the harness script. The harness then defaults engine execution to `venv/Scripts/python.exe` when that venv exists.

## Refreshing Goldens

Refresh is deliberate and destructive for the selected golden output.

```powershell
python scripts/run_e2e.py refresh-build --case baseline
```

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
- Do not rely on root-level `your_content/`; it is ignored and only for local manual runs.

## Adding A Test Case

1. Create `test_cases/<case>/manifest.toml`.
2. Create `test_cases/<case>/TEST_CASE.md`.
3. Add a complete `test_cases/<case>/your_content/` fixture.
4. Run `python scripts/run_e2e.py refresh-build --case <case>`.
5. Inspect `golden_builds/<case>/`.
6. Run `python scripts/run_e2e.py legacy-build --case <case>`.

## Baseline Case

The baseline case is a broad full-parity fixture. It should remain realistic and cover common legacy behavior.

Focused cases should not keep adding complexity to baseline by default. Prefer a new small independent case when validating a specific edge case or config combination.

## Future Test Modes

The manifest already has mode flags for:

- `legacy_build`
- `migration`
- `toml_build`

Only `legacy_build` is implemented today. Migration and TOML-build checks should use the same principles: complete fixture input, explicit manifest inputs, temp workspace execution, and strict golden comparison.
