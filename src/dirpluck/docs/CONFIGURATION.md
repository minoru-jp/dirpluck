# dirpluck Configuration

A dirpluck Configuration is a TOML file that describes one extraction intent. This document is the authoring guide: it explains how to choose Target and Companion sources, write selections, define Cases, and set Output policy.

For an overview of where this model is useful, start with [README.md](README.md). For exact parser, matching, filesystem, Archive, and error semantics, use [SPECIFICATION.md](SPECIFICATION.md).

## Start with one extraction intent

Use one Configuration for one package you want to be able to reproduce. A Configuration may describe a changing runtime subject, fixed material from several directories, or both.

If two workflows need different source membership, different Companion paths, or different Output policy, write two Configurations. Cases are for coordinated selection variations inside one intent, not for turning one Configuration into a stack of profiles.

Every Configuration contains:

```text
Configuration
├── target                 optional, runtime-bound
├── companion.<name>       zero or more, configuration-bound
└── output                 exactly one
```

At least one Target or Companion is required.

## Target

Use a Target when one or more source directories of the same role should be supplied at invocation time. The Configuration contains one `[target]` definition that declares how files are selected, but it does not store those runtime directory paths. When several directories are supplied, the same Target selection is applied independently to each one.

```toml
[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
```

A Configuration that defines a Target requires at least one `DIRECTORY` on the CLI:

```console
dirpluck submissions/acme
```

The same Target definition may be applied to several runtime directories in one run:

```console
dirpluck submissions/acme submissions/contoso submissions/globex
```

TOML still contains only one Target definition; the CLI list does not create separately configured Targets. Runtime Target directories must resolve to distinct directories. If the Configuration does not define a Target, supplying any positional `DIRECTORY` is an error. This keeps runtime input aligned with what the Configuration actually declares.

A Target may define a default selection, named Cases, or both. If it has Cases but no default `[target]` selection, the Configuration must be invoked with `--case`.

## Companions

Use a Companion for a source directory that belongs to the extraction intent itself and therefore has a fixed path in TOML.

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

The Companion name (`guidelines` above) identifies that source inside the Configuration. `path` is relative to the current working directory and names one concrete directory.

Companions do not require a Target. A Configuration may be made entirely of fixed Companions:

```toml
[companion.contracts]
path = "records/contracts"
description = "Contracts included in the project snapshot."
include = ["*.pdf"]

[companion.minutes]
path = "records/meetings"
description = "Meeting records included in the project snapshot."
include = ["*.md"]

[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

Run it without a positional directory:

```console
dirpluck --config project-snapshot
```

## Selection fields

Every Target selection, Companion base selection, and Case selection has its own `description` and file-selection fields.

### `description`

`description` is required and must be non-empty. Write the role of that source or selection in the extraction intent rather than merely repeating its directory name.

```toml
description = "Reference material used to evaluate the submission."
```

The generated Archive index carries these descriptions forward, so purpose-specific meaning should be stated here rather than inferred later from filenames.

### `include`

Use `include` for entries that must be present. Every pattern must match during a normal build.

```toml
include = [
    "report.pdf",
    "data/*.csv",
]
```

A missing required pattern is an error. Use this when absence means the resulting package would no longer represent the declared intent.

### `include_if_exists`

Use `include_if_exists` for known candidates whose absence is acceptable.

```toml
include_if_exists = [
    "generated/*.pdf",
    "coverage.xml",
]
```

This is useful for generated outputs, optional attachments, or files that exist only in some runs.

A selection may use both `include` and `include_if_exists` when it has a required core plus optional additions.

### `exclude`

Use `exclude` to filter names only inside areas already selected by `include` or `include_if_exists`.

```toml
exclude = [
    ".git/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    ".DS_Store",
    "*.pyc",
]
```

Selecting a directory with `include` or `include_if_exists` recursively collects files below it. dirpluck does not automatically recognize hidden files or secret-like names, so broad selections should add `exclude` rules appropriate to the workspace. The list above is illustrative, not an exhaustive secret filter.

`exclude` is not another include language and does not select files by itself. Exact supported pattern forms are defined in [SPECIFICATION.md](SPECIFICATION.md).

### `if_empty`

The default is:

```toml
if_empty = "error"
```

For a selection that contains only `include_if_exists`, you may explicitly allow a zero-file result:

```toml
include_if_exists = ["generated/*.pdf"]
if_empty = "allow"
```

`if_empty = "allow"` cannot be combined with required `include` patterns.

## Cases

A Case is one flat, named selection variation shared by the Configuration. At most one Case name can be active in a run.

Cases replace a source's selection as a whole. They do not inherit from or merge with the base selection.

### Target Case

```toml
[target]
description = "The current project for normal development work."
include = ["src", "pyproject.toml"]

[target.case.review]
description = "The current project with review material included."
include = ["src", "tests", "pyproject.toml"]
```

```console
dirpluck project-a project-b --case review
```

When a Target exists, it defines the valid Case namespace. Selecting `review` requires `[target.case.review]` to exist, and that same Case selection is applied to every runtime Target directory supplied in the command.

### Companion Case and fallback

A Companion may define the same Case name when its own selection should change with that Configuration-wide Case:

```toml
[companion.framework]
path = "framework"
description = "The framework used by the project."
include = ["dist/framework-*.whl"]

[companion.framework.case.review]
description = "The framework distribution and source used during review."
include = ["dist/framework-*.whl", "src"]
```

If `--case review` is active, this Companion uses its `review` selection. A Companion without `[companion.<name>.case.review]` remains present and falls back to its base selection.

### Cases without a Target

Companion-only Configurations may also use Cases:

```toml
[companion.documents]
path = "documents"
description = "Current documents in the snapshot."
include = ["current/*.md"]

[companion.documents.case.archive]
description = "Current and historical documents in the archival snapshot."
include = ["current/*.md", "history/*.md"]

[companion.assets]
path = "assets"
description = "Assets included in every snapshot."
include = ["*.png"]
```

```console
dirpluck --config snapshot --case archive
```

Here `documents` uses its `archive` Case while `assets` falls back to base. Without a Target, a selected Case must be defined by at least one Companion.

Case names are flat. Do not combine Cases, repeat `--case`, or create nested forms such as `case.review.case.security`.

Cases change selections only. If a variation needs a different Companion set, Companion path, or Output policy, use another Configuration.

## Output

Every Configuration has one `[output]` table. It uses exactly one of two forms: **fixed output**, which updates one known path, or **generated output**, which creates a new timestamped name for each run. The two forms cannot be mixed.

### Fixed output

```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`path` is a concrete path below the current working directory. `if_exists` is required:

- `error` refuses to replace an existing output.
- `overwrite` replaces it only after a new Archive has been written successfully.

Use fixed output when the workflow intentionally maintains one known artifact. Only fixed output can permit replacement.

### Generated output

Use generated output when runs are meant to accumulate, such as snapshots or recurring packages:

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

The filename has one fixed layout:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

The example above produces a name such as:

```text
project-20260916-011623-review.zip
```

`prefix` and `suffix` are optional. `timestamp = true` is required. The local process time is captured once at the start of the build; custom timestamp formats and general naming templates are not supported.

If a script deliberately starts more than one run in the same second, the caller can supply one positive integer:

```console
dirpluck --config project-snapshot --sequence 3
```

The sequence is placed immediately after the timestamp:

```text
project-20260916-011623-3-review.zip
```

`--sequence` is not automatic numbering. dirpluck never inspects existing outputs to infer the next number, and the number segment is omitted when it is not supplied. `--sequence` is invalid with fixed output.

Generated output does not accept `if_exists`. If the generated name already exists when the run checks its destination, the run fails. dirpluck neither auto-numbers nor auto-renames it. dirpluck does not coordinate concurrent writes to the same output path, so overlapping invocations must be given distinct names by the caller.

The CLI does not temporarily replace the Output form. If two workflows need different output behavior, represent them as different Configurations. `--sequence` only fills the runtime number slot provided by generated naming; it does not replace the naming rule.

## Complete example: changing Target with fixed references

```toml
[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
include_if_exists = ["attachments"]

[target.case.audit]
description = "The submission with additional records required for audit."
include = [
    "documents",
    "metadata.json",
    "records",
]
include_if_exists = ["attachments"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[companion.guidelines.case.audit]
description = "Guidelines and audit checklist used for an audit review."
include = ["*.md", "audit-checklist.pdf"]

[companion.reference]
path = "reference-data"
description = "Reference data used by every review type."
include = ["*.csv"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

Normal review, with one or more runtime Targets:

```console
dirpluck submissions/acme submissions/contoso
```

Audit variation:

```console
dirpluck submissions/acme submissions/contoso --case audit
```

The same Target selection is applied to both runtime directories. Under `audit`, every runtime Target and `guidelines` switch to the `audit` selection; `reference` has no `audit` Case and therefore uses its base selection.

## Complete example: fixed-source snapshot

```toml
[companion.documents]
path = "records/documents"
description = "Documents that define the current project state."
include = ["*.pdf", "*.md"]

[companion.decisions]
path = "records/decisions"
description = "Recorded decisions that explain the current project state."
include = ["*.md"]

[companion.generated]
path = "generated"
description = "Generated material available at snapshot time."
include_if_exists = ["*.pdf", "*.zip"]
if_empty = "allow"

[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "snapshot"
```

```console
dirpluck --config project-snapshot
```

This Configuration is complete without a Target because all of its sources are fixed Companions. Each run adds a name such as `project-YYYYMMDD-HHMMSS-snapshot.zip`; a script that intentionally launches multiple runs in the same second can supply `--sequence N`.

## Configuration discovery

By default, dirpluck looks for `dirpluck.toml`. With `--config NAME`, the `.toml` suffix may be omitted:

```console
dirpluck DIRECTORY [DIRECTORY ...] --config review
```

Configuration discovery is limited to the current working directory and `./dirpluck/`. A name found in both places is ambiguous and is rejected rather than resolved by precedence.

Use:

```console
dirpluck --configs
```

to list discoverable Configurations.

## Exact syntax and execution rules

This guide is intentionally about writing and structuring Configurations. [SPECIFICATION.md](SPECIFICATION.md) is the authority for exact include and exclude pattern grammar, case-sensitive matching, symbolic-link boundaries, Archive path behavior, dry-run semantics, and validation errors.
