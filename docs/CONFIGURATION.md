# dirpluck Configuration Guide

This document is a guide to writing Configuration files in TOML. For exact validation of each field, base composition, pattern grammar, filesystem boundaries, Output collisions, and related rules, see [SPECIFICATION.md](SPECIFICATION.md). For Configuration selection and CLI options, see [CLI.md](CLI.md). For the trust boundary around Configurations and filesystem operations, see [TRUST.md](TRUST.md).


## Configuration document

Save a Configuration as a document whose filename ends in `.dirpluck`; its contents use TOML syntax. A `.toml` filename is not accepted as a dirpluck Configuration.

```text
default.dirpluck
review.dirpluck
configs/common.dirpluck
```

`default.dirpluck` is the special filename used automatically from the runtime cwd only when `--config` is omitted. Select a differently named Configuration or one in another directory explicitly with `--config PATH`. Relative CLI paths are resolved from the cwd, while relative filesystem paths inside a Configuration are resolved from that Configuration file's directory. Paths that select or reference Configuration documents follow the host OS's normal filesystem semantics, including symbolic links and Windows directory junctions. Relative paths are anchored to the selected or referenced document path's directory rather than to the physical location of a link target. See [CLI.md](CLI.md) and [SPECIFICATION.md](SPECIFICATION.md) for the exact selection rules. A Base Configuration does not need the special default name; `[about].base` references a concrete `.dirpluck` path.

A `.dirpluck-inv` file is a separate Invocation Template document type, not a Configuration. It does not participate in the Configuration schema or base chain. See [CLI.md](CLI.md) for authoring and selecting Invocation Templates.

## Basic form

A Configuration represents one final Archive intent. When Targets are selected at runtime, use `pluck` and `scope`; use `always` for sources fixed by the Configuration.

```toml
[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive", "tmp-*"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[pluck]` is the Pluck applied to Targets, `[scope]` / `[scope.<name>]` are the Scopes in which Targets are searched for, and `[always.<name>]` defines Always sources. When same-named source roots need to remain distinct in the Archive, a Namespace can be used. Add Shared patterns, Cases, and a Base Configuration as needed.

## About

`[about]` declares information about the Configuration itself. It may contain `description` and `base`.

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
base = "../common/common.dirpluck"
```

`description` is optional and describes the Configuration as a whole. It is displayed directly below the heading in the generated Archive README. If multiple Configurations in a base chain define a description, the first definition found from the outermost Configuration inward is used.

`base` is also optional and names one Base Configuration on which this Configuration is based. A Configuration may specify only `base` without a `description`. If `[about]` is present, at least one of these fields must be present.

See [SPECIFICATION.md](SPECIFICATION.md) for base-chain composition and cycle detection.

## Path notation

Filesystem locations in a Configuration use `/` as the separator regardless of the host OS. Backslashes are not path separators. On Windows, write paths such as `C:/...` or `//server/share/...` with `/` separators.

A relative filesystem path is resolved from the **directory containing the Configuration file in which that field is written**. The runtime cwd is not substituted as the path-resolution base.

```text
project/default.dirpluck
    [always.notes]
    path = "../notes"
        -> resolved from project/
```

Absolute paths are written using `/` separators in a form recognized as an absolute root by the host OS.

```text
# POSIX host
/opt/company/references

# Windows host
C:/Users/name/references
//server/share/references
```

An absolute path directly references that location and therefore reduces Configuration portability. `dirpluck` does not convert absolute-root notation for another OS, expand `~`, or interpolate environment variables.

This rule applies at least to `about.base`, `scope.<name>.path`, `always.<name>.path`, `output.path`, and `output.timestamp.path`. Not only `about.base`, which references another Configuration document, but also explicitly configured source-root locations such as named Scopes and Always sources follow the host OS's normal filesystem semantics and may include symbolic links or Windows directory junctions. Resolving an alias used as an explicit root is separate from the rule that recognized link-like entries are not selected during automatic traversal below that root. Values that are not filesystem locations, such as patterns and CLI Target references, follow their own rules. See [SPECIFICATION.md](SPECIFICATION.md) for exact validation.

## Pluck

`[pluck]` defines what to extract from Targets selected for the current run. It does not contain a source path itself; Targets are resolved from Scopes and CLI Target references.

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents", "metadata.json"]
may = ["attachments"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

When multiple Targets are selected in one run, the same Pluck selection is applied independently to each Target.

A Configuration with no Pluck does not use positional Target references.

## Scope

A Scope is a place where Targets are searched for. Configurations use an always-present default Scope and may add named Scopes.

The default Scope always exists and always uses the directory containing the Root Configuration file as its search root. The `[scope]` table configures only the default Scope's optional `ignore` and `namespace`; it has no `path` field. Omitting `[scope]`, or writing an empty `[scope]`, is equivalent to `ignore = []` with no Namespace. A `[scope]` written in a Base Configuration applies when that Configuration itself is used as the Root; it is not inherited by an outer Root Configuration.

```toml
[scope]
ignore = ["archive", "tmp-*"]
```

A named Scope has a `path`.

```toml
[scope.work]
path = "../work"
ignore = ["archive", "tmp-*"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*"]
```

`ignore` names directories directly under the Scope that should not be treated as Target candidates. Its role is different from the file-selection `pluck.ignore`.

CLI Target references have four forms combining unnamed or named Scope selection with one Target or all Targets:

```text
NAME        -> one Target from the default Scope
SCOPE/NAME  -> one Target from a named Scope
/           -> all Targets from the default Scope
SCOPE/      -> all Targets from a named Scope
```

Expansion includes only eligible directories directly under the Scope and is not recursive.

Along a base chain, only named Scopes are overlaid by name. A named Scope in an outer Configuration replaces a same-named Scope, while differently named Scopes coexist. The default Scope is not inherited from a Base Configuration; it always belongs to the Root Configuration. Therefore a Base Configuration's `[scope].ignore` / `namespace` is not used by an outer Root, but remains valid when that Base Configuration itself is used as the Root. An inherited named Scope root remains anchored to the Configuration in which the Scope was declared and is not rebased to an outer Configuration.

A Scope may optionally specify `namespace = "<name>"`. This does not change where Targets are searched for. Instead, it prefixes the Archive root of every Target obtained from that Scope with a separately defined Namespace. A Namespace is applied whenever it is configured, not only when a collision happens.

Whether a named Scope path is currently available on the filesystem is checked only when that Scope is actually used by a Target reference. A named Scope that points to an unmounted or otherwise missing location does not prevent a run that uses only another Scope. The named Scope root location itself may contain a symbolic link or Windows directory junction. After that root is resolved, link-like entries discovered automatically directly under the Scope are not selected or expanded as Targets. See [SPECIFICATION.md](SPECIFICATION.md) for exact rules on duplicate roots, Namespace references, and Target resolution.

## Namespace

A Namespace is an Archive-only prefix used to place source roots distinctly when they would otherwise resolve to the same Archive path. Define Namespaces as named empty tables:

```toml
[namespace.work]

[namespace.external]
```

The Namespace name itself becomes one directory name in the Archive. In the current schema, `[namespace.<name>]` has no fields. This keeps the declaration small while leaving the table available for future Namespace-specific policy.

Scopes and Always sources reference Namespace names explicitly:

```toml
[namespace.work]
[namespace.external]

[scope.work]
path = "/srv/work"
namespace = "work"

[always.docs]
path = "../docs"
namespace = "external"
description = "External documentation."
must = ["*.md"]
```

If `work/project` has source root `project/`, it is placed at `work/project/`. If an Always source would normally have source root `docs/`, the example above places it at `external/docs/`. A source without a Namespace keeps its source root as its Archive root.

If different resolved sources still produce the same final Archive root, `dirpluck` fails rather than silently merging them. A Namespace is an explicit way to avoid that collision, but it does not guarantee uniqueness by itself; two sources may still collide if they use the same Namespace and the same source root.

When at least one Namespace is used, the generated Archive README explains that Namespace directories are Archive-only and not part of the original source path. Each source uses its final Archive root as a heading, and namespaced sources identify the Namespace and Source root separately as metadata.

## Always

`[always.<name>]` fixes a source directory in the Configuration and makes it participate on every run. Its `path` may be relative or absolute.

```toml
[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[always.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
must = ["*.md"]
```

A relative `path` is resolved from the directory containing the Configuration file in which the definition is written. It may use `..` to reference an outer directory. An absolute `path` directly references a location on the host filesystem. An explicitly configured Always root location may contain a symbolic link or Windows directory junction, and the referenced directory is used as the source root. The Archive source-root name is taken from the location written in the Configuration rather than being replaced by the physical target directory's name.

The resolved source directory itself is the selection boundary. Allowing an alias for that explicit root does not enable link traversal inside the source. Entries recognized as symbolic links or Windows directory junctions during automatic Selection traversal are not selected, and their targets are not followed.

An Always source's Selection is evaluated independently of the Target Pluck. Even when the same physical file also exists under a Target, the Target's `ignore` rules and Selection result do not change the Always source's Selection. If both sources select the same physical file for different Archive paths, both entries are included. When selected files from an Always source physically overlap selected files from a Target, the generated Archive README records the Target-side Archive root and overlap count in the Always source section.

Define multiple Always sources with different names. A Configuration with only Always sources and no Pluck is also valid.

## Selection

Pluck, Always sources, and Cases each contain an independent Selection. A Selection uses `must`, `may`, `ignore`, and optionally `allow_empty`; use `description` only when you want to attach a human-readable explanation.

### `description`

Describe the role the source plays in the extraction intent. In the generated Archive README, this description explains the meaning of the archive path.

```toml
description = "Reference material used to evaluate the submission."
```

`description` is optional. Omitting it does not change Selection semantics. When present, it must be a non-empty string and appears as the body of that source's section in the generated Archive README, after the source heading and file count. Multi-line descriptions are kept as section content rather than being compressed into a table cell.

### `must`

Candidates that are required to exist and are included when present.

```toml
must = ["report.pdf", "data/*.csv"]
```

If a pattern matches nothing, the Selection does not succeed.

### `may`

Candidates that are included when present but whose absence is not an error.

```toml
may = ["generated/*.pdf", "coverage.xml"]
```

`must` and `may` can be used together in one Selection.

### `ignore`

Use `ignore` for entries that should not be plucked from areas already selected as candidates by `must` or `may`. A normal string continues to match a file or directory **name**.

```toml
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

When only one concrete location should be excluded, use a one-element nested array whose string begins with `./`. This is a path reference relative to the Selection root.

```toml
ignore = [
    ["./tests/fixtures/big.bin"],
    ["./src/generated/"],
]
```

For Pluck, `./` means the current Target root. For an Always source, it means that Always source root. A trailing `/` marks a directory path; without the trailing `/`, the reference is a file path. Dirpluck does not infer file-versus-directory meaning from the current filesystem state. Path references must stay inside the Selection root and do not accept `..`, absolute paths, globs, or backslashes.

Name patterns, Shared ignore references, and path references are combined as one set of exclusion conditions. It is valid for several conditions to match the same entry. A directory matching either a directory name ignore or a directory path reference is excluded before traversal, and its contents are not inspected. Evaluation order is not part of the semantics.

`ignore` takes precedence over diagnostics based on an entry's filesystem type: once an entry is ignored, it is treated as handled rather than as evidence for a symbolic-link, Windows-junction, or special-entry diagnostic. A `must` pattern that matches only ignored entries therefore fails as an ordinary unsatisfied `must`.

Recognized non-ignored symbolic links or Windows directory junctions are neither `must` / `may` selection candidates nor recursive traversal targets and are not included in the Archive. Other non-ignored filesystem entries that are neither regular files nor regular directories, such as FIFOs, sockets, and devices, are also not archived. If `must` matches only such special entries, the error explains that those entries are not selectable; `may` treats them as optional missing. Selections do not add implicit ignores based on content or names. See [TRUST.md](TRUST.md) for the trust boundary when running Configurations and for handling broad selections.

### `allow_empty`

Use this for a Selection containing only `may` candidates when zero final files should still be valid.

```toml
may = ["generated/*.pdf"]
allow_empty = true
```

The default is `false`. `allow_empty = true` cannot be combined with `must`.

## Shared patterns

When the same pattern set is used by multiple Selections, define it as a named Shared pattern. Shared patterns use the same three namespaces as Selections: `must`, `may`, and `ignore`.

```toml
[shared.must]
project = ["src", "pyproject.toml"]

[shared.may]
docs = ["README.md", "docs"]

[shared.ignore]
python-noise = ["__pycache__/", "*.pyc"]
```

A normal string in a Selection array is a direct pattern. In `must` and `may`, a one-element nested array is a Shared reference. In `ignore`, a one-element nested array is a Shared reference when it contains a plain name, or a Selection-relative path reference when the string begins with `./`.

```toml
[pluck]
description = "The current project."
must = [
    "LICENSE",
    ["project"],
]
may = [
    ["docs"],
]
ignore = [
    ".git/",
    ["python-noise"],
]
```

The referenced namespace is determined by the field containing the reference. `must = [["project"]]` refers to `shared.must.project`; references in `may` use `shared.may`; `ignore = [["python-noise"]]` refers to `shared.ignore.python-noise`. Only an `ignore` nested-array string beginning with `./`, such as `ignore = [["./tests/fixtures/"]]`, refers to a Selection-relative path instead of the Shared namespace.

Nested arrays such as `[]`, `["a", "b"]`, and `[123]` are invalid references. In `must` and `may`, nested arrays are reserved for Shared references. `ignore` reserves the `./` prefix inside a nested array for path references, without changing the syntax of ordinary direct-string patterns.

See [SPECIFICATION.md](SPECIFICATION.md) for name resolution and duplicate validation along a base chain.

## Cases

Use a Case to provide another complete Selection for the same source.

```toml
[pluck]
description = "Normal review."
must = ["documents", "metadata.json"]

[pluck.case.audit]
description = "Audit review."
must = ["documents", "metadata.json", "records"]
```

```console
dirpluck acme --case audit
```

A Case is not a delta applied to the base Selection. Write all required `must`, `may`, `ignore`, Shared references, and `allow_empty` values in the Case itself.

If Pluck and an Always source both have the same Case name, the same CLI `--case` selects the corresponding variation. See [SPECIFICATION.md](SPECIFICATION.md) for exact Case semantics, including fallback when an Always source does not define the selected Case.

## Base Configuration

Reference a Base Configuration with `base` in `[about]` when reusing an existing Configuration as the foundation of another.

```toml
[about]
base = "../common/common.dirpluck"
```

`base` references one Configuration file. If that Configuration has another `base`, the result is a linear base chain. There is no fixed maximum base-chain depth.

Relative filesystem paths in each Configuration are always resolved from the directory containing that Configuration file itself. A Scope or Always-source path inherited from a Base Configuration is not rebased to the location of an outer Configuration. The default Scope has no relative-path field and always uses the Root Configuration file's directory as its root.

[SPECIFICATION.md](SPECIFICATION.md) defines composition of Pluck, Always, Scope, and Shared patterns, description resolution, cycle detection, and Output handling. A Base Configuration may omit Output. A Root Configuration used with `--preview` or Runtime Output may also omit it; a normal build without Runtime Output must declare its own fixed or timestamp Output directly.

## Output

Output is optional on a Configuration by itself. A Base Configuration that only provides shared definitions may omit it, and a Root Configuration used with `--preview` or Runtime Output may also omit it. A normal build without Runtime Output must directly declare exactly one of two modes on the Root Configuration: fixed mode, in which the user chooses the final filename, or timestamp mode, in which `dirpluck` generates a filename from a timestamp. Output from a Base Configuration is not inherited.

### Fixed Output

```toml
[output]
path = "artifacts/review.zip"
overwrite = false
```

`path` is a concrete output file path including the filename. A relative path is resolved from the directory containing the Configuration file in which this `[output]` is written.

`overwrite` controls whether an existing output may be replaced and defaults to `false`. Output files are created with the same permission semantics as ordinary newly created files, so POSIX systems apply the process `umask`. Even with `overwrite = true`, the mode of the file being replaced is not inherited. `prefix` and `suffix` are not used in fixed mode.

### Timestamp Output

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` specifies the output directory and ends in `/` to indicate directory notation. A relative path is resolved from the directory containing the Configuration file in which this definition is written.

The filename is generated in this form:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

`prefix` and `suffix` are specific to timestamp mode. Use CLI `--sequence N` when multiple runs in the same second need to be distinguished intentionally. When CLI `--here`, trailing-`/` `--output`, or Python `output=` requests automatic Runtime Output, these `prefix` / `suffix` values are reused as the naming rule, but the configured timestamp-output directory is not. A policy that gives every ZIP entry the same mtime is not a Configuration field; set it at runtime with CLI `--archive-mtime` or Invocation Template `archive_mtime`.

### Writable destination

Output forms are limited so that the write boundary can be determined statically from the Configuration alone. For fixed Output, the boundary is the exact file path. For timestamp Output, it is the specified directory tree.

Output definitions in the same base chain cannot intrude on one another's write boundaries. See [SPECIFICATION.md](SPECIFICATION.md) for overlap rules for each fixed/timestamp combination.

## Complete example

```toml
[about]
description = "Materials prepared for reviewing the current project."
base = "../common/common.dirpluck"

[shared.ignore]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [["python-dev"]]
allow_empty = true

[pluck.case.full]
description = "The project with all review material."
may = ["README.md", "src", "tests", "docs"]
ignore = [["python-dev"]]
allow_empty = true

[scope]
ignore = ["archive"]

[scope.projects]
path = "/srv/projects"
ignore = ["archive", "tmp-*"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

```console
dirpluck projects/example
dirpluck projects/example --case full --preview
dirpluck projects/
```

For all CLI options and Configuration / Invocation Template selection, see [CLI.md](CLI.md). For the exact way this Configuration is resolved and validated, see [SPECIFICATION.md](SPECIFICATION.md).
