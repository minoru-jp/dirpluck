# Current-implementation characterization tests

These tests protect canonical behavior while the 1.0 internals are being replaced, but
they currently depend on private parser, configuration, source-resolution, selection,
archive, or output boundaries.

They are therefore **REWRITE** tests rather than stable public-interface tests. When a
private boundary is replaced, rewrite the affected tests against the new focused unit
boundary or move the resulting public scenario into `tests/contract/`. Do not preserve a
private class/function solely to keep this directory unchanged.

The subdirectories follow the intended replacement pipeline:

- `input_compilation/`: Configuration / Invocation parsing, value grammar, Base / Shared
  composition, and other tests expected to move onto the typed input compiler.
- `resolution/`: Case consumption, Scope / Target resolution, source construction, and
  strict entry-type behavior that currently depends on private normalization / resolution models.
- `collection/`: filesystem Selection behavior and traversal safety.
- `archive_output/`: Archive planning, ZIP metadata, README derivation, and Output
  writing policy.

Canonical grammar and semantics represented here remain authoritative unless the
canonical specification explicitly changes them.
