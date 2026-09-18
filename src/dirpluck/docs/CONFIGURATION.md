# dirpluck Configuration Quick Reference

This is the compact TOML reference included in the wheel.

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

The concrete Target directory comes from CLI `DIRECTORY`. A Companion fixes its directory with `path` in the Configuration.

Selections can use:

- `description`: the role of the source or selection;
- `include`: candidates that must exist;
- `include_if_exists`: candidates whose absence is allowed;
- `exclude`: names removed from already selected areas;
- `if_empty = "allow"`: permit zero files for an optional-only selection;
- `include_pattern_refs`, `include_if_exists_pattern_refs`, `exclude_pattern_refs`: references to Shared patterns.

Define reusable patterns under `[shared.include_patterns]` or `[shared.exclude_patterns]`. Define named variations as complete selections under `[target.case.<name>]` or `[companion.<name>.case.<name>]`.

Import another Configuration with:

```toml
[import.base]
root = ".."
configuration = "base/dirpluck.toml"
```

Output may also use the generated form with `directory`, `timestamp = true`, and optional `prefix` / `suffix`:

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

For pattern grammar, import shadowing, Case semantics, filesystem boundaries, output collisions, and other details, see `docs/CONFIGURATION.md` and `docs/SPECIFICATION.md` in the source distribution for the same release. The bundled `CLI.md` is the compact CLI reference.
