# dirpluck Configuration

A dirpluck Configuration is a TOML file that describes an extraction intent. This document is the authoring guide: it explains how to choose Target and Companion sources, explicitly import another Configuration, write selections, define Cases, and set Output policy.

For an overview of where this model is useful, start with [README.md](README.md). For exact parser, matching, filesystem, Archive, and error semantics, use [SPECIFICATION.md](SPECIFICATION.md).

## Start with one extraction intent

Use one Root Configuration for one package you want to reproduce. It may import one other Configuration, and that Configuration may in turn import one more. dirpluck resolves this linear chain from the deepest layer outward and produces one effective Configuration.

A Configuration may contain:

```text
Configuration
├── shared                 optional, named reusable pattern sets
├── import.<name>          zero or one
│   └── companion.<name>  zero or more, overlays anchored to the import root
├── target                 optional, at most one per Configuration
├── companion.<name>       zero or more
└── output                 exactly one
```

Each Configuration may declare at most one `[import.<name>]`. There is no import-depth limit. A run fails only when a Configuration file already present in the active chain is encountered again, which is a cycle.

Target, Companion, and Shared-pattern definitions are resolved from the imported side toward the importing side. An outer definition with the same name shadows the inner definition as a whole. Target is a singleton, so the final effective Configuration contains at most one Target. Companions and Shared patterns accumulate under distinct names and are replaced only by an outer definition with the same name. `[output]` is not layered; only the outermost Root Configuration's Output is used.

## Configuration imports

Use `[import.<name>]` to place another Configuration one layer inside the current one. Import is no longer limited to Companions: Target, Companion, Shared-pattern, and Case definitions participate in effective name resolution. The imported `[output]` is still not executed.

For example:

```text
projects/
├── shikumi/
│   └── dirpluck.toml
└── context/
    └── dirpluck.toml
```

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"

[output]
path = "context.zip"
if_exists = "overwrite"
```

The Root Configuration itself may have no local Target or Companion as long as resolution of the import chain leaves at least one Target or Companion.

### `root`

`root` is required. It is a directory path relative to the directory containing **the Configuration file that declares that import**. It may contain `..`. Absolute paths and globs are rejected. `/` is the canonical separator, and Windows drive paths and UNC paths are treated as absolute regardless of the host OS.

The resolved root becomes the execution root and filesystem boundary of the directly imported Configuration. If that imported Configuration imports another one, its own `root` is resolved by the same rule relative to that Configuration file.

### `configuration`

`configuration` is a relative TOML file path from the import root.

```toml
configuration = "shikumi/dirpluck.toml"
```

It must remain inside the import root. Absolute paths, escaping `..`, and globs are rejected. Import resolution does not search the cwd or `./dirpluck/`; it reads exactly this file.

### Linear chains and cycles

An imported Configuration may itself contain one `[import.<name>]`.

```text
A imports B
B imports C
C imports D
```

There is no maximum depth. dirpluck keeps the resolved Configuration-file path for every active layer. If a file already present in the current chain is encountered again, the run fails with a cycle diagnostic that shows the chain.

```text
A -> B -> C -> A   error
```

Depth alone is never an error or warning.

### Name resolution and shadowing

Resolution starts at the deepest Configuration and proceeds outward.

- Target uses the singleton name `target`; an outer Target shadows the inner Target, including all of its Cases.
- Companions resolve by Companion name; an outer Companion with the same name replaces the inner definition as a whole, while different names coexist.
- Shared include patterns resolve by pattern name.
- Shared exclude patterns use a separate namespace and resolve by the same rule.

`include_pattern_refs`, `include_if_exists_pattern_refs`, and `exclude_pattern_refs` are resolved against the final effective Shared-pattern namespaces, not only against the layer where the selection was written. An outer layer may therefore provide or override a Shared pattern referenced by an inner source. A reference that remains unresolved after the full chain is composed is a Configuration error.

The import name identifies the link for diagnostics and Archive indexing. It is not an automatic namespace prefix for Companion or Shared-pattern names.

### Add or override a Companion inside the import root

`[import.<name>.companion.<companion-name>]` remains available when the importing layer needs a Companion whose `path` is relative to the immediate import root.

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

This definition participates in normal Companion resolution under the name `project`. It can shadow an imported `[companion.project]`. The same Configuration may not define both `[companion.project]` and `[import.shikumi.companion.project]`.

Its `path` is relative to the immediate import root. `path = "."` is allowed to select the import root itself. Absolute paths, `..`, and globs are rejected.

### Target resolution

If a Target survives into the effective Configuration, one or more CLI `DIRECTORY` arguments are required regardless of which Configuration layer defined it. The Target selection definition is resolved through the Configuration chain, while each runtime Target directory is resolved from CLI input inside the Root Configuration's execution root.

This allows an imported Configuration to provide the Target selection rules while the importing run chooses the concrete runtime directory. dirpluck does not infer a Target directory from the imported Configuration file's location.

### Case

`[import.<name>].case` is not used. After the Configuration chain is resolved, a single CLI `--case` is applied to the effective Configuration. Shadowing a Target or Companion also replaces all Cases owned by that source.

## Target

Each Configuration may define at most one Target. A Target stores its selection rules but no fixed source path.

```toml
[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
```

Across a Configuration chain, an outer Target shadows the inner Target as a complete definition. The effective Configuration therefore contains at most one Target.

If the effective Configuration contains a Target, at least one CLI `DIRECTORY` is required regardless of that Target's origin layer, and the same Target selection is applied independently to every supplied directory.

```console
dirpluck submissions/acme submissions/contoso
```

An imported Target follows the same rule: its selection definition may survive layering, but its runtime directory still comes from CLI `DIRECTORY`. If the effective Configuration has no Target, positional directories are rejected.

A Target may define a base selection, named Cases, or both. If it defines Cases but no base `[target]`, `--case` is required.

## Companions

Use a Companion for a fixed-path source.

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

Companion names are name-resolution keys across the Configuration chain. An outer Companion with the same name shadows the inner definition, including `path`, `description`, base selection, and Cases. Companions with different names all remain in the effective Configuration.

For an ordinary `[companion.<name>]`, `path` is relative to the execution root of the layer that owns that definition. For `[import.<name>.companion.<name>]`, it is relative to the immediate import root. A Companion that survives shadowing keeps the execution-root context associated with its definition.

A Configuration may still resolve to Companions only, in which case no positional directory is supplied.

## Shared patterns

Define named Shared patterns when multiple selections use the same include or exclude arrays.

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]

[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

Selections reference normal names:

```toml
[target]
description = "The current project."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]
```

Shared include and exclude patterns are resolved in separate namespaces from the deepest Configuration outward. An outer definition with the same name shadows the inner array. Import names are not required as prefixes for Shared-pattern references.

This also means that a source defined in an inner Configuration resolves its Shared-pattern references against the final effective namespace. An outer Configuration may provide or override a pattern referenced by that inner source. Conversely, a reference may be absent in the inner file and still be valid if an outer layer supplies it. If the name is still missing after the full chain is resolved, the Configuration is invalid.

Shared references may be combined with direct `include`, `include_if_exists`, and `exclude` entries. Cases do not inherit base selections, so a Case must repeat any Shared-pattern references it needs.

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

A single flat Case name may be active for the effective Configuration. Select it with CLI `--case` after the Configuration chain has been composed. There is no per-import Case setting.

If a source is shadowed by an outer layer, its base and all of its Cases are replaced together. Cases of sources that survive shadowing remain part of the effective Configuration regardless of which layer originally defined them.

When an effective Target exists, the selected Case must exist as `[target.case.<name>]`. Each Companion uses the same-named Case if present and otherwise falls back to its base selection. Without a Target, at least one effective Companion must define the selected Case.

A Case is a complete selection definition, not a delta from base, and does not inherit include/exclude fields or Shared-pattern references.

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

## Complete example: layer another Configuration

Assume the following Root Configuration is run from `workspace/dirpluck/`:

```toml
[target]
description = "The dirpluck project being prepared for development context."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.pyc",
]

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

If the imported `workspace/shikumi/dirpluck.toml` declares `shikumi-devdoc` as a Companion like this, its path is resolved from the import root `workspace/`:

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

The imported `shikumi-context.zip` is neither created nor overwritten during the Root run. Only the Root Configuration's `development-context.zip` is the final Output.

```console
dirpluck . --dry-run
dirpluck .
```

The Root Target binds to CLI `.` and shadows the imported Target, so the effective Target comes from the Root Configuration. After name resolution, the Companions named `shikumi` and `devdoc` come from the imported Configuration, while `project` comes from the Root import overlay. If the outer Target were removed, the imported Target definition would survive and would still bind to CLI `DIRECTORY` at runtime.

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
