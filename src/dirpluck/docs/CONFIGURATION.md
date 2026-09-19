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

[target.location.work]
path = "/srv/work"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`[about].description` is an optional description of the Archive as a whole. If several imported Configurations define it, the first value found from the outermost Configuration inward is used and appears before the index table in the generated Archive README.

Review selections before creating an Archive that will be shared. `dirpluck` does not infer which files are sensitive; explicitly exclude material that should not be collected.

```toml
exclude = [".git/", ".env*", "*.pem", "*.key"]
```

This is only an example. See the bundled `TRUST.md` for the trust model and filesystem responsibilities.

The concrete Target directory is selected by a positional CLI `TARGET`. `[target.location.<name>]` maps a logical prefix such as `work/project` to a filesystem directory. `work/` expands every direct child directory of the `work` location and is an error if that location is undefined. Arguments without a location prefix resolve from the current working directory; `./work/project` explicitly bypasses location lookup. A Companion fixes its directory with `path` in the Configuration. Filesystem locations use `/` as the separator, and Target-location / Companion paths may be relative or absolute. Relative paths are resolved from the corresponding Configuration execution root.

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

For pattern grammar, import shadowing, Case semantics, filesystem boundaries, and output collisions, see `docs/CONFIGURATION.md` and `docs/SPECIFICATION.md` in the source distribution for the same release. The trust model is in the bundled `TRUST.md`, and the bundled `CLI.md` is the compact CLI reference.
