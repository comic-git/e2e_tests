<!-- Audience: Human developers.
     Purpose: Human entry point for this repo. Short and navigational; links to docs instead of duplicating them.
     AGENTS.md is the AI entry point; this file is for humans. -->

# e2e_tests

`e2e_tests` is a local end-to-end harness for `comic_git_engine`.

It validates real engine behavior by staging realistic `your_content/` fixtures into a temporary host repo, running the engine, and comparing produced output against checked-in goldens.

## Quick Start

```powershell
python scripts/run_e2e.py check-build
```

The default case is `baseline`. To run or refresh a specific case:

```powershell
python scripts/run_e2e.py check-build --case baseline
python scripts/run_e2e.py refresh-build --case baseline
```

To run every build-enabled case:

```powershell
python scripts/run_e2e.py check-build --all
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

| Folder                             | Contents                                                   |
|------------------------------------|------------------------------------------------------------|
| [`test_cases/`](test_cases/)       | Checked-in fixture inputs, manifests, and case docs        |
| [`golden_builds/`](golden_builds/) | Expected full built site output grouped by test case       |
| `golden_toml/`                     | Future expected TOML migration output grouped by test case |
| [`scripts/`](scripts/)             | Local harness scripts                                      |
| `specs/`                           | Ignored scratch plans and temporary agent notes            |

Root-level `your_content/` and `build/` are ignored local artifacts. Checked-in fixture input belongs under `test_cases/<case>/your_content/`.
