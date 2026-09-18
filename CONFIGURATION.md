# dirpluck Configuration

A dirpluck Configuration is a TOML file that describes an extraction intent. This document is the authoring guide: it explains how to choose Target and Companion sources, explicitly import another Configuration, write selections, define Cases, and set Output policy.

For an overview of where this model is useful, start with [README.md](README.md). For exact parser, matching, filesystem, Archive, and error semantics, use [SPECIFICATION.md](SPECIFICATION.md).

## Start with one extraction intent

Use one Root Configuration for one package you want to be able to reproduce. It may describe changing runtime subjects, fixed material, Companions already declared by another Configuration, Shared patterns imported from another Configuration, or a combination of them.

Cases coordinate selection changes inside one Configuration; they are not a profile stack. When you want to reuse Companion definitions or Shared patterns owned by another Configuration, import that Configuration explicitly instead of copying its source paths or pattern arrays into the parent.

A Configuration may contain:

```text
Configuration
├── shared                 optional, named reusable pattern sets
├── import.<name>          zero or more, root configuration only
│   └── companion.<name>  zero or more, root-owned companions inside import root
├── target                 optional, runtime-bound
├── companion.<name>       zero or more, configuration-bound
└── output                 exactly one
```

A Root Configuration must contain at least one local Target / Companion or one Configuration import. Within each import, the Companions declared by the imported Configuration and any `[import.<name>.companion.<name>]` tables declared by the Root Configuration must together provide at least one Companion. Configuration imports are one level deep: the imported Configuration cannot import another Configuration. If it also defines a Target, that Target is not used during the importing run.

## Configuration imports

Use a Configuration import when Companion definitions or Shared patterns owned by another Configuration should participate in the same Root intent. Instead of permitting arbitrary `../` paths on individual Companions, each import declares a separate execution root and the existing boundary rules continue to apply inside that root.

For example, when running from `workspace/dirpluck/`, this can import the Configuration for `shikumi` while using the whole `workspace/` directory as its root:

```text
workspace/
├── dirpluck/
├── shikumi/
│   └── dirpluck.toml
└── shikumi-devdoc/
```

```toml
[import.shikumi-stack]
root = ".."
configuration = "shikumi/dirpluck.toml"
case = "distribution"
```

The import name (`shikumi-stack` above) identifies the import in errors and the Archive index, and it is also the logical namespace for Companions under that import. An imported `[companion.devdoc]` and a Root-defined `[import.shikumi-stack.companion.project]` are identified logically as `shikumi-stack.devdoc` and `shikumi-stack.project`. The import name is not an Archive-path prefix.

### `root`

`root` is required. It is a directory path relative to the directory containing the Root Configuration file itself. Because importing another Configuration is the explicit mechanism for crossing the cwd boundary, `root` may contain `..`. Absolute paths and globs are not accepted. `/` is the canonical path separator, and absolute paths in Windows syntax are rejected regardless of the host OS. The resolved path must be an existing directory.

The resolved `root` becomes the imported Configuration's filesystem boundary. The Companions used by the import and their selected files may not resolve outside that root, including through symbolic links.

### `configuration`

`configuration` is required and is a relative TOML file path from the import root.

```toml
configuration = "shikumi/dirpluck.toml"
```

It must remain inside the import root. Absolute paths, `..`, and globs are not accepted. Import resolution does not search the cwd or `./dirpluck/`; it reads exactly the file named here.

The imported file is fully validated as a normal Configuration. Its `[shared.*]`, Target, Companion, Case, and `[output]` definitions are validated as definitions owned by that Configuration. During an importing run, however, only its Companions are used as sources. Its Target and `[output]` are not executed.

The imported Configuration's `[shared.include_patterns]` and `[shared.exclude_patterns]` are also exposed to Root-owned selections under qualified names of the form `<import-name>.<pattern-name>`. For example, an exclude Shared pattern named `python-dev` under import `shikumi-stack` is referenced from the Root side as `shikumi-stack.python-dev`. The import name is therefore a namespace for both Companions and Root-visible Shared patterns.

### Add a Companion inside the import root

The Root Configuration may explicitly define an additional source inside the import root as a Companion, even when the imported Configuration does not declare that source.

```toml
[import.shikumi-stack.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

`path` is relative to the import root. As with ordinary Companions, absolute paths and `..` are not accepted. Unlike ordinary Companions, this form permits `path = "."` so the import root itself can be treated as a Companion.

Because this Companion definition is owned by the Root Configuration, its Shared pattern references resolve in the Root-visible Shared-pattern namespace. Root-local Shared patterns use local names, while imported Shared patterns use qualified names such as `<import>.<pattern>`. Companions declared by the imported Configuration continue to resolve their own Shared patterns by local name inside that imported Configuration; importing them does not rewrite those references.

If the imported Configuration already declares `[companion.project]`, the Root Configuration may not also declare `[import.shikumi-stack.companion.project]`, because both would have the logical name `shikumi-stack.project`. A Root-local `[companion.project]` or `other.project` from another import is a different logical name and may coexist.

### `case`

Specify `case` only when the imported Companions should use a named Case:

```toml
case = "distribution"
```

If omitted, every Companion in the import namespace uses its base selection. If supplied, at least one Companion from either the imported Configuration or the Root-defined import Companions must define that Case. A Companion with the same Case uses it, while another Companion without that Case falls back to its base selection. The imported Target Case is not used. A CLI `--case` selected for the Root Configuration does not propagate into imports; each `[import.<name>]` chooses its Companion Case independently.

### Imports are one level deep

Only the Root Configuration may declare Configuration imports. If an imported Configuration itself contains `[import.<name>]`, the run fails. This avoids cycles, depth-dependent Case propagation, and complex Configuration graphs.

A Root Configuration may contain only Configuration imports and no local Target or Root-local Companion. It still owns the final `[output]`. Each import namespace must contain at least one Companion from either the imported Configuration or a Root-defined `[import.<name>.companion.<name>]`.

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

When the Root Configuration defines a Target, at least one CLI `DIRECTORY` is required:

```console
dirpluck submissions/acme
```

The same Target definition may be applied to several runtime directories in one run:

```console
dirpluck submissions/acme submissions/contoso submissions/globex
```

TOML still contains only one Target definition; the CLI list does not create separately configured Targets. Runtime Target directories must resolve to distinct directories. If the Root Configuration does not define a Target, supplying any positional `DIRECTORY` is an error. CLI positional directories are never assigned to imports. If an imported Configuration defines `[target]`, that definition is used only when the Configuration is run directly, not when it is imported.

A Target may define a default selection, named Cases, or both. If it has Cases but no default `[target]` selection, the Configuration must be invoked with `--case`.

## Companions

Use a Companion for a source directory that belongs to the extraction intent itself and therefore has a fixed path in TOML.

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

The Companion name (`guidelines` above) identifies the source inside its logical namespace. A Root-local `[companion.<name>]` has logical name `<name>`, while every Companion under an import has logical name `<import>.<companion>` regardless of whether it comes from the imported Configuration or the Root Configuration. `path` is relative to the execution root assigned to that Companion. Root-local Companions use the process cwd; imported and Root-added import Companions use the corresponding import root.

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

## Shared patterns

When several selections need the same include or exclude pattern set, define a named Shared pattern. Only the pattern array is shared, not a complete selection definition. Root-owned selections may use Shared patterns defined locally or Shared patterns exposed by an explicitly imported Configuration.

Define include patterns under `[shared.include_patterns]`:

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]
```

Define exclude patterns under `[shared.exclude_patterns]`:

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
    "*.pyc",
    ".DS_Store",
]
```

Each named array is validated with the normal include or exclude pattern grammar for its table. A named array cannot be empty. Defining a Shared pattern does not apply it to any source; selections must reference it explicitly.

Reference a shared include set as required candidates with `include_pattern_refs`, or as optional candidates with `include_if_exists_pattern_refs`. Reference a shared exclude set with `exclude_pattern_refs`.

```toml
[target]
description = "The current project for normal development work."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]

[target.case.all]
description = "All project files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Shared references may be combined with a selection's own `include` / `include_if_exists` / `exclude`. Referenced Shared patterns are expanded first, followed by patterns written directly on the selection. A duplicate effective pattern is a Configuration error.

Cases do not inherit the base selection, so they do not inherit its Shared pattern references either. In the example above, both the base selection and `all` explicitly reference `python-dev`. This is not Case inheritance; two independent selections are referencing the same named pattern set.

### Reference Shared patterns from an imported Configuration

Shared patterns from an imported Configuration are referenced from the Root side as `<import-name>.<pattern-name>`.

Suppose `shikumi/dirpluck.toml` contains:

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

After declaring the import:

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

a Root-owned Target, Root Companion, or `[import.<name>.companion.<name>]` selection may reference that set as `shikumi.python-dev`:

```toml
[target]
description = "The current project."
include_if_exists = ["*"]
exclude_pattern_refs = ["shikumi.python-dev"]
if_empty = "allow"
```

Imported include sets use the same qualification rule in `include_pattern_refs` or `include_if_exists_pattern_refs`. Include and exclude namespaces remain distinct.

A Companion declared by the imported Configuration itself still resolves Shared patterns by local name inside that imported Configuration. Its references are not rebound to qualified Root names, and imported Shared-pattern tables are not merged with Root-local tables.

If a Root-local Shared pattern name is exactly the same string as a qualified imported Shared-pattern name of the same kind, the reference would be ambiguous and the Configuration is rejected rather than choosing an implicit precedence.


## Selection fields

Every Target selection, Companion base selection, and Case selection has its own `description` and file-selection fields. Shared patterns may be referenced instead of direct patterns or combined with them.

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

`if_empty = "allow"` cannot be combined with required `include` patterns or required Shared includes referenced through `include_pattern_refs`.

## Cases

A Case is one flat, named selection variation shared by the Configuration. At most one Case name can be active in a run.

Cases replace a source's selection as a whole. They do not inherit from or merge with the base selection. Shared pattern references on the base selection are not inherited either, so a Case that needs the same Shared pattern must reference the same name itself.

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

A Companion may define the same Case name when its own selection should change with the selected Case within that Configuration:

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
[shared.exclude_patterns]
workspace-noise = [
    ".git/",
    "__pycache__/",
    "*.pyc",
]

[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
include_if_exists = ["attachments"]
exclude_pattern_refs = ["workspace-noise"]

[target.case.audit]
description = "The submission with additional records required for audit."
include = [
    "documents",
    "metadata.json",
    "records",
]
include_if_exists = ["attachments"]
exclude_pattern_refs = ["workspace-noise"]

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

## Complete example: import another Configuration

Assume the following Root Configuration is run from `workspace/dirpluck/`:

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.pyc",
]

[target]
description = "The dirpluck project being prepared for development context."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[import.shikumi-stack]
root = ".."
configuration = "shikumi/dirpluck.toml"

[import.shikumi-stack.companion.project]
path = "shikumi"
description = "The shikumi project itself, added by the Root Configuration."
include_if_exists = ["pyproject.toml", "src", "README.md"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[output]
path = "development-context.zip"
if_exists = "overwrite"
```

If `workspace/shikumi/dirpluck.toml` declares `shikumi-devdoc` as a Companion like this, that Companion path is resolved from the import root, `workspace/`:

```toml
[target]
description = "The project selected when this Configuration is run directly."
include_if_exists = ["*"]
if_empty = "allow"

[companion.shikumi]
path = "shikumi"
description = "The shikumi wheel used by related projects."
include = ["dist/shikumi-*.whl"]

[companion.devdoc]
path = "shikumi-devdoc"
description = "The shikumi-devdoc wheel used for document generation."
include = ["dist/shikumi_devdoc-*.whl"]

[output]
path = "shikumi-context.zip"
if_exists = "overwrite"
```

The importing run does not create or overwrite `shikumi-context.zip`; its only final artifact is the Root Configuration's `development-context.zip`.

```console
dirpluck . --dry-run
dirpluck .
```

The Root Configuration's Target comes from CLI `.`. The imported Configuration's Target is not used. The Archive plan includes imported `shikumi-stack.shikumi` / `shikumi-stack.devdoc` Companions plus the Root-defined `shikumi-stack.project` Companion.

## Configuration discovery

By default, dirpluck looks for `dirpluck.toml`. With `--config NAME`, the `.toml` suffix may be omitted:

```console
dirpluck DIRECTORY [DIRECTORY ...] --config review
```

Configuration discovery is limited to the current working directory and `./dirpluck/`. A name found in both places is ambiguous and is rejected rather than resolved by precedence. An import `root` is then resolved relative to the directory containing the selected Root Configuration file itself. Imports do not perform Configuration discovery; `configuration` names one relative TOML file inside the import root.

Use:

```console
dirpluck --configs
```

to list discoverable Configurations.

## Exact syntax and execution rules

This guide is intentionally about writing and structuring Configurations. [SPECIFICATION.md](SPECIFICATION.md) is the authority for exact include and exclude pattern grammar, case-sensitive matching, symbolic-link boundaries, Archive path behavior, dry-run semantics, and validation errors.
