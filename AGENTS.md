<!-- This file is the AI entry point for this repo. It orients AI agents operating here and sets
     universal behavioral rules that apply regardless of task or workflow.
     Keep this file short; durable details belong in docs/. -->

# AGENTS.md

## Project Overview

`e2e_tests` is a local end-to-end harness for `comic_git_engine`.

It stages checked-in fixture inputs from `test_cases/<case>/your_content/` into minimal temporary host repos, runs the real engine, and compares generated output against checked-in goldens.

This repo is a harness repo, not a normal `comic_git` host repo. Root-level `your_content/` and `build/` are disposable ignored artifacts.

## Behavioral Guardrails

- Keep checked-in engine-facing user content under `test_cases/<case>/your_content/`.
- Treat each test case `your_content/` like real user content, not mock-only data.
- Do not change fixture content casually; fixture changes redefine the golden contract.
- Keep test cases independent and explicit. Do not add fixture inheritance unless there is a concrete maintenance problem.
- Keep `TEST_CASE.md` human-readable. Do not parse it or treat it as behavior source of truth.
- Source of truth for behavior is `manifest.toml`, `your_content/`, and the matching golden output.
- Run builds and migrations in temporary workspaces, not directly from checked-in fixture data.
- `refresh-build` fully rewrites the selected golden. Review refreshed output before committing.

## Key Docs

| Doc                                              | Contents                                              |
|--------------------------------------------------|-------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)   | Harness structure, data flow, and design rationale    |
| [`docs/testing.md`](docs/testing.md)             | Running the harness, adding cases, refreshing goldens |
| [`docs/gotchas.md`](docs/gotchas.md)             | Known sharp edges and confusing behavior              |
| [`docs/roadmap.md`](docs/roadmap.md)             | Durable future work                                   |
| [`docs/documentation.md`](docs/documentation.md) | Docs structure and where new content belongs          |

## Current Baseline

- test case: `baseline`
- input fixture: `test_cases/baseline/your_content/`
- manifest: `test_cases/baseline/manifest.toml`
- case docs: `test_cases/baseline/TEST_CASE.md`
- golden build: `golden_builds/baseline/`

The baseline case exercises GitHub Pages inference by omitting `Comic subdirectory` and `Comic domain` from `comic_info.ini` and setting `GITHUB_REPOSITORY` in the manifest.
