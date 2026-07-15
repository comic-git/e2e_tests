<!-- Audience: AI agents and developers planning future harness work.
     Purpose: Track durable next steps without preserving ephemeral specs as permanent docs. -->

# Roadmap

## Near Term

- Add focused independent test cases for additional high-value build behavior, such as RSS settings, transcript settings, future-page filtering, and theme overrides.
- Keep each focused fixture small enough that full golden comparison remains practical.
- Add `TEST_CASE.md` for every new case.

## Migration And TOML

- Implement legacy-to-TOML migration output in `comic_git_engine`.
- Enable migration checks case-by-case once the engine migration script is ready.
- Add `golden_toml/<case>/` snapshots for migrated fixture output.
- Use migrated-build parity checks to compare migrated builds against `golden_builds/<case>/`.
- Decide which focused cases should opt into migration coverage first.

## CI And Platform Support

- Add Linux-compatible temp engine linking or copying.
- Run the harness in CI after local behavior stabilizes.
- Decide whether CI should run every case by default or support tags for slower cases.

## Documentation

- Keep `docs/` for durable reference material.
- Keep `specs/` ignored for temporary plans and agent scratch work.
- Add decision records only if architectural choices become numerous enough that `architecture.md` is too crowded.
