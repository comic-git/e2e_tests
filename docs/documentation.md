<!-- Audience: Developers and AI agents adding or modifying documentation.
     Purpose: Explain where durable docs, case docs, and temporary planning notes belong. -->

# Documentation Guide

## Philosophy

Docs should explain intent, decisions, and sharp edges that are not obvious from the code.

- Keep durable docs accurate and concise.
- Prefer linking over duplicating.
- Do not preserve temporary implementation plans as permanent docs.
- Document why the harness is shaped a certain way, not every line of what the code does.

## Structure

```text
docs/
  architecture.md       - harness structure and design rationale
  testing.md            - commands, adding cases, refreshing goldens
  gotchas.md            - sharp edges and silent failure modes
  roadmap.md            - durable future work
  documentation.md      - this guide

test_cases/build/<case>/
  TEST_CASE.md          - golden-backed case intent and coverage

test_cases/browser/<case>/
  TEST_CASE.md          - mutable browser case intent and known behavior

specs/
  ...                   - ignored scratch plans and temporary design notes
```

## What Goes Where

| Content type                            | Location                         |
|-----------------------------------------|----------------------------------|
| Overall harness structure and decisions | `docs/architecture.md`           |
| How to run or add harness cases         | `docs/testing.md`                |
| Sharp edges and confusing behavior      | `docs/gotchas.md`                |
| Future work that should remain visible  | `docs/roadmap.md`                |
| Build case intent and coverage          | `test_cases/build/<case>/TEST_CASE.md` |
| Browser case intent and coverage        | `test_cases/browser/<case>/TEST_CASE.md` |
| Temporary agent plans and drafts        | `specs/`                         |

## Format

Persistent docs should start with:

```html
<!-- Audience: who reads this doc.
     Purpose: what this doc is for. -->
```

This makes it easier for agents and developers to decide which docs are relevant before reading everything.
