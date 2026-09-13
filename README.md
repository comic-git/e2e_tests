<!-- Audience: Human developers.
     Purpose: Human entry point for this repo. Short and navigational; links to docs instead of duplicating them.
     AGENTS.md is the AI entry point; this file is for humans. -->

# e2e_tests

`e2e_tests` is a local end-to-end harness for `comic_git_engine`.

It validates real engine behavior by staging realistic `your_content/` fixtures into a temporary host repo, running the engine, and comparing produced output against checked-in goldens.

## Quick Start

Install the harness dev dependencies, then run the pytest wrapper suite:

```powershell
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest
```

Pytest runs each enabled manifest check independently and reports disabled checks as skipped.

Browser tests are opt-in and use pinned local Decap packages:

```powershell
npm install
venv\Scripts\python.exe -m playwright install chromium
venv\Scripts\python.exe -m pytest -m browser
```

The lower-level harness CLI is available for targeted checks and golden refreshes. To run or refresh a specific case:

```powershell
python scripts/run_e2e.py check-build --case baseline
python scripts/run_e2e.py refresh-build --case baseline
```

To deliberately refresh every build-enabled golden and review the aggregate engine changes with Git:

```powershell
python scripts/run_e2e.py refresh-build --all
git diff -- golden_builds
```

The harness has three check lanes:

```powershell
python scripts/run_e2e.py check-build --all
python scripts/run_e2e.py check-migration --all
python scripts/run_e2e.py check-migrated-build --all
```

See [`docs/testing.md`](docs/testing.md) for the full harness workflow.

## Docs

| Doc                                              | Contents                                              |
|--------------------------------------------------|-------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)   | Harness structure, data flow, and design rationale    |
| [`docs/testing.md`](docs/testing.md)             | Running the harness, adding cases, refreshing goldens |
| [`docs/gotchas.md`](docs/gotchas.md)             | Known sharp edges and confusing behavior              |
| [`docs/roadmap.md`](docs/roadmap.md)             | Durable future work                                   |
| [`docs/documentation.md`](docs/documentation.md) | Docs structure and where new content belongs          |

## Key Folders

| Folder                             | Contents                                                      |
|------------------------------------|---------------------------------------------------------------|
| [`test_cases/build/`](test_cases/build/) | Golden-backed fixture inputs, manifests, and case docs  |
| [`test_cases/browser/`](test_cases/browser/) | Mutable browser fixtures tested with semantic assertions |
| [`golden_builds/`](golden_builds/) | Expected full built site output grouped by test case          |
| `golden_toml/`                     | Expected migrated `your_content/` output grouped by test case |
| [`tests/generated_site_contracts/`](tests/generated_site_contracts/) | Semantic public-contract checks over generated sites |
| [`scripts/`](scripts/)             | Local harness scripts                                         |
| `specs/`                           | Ignored scratch plans and temporary agent notes               |

Root-level `your_content/` and `build/` are ignored local artifacts. Checked-in fixture input belongs under the appropriate `test_cases/build/` or `test_cases/browser/` case.

For each test case, `manifest.toml` and `your_content/` define the executable input. `TEST_CASE.md` is required human reference material, but it is not parsed by the runner.

Text files in refreshed goldens are normalized to LF line endings for cross-platform stability. Binary files remain strict byte-for-byte comparison targets.

Golden builds are directly viewable with a local static server. For normal non-empty subdirectory cases, serve `golden_builds/` and open `/<case>/`. Blank-subdirectory cases are the exception; serve that case's golden folder directly and open `/`.
