# dirpluck Configuration Quick Reference

This is the compact TOML reference included in the wheel.

```toml
[about]
description = "Materials prepared for reviewing the current project."

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

`[about].description` is an optional description of the Archive as a whole. If several imported Configurations define it, the first value found from the outermost Configuration inward is used and appears before the index table in the generated Archive README.

The concrete Target directory comes from CLI `DIRECTORY`. A Companion fixes its directory with `path` in the Configuration. Filesystem locations in a Configuration use `/` as the separator, and Companion `path` may be relative or absolute. A relative Companion path is resolved from the corresponding Configuration execution root.

Selections can use:

- `description`: the role of the source or selection, used to explain it in the archive index;
- `include`: candidates that must exist;
- `include_if_exists`: candidates whose absence is allowed;
- `exclude`: names removed from already selected areas;
- `if_empty = "allow"`: permit zero files for an optional-only selection;
- `include_pattern_refs`, `include_if_exists_pattern_refs`, `exclude_pattern_refs`: references to Shared patterns.

Define reusable patterns under `[shared.include_patterns]` or `[shared.exclude_patterns]`. Define named variations as complete selections under `[target.case.<name>]` or `[companion.<name>.case.<name>]`.

Import another Configuration with the following form. `root` may be relative or absolute; `configuration` is a relative TOML path inside the import root.

```toml
[import.base]
root = ".."
configuration = "base/dirpluck.toml"
```

Output `path` / `directory` may also be relative or absolute. Output may use the generated form with `directory`, `timestamp = true`, and optional `prefix` / `suffix`:

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

For pattern grammar, import shadowing, Case semantics, filesystem boundaries, output collisions, and other details, see `docs/CONFIGURATION.md` and `docs/SPECIFICATION.md` in the source distribution for the same release. The bundled `CLI.md` is the compact CLI reference.
