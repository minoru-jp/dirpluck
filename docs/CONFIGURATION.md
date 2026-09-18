# dirpluck Configuration Guide

This document explains how to write a Configuration file in TOML. For exact field validation, pattern grammar, import resolution, and filesystem boundaries, see [SPECIFICATION.md](SPECIFICATION.md). For Configuration selection and CLI options, see [CLI.md](CLI.md).

## Basic shape

A Configuration represents one final archive intent. At minimum, define a source and an output.

```toml
[companion.notes]
path = "notes"
description = "Notes included in the package."
include = ["*.md"]

[output]
path = "artifacts/notes.zip"
if_exists = "overwrite"
```

Use a Target for a source that changes from run to run, and a Companion for a source whose path is fixed in the Configuration. Add Shared patterns, Cases, and Configuration imports when they are useful.

## About

Use `[about]` when the Configuration should describe its overall purpose or what the generated Archive represents. The table is optional; when present, it contains one non-empty `description`.

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
```

This description appears below the heading in the generated Archive README, above the per-source index. Across an import chain, dirpluck searches from the outermost Configuration inward and uses the first `[about].description` it finds. If none is defined, the README has no overall description. See [SPECIFICATION.md](SPECIFICATION.md) for the exact resolution rule.

## Path notation

Filesystem locations in a Configuration use `/` as the path separator regardless of the host OS. Backslash is not a path separator.

Relative paths are resolved from the base defined for each field. Absolute paths use an absolute-root form recognized by the host OS, written with `/` separators.

```text
# POSIX host
/opt/company/references

# Windows host
C:/Users/name/references
//server/share/references
```

An absolute path refers directly to that location, so a Configuration that uses one is less portable. `dirpluck` does not translate absolute-root notation from another OS, expand `~`, or interpolate environment variables.

This notation applies to filesystem-location fields such as Companion `path`, import `root`, and output `path` / `directory`. Fields intentionally defined as relative, such as include patterns and imported `configuration`, retain their own restrictions. See [SPECIFICATION.md](SPECIFICATION.md) for exact validation.

## Target

Use a Target when the same selection rules should be applied to source directories supplied through the CLI.

```toml
[target]
description = "The submission currently being reviewed."
include = ["documents", "metadata.json"]
include_if_exists = ["attachments"]
exclude = [".git/", "__pycache__/", "*.pyc"]
```

The concrete Target directory is not stored in the Configuration. The same Target selection is applied independently to one or more directories supplied by the CLI.

```console
dirpluck submissions/acme submissions/contoso
```

Do not supply positional `DIRECTORY` arguments for a Configuration with no Target.

## Companion

Use a Companion when the Configuration should fix a source directory. `path` may be relative or absolute.

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[companion.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
include = ["*.md"]
```

A relative `path` is resolved from the Configuration execution root associated with that Companion definition. It may use `..` to refer outside that root. An absolute `path` refers directly to a location on the host filesystem. In either case, the resolved Companion source directory itself becomes the selection boundary, so includes and symbolic links cannot escape it.

Define multiple Companions under different names. A Configuration may consist entirely of Companions. See [SPECIFICATION.md](SPECIFICATION.md) for exact archive-path and symbolic-link behavior.

## Selection

Targets, Companions, and Cases each carry an independent selection. A selection has a `description` and include candidates.

### `description`

Describe the role of the source in the extraction intent. The generated Archive README uses this description to explain the meaning of the archive path. Because the index does not add dirpluck-specific role labels such as Target or Companion, write a description that remains understandable to a recipient on its own rather than merely repeating a directory name.

```toml
description = "Reference material used to evaluate the submission."
```

### `include`

Use `include` for candidates that must exist.

```toml
include = ["report.pdf", "data/*.csv"]
```

### `include_if_exists`

Use `include_if_exists` for candidates whose absence is acceptable.

```toml
include_if_exists = ["generated/*.pdf", "coverage.xml"]
```

A selection may use both `include` and `include_if_exists`.

### `exclude`

Use `exclude` to remove names from areas already selected by include candidates.

```toml
exclude = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

Including a directory makes files below it candidates for collection. `dirpluck` does not automatically identify secret-like names, so broad directory selections should declare exclusions appropriate to the workspace.

### `if_empty`

For a selection containing only optional candidates, use `if_empty = "allow"` when selecting zero files is valid.

```toml
include_if_exists = ["generated/*.pdf"]
if_empty = "allow"
```

The default is `"error"`. Exact field-combination rules are in [SPECIFICATION.md](SPECIFICATION.md).

## Shared patterns

When several selections reuse the same include or exclude arrays, define a Shared pattern once and reference it by name.

```toml
[shared.include_patterns]
project-core = ["pyproject.toml", "src", "README.md"]

[shared.exclude_patterns]
python-dev = [".git/", ".venv/", "__pycache__/", "*.pyc"]

[target]
description = "The current project."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]
```

A Shared pattern affects only selections that reference it. References may be combined with direct `include`, `include_if_exists`, and `exclude` entries.

Shared-pattern name resolution across Configuration imports is defined in [SPECIFICATION.md](SPECIFICATION.md).

## Cases

Use a Case when the same source needs another complete selection.

```toml
[target]
description = "Normal review."
include = ["documents", "metadata.json"]

[target.case.audit]
description = "Audit review."
include = ["documents", "metadata.json", "records"]
```

```console
dirpluck submissions/acme --case audit
```

A Case is not a delta from the base selection. Write every include, exclude, and Shared-pattern reference needed by the Case in the Case itself.

Targets and Companions can define the same Case name so one CLI `--case` selects the corresponding variation. Exact fallback behavior for Companions is defined in [SPECIFICATION.md](SPECIFICATION.md).

## Configuration import

Use a Configuration import to reuse another Configuration as an inner layer.

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

`root` may be relative or absolute. A relative `root` is resolved from the directory containing the Configuration that declares the import; an absolute `root` refers directly to a location on the host filesystem. `configuration` remains a relative TOML file path inside the resolved import root.

The imported definitions and the current Configuration are composed into the Effective Configuration. Exact shadowing, chain, cycle, and Shared-pattern resolution rules are in [SPECIFICATION.md](SPECIFICATION.md).

If an imported Target remains in the Effective Configuration, its concrete Target directory still comes from CLI `DIRECTORY`; `dirpluck` does not infer it from the imported Configuration file's location.

To add a fixed source anchored at the immediate import root, define an import-root Companion overlay:

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The imported project itself."
include_if_exists = ["pyproject.toml", "src", "README.md"]
if_empty = "allow"
```

## Output

Every Configuration has an `[output]`. Use either a fixed path or a generated timestamped name.

### Fixed output

```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`path` may be relative to the current working directory or absolute. `if_exists` is either `"error"` or `"overwrite"`. Fixed output suits a workflow that intentionally maintains one known artifact.

### Generated output

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "snapshot"
```

`directory` may be relative to the current working directory or absolute. Generated output suits recurring snapshots and other workflows where each run should accumulate as a separate artifact. If the caller deliberately starts multiple runs in the same second, it may supply CLI `--sequence N`.

For exact filename layout, collision behavior, concurrent-write rules, and the handling of outputs in imported Configurations, see [SPECIFICATION.md](SPECIFICATION.md).

## Complete example

```toml
[about]
description = "Materials prepared for reviewing the current project."

[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[target.case.full]
description = "The project with all review material."
include_if_exists = ["README.md", "src", "tests", "docs"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck projects/example
dirpluck projects/example --case full --dry-run
```

For all CLI options and Configuration discovery, see [CLI.md](CLI.md). For exactly how this Configuration is resolved and validated, see [SPECIFICATION.md](SPECIFICATION.md).
