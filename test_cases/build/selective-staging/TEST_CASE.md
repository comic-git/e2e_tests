# Selective staging

This independent fixture tests a publication boundary that spans discovery,
source thumbnail caching, page copying, generated metadata, navigation, and RSS.
Unit tests cannot prove that all of these outputs agree in an actual host build.

`tests/test_selective_staging.py` stages this content into disposable hosts and
runs the public CLI. It validates each generated JSON document against the schema
deployed by the same build, checks output links/files against independently
specified eligible pages, and checks combined RSS across the main comic and two
Extra Comics whose base directories are nested. Shared page names deliberately
exercise comic-scoped RSS identity.

The main comic uses legacy INI with image auto-discovery and a TOML text-only
page. Extra Comics use native TOML. Each comic has a scheduled folder and either
a draft without a metadata file, plus loose files under its comics root. Non-comic
assets, hidden source files, site_root exceptions, and postprocess-created hidden
files exercise the separate auxiliary-copy and final-filter paths.

The test varies publish-all and explicit allowlists, checks invalid and incomplete
metadata errors, and repeats builds. Source snapshots permit only expected thumbnail
cache writes. This is a semantic-only build case: the three golden check flags
are disabled deliberately. No golden files are added or refreshed.

Multiline `Hidden paths` values are also read from actual INI files without a
command-line override, using both inline-first and all-indented layouts with LF
and Windows CRLF line endings.
