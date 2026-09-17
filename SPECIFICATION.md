# dirpluck Specification

This document defines the exact operational semantics of dirpluck's supported CLI and Configuration format. README explains the uses and design model, while CONFIGURATION.md explains how to write the TOML. Use this document when exact behavior matters.

## 1. Public surface

The compatibility-supported public interface is the `dirpluck` CLI together with the TOML Configuration format described here. Python modules under the package are implementation internals unless a Python API is explicitly documented in the future.

## 2. Configuration discovery

Configuration discovery is non-recursive and limited to two locations relative to the current working directory (cwd):

- the cwd itself;
- `./dirpluck/`.

Without `--config`, the candidate filename is `dirpluck.toml`. With `--config NAME`, `NAME` is treated as a filename, not an arbitrary path; `.toml` may be omitted.

Zero matching candidates is an error. If the same candidate filename exists in both discovery locations, the result is ambiguous and is rejected. Neither location has implicit precedence.

`--configs` lists discoverable candidates. At the cwd root, only TOML files that resemble a dirpluck Configuration are listed; a candidate is recognizable when it has `[output]` and at least one of `[target]` or `[companion]`. TOML files directly under `./dirpluck/` are listed as candidates. Duplicate filenames across both locations are marked ambiguous.

## 3. Top-level Configuration shape

Only the following forms are accepted:

```text
[shared.include_patterns]
[shared.exclude_patterns]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

Unknown keys are errors at every validated level.

A Configuration represents one extraction intent and contains:

- zero or more named Shared patterns;
- zero or one logical Target definition;
- zero or more Companions;
- at least one source in total, meaning a Target and/or one or more Companions;
- exactly one Output definition.

The Target is runtime-bound: one logical `[target]` definition may be instantiated by one or more directory arguments from the CLI. Every runtime Target uses the same selected Target definition. Each Companion is configuration-bound: its directory is fixed by its `path`.

Shared patterns reuse named pattern arrays only; they are not complete shared selection definitions. There are no bundles, Configuration inheritance, Configuration merging, or CLI selection overrides.

`[shared.include_patterns]` and `[shared.exclude_patterns]` are each optional. If `[shared]` is present, at least one of these tables must be present, and every present table must contain at least one named array. Each name must be a non-empty string and each array must contain at least one string. Include arrays are validated using the include pattern grammar and exclude arrays using the exclude pattern grammar when the Configuration is loaded. Merely defining a Shared pattern does not apply it to any selection.

## 4. Case semantics

A Case is one flat, named selection variation for the Configuration. A run has zero or one active Case. Case names cannot be combined or nested, and `--case` may be specified at most once.

A Case changes selections only. It never adds or removes a Target or Companion, changes a Companion `path`, or changes Output policy.

When no Case is selected:

- the Target, when present, uses `[target]`; if the Target has no default `[target]` selection, the run is an error;
- every Companion uses its base `[companion.<name>]` selection.

When a Case is selected and a Target exists:

- `[target.case.<name>]` with the selected name is required;
- a Companion uses `[companion.<companion-name>.case.<name>]` when present;
- otherwise that Companion falls back to its base `[companion.<companion-name>]` selection;
- a Companion Case whose name is not defined by the Target is a Configuration error because it is unreachable.

When a Case is selected and no Target exists:

- the selected Case name must be defined by at least one Companion;
- each Companion with that Case uses its Case selection;
- every other Companion falls back to its base selection.

Every Target Case and Companion Case is a complete selection definition. It does not inherit from or merge with the source's base selection. Shared pattern references on the base selection are not inherited either; a Case that needs the same Shared pattern must explicitly reference the same name.

## 5. Target and Companion semantics

The Target is optional. When `[target]` and/or `[target.case.<name>]` is present, the Configuration defines one logical runtime-bound Target rule. No Target `path` is stored in TOML, and TOML cannot define multiple separately configured Targets.

If the Configuration defines a Target, the CLI requires one or more positional `DIRECTORY` values. The selected Target definition is applied independently to every supplied directory, in CLI order. All runtime Target directories must resolve to distinct actual directories. If the Configuration does not define a Target, supplying any positional `DIRECTORY` is an error.

`[target]`, when present, is the default Target selection used when `--case` is omitted. A Target may omit `[target]` and define only named Cases; in that form, invoking without `--case` is an error.

Every runtime Target directory must exist at execution time and is resolved according to the filesystem boundary rules below.

Each `[companion.<name>]` must define one concrete cwd-relative `path`, a non-empty `description`, and one complete base selection. A Companion is always part of the Configuration's source set, whether or not a Target exists, and its directory must exist at execution time.

A Companion may additionally define zero or more complete Case selections under `[companion.<name>.case.<case-name>]`. Case selection follows the Configuration-wide rules in section 4. A missing Companion Case never removes the Companion; it causes that Companion to use its base selection.

## 6. Selection definition

Every `[target]`, `[target.case.<name>]`, `[companion.<name>]`, and `[companion.<name>.case.<case-name>]` selection requires a non-empty `description` and at least one `include` / `include_if_exists` equivalent candidate, supplied either directly or through Shared references.

Direct `include` and `include_if_exists` fields, when present, must each contain at least one string. Shared-reference fields, when present, must each contain at least one Shared name. Duplicate references within one field are rejected.

### `include` and `include_pattern_refs`

`include` directly declares required include patterns. `include_pattern_refs` names entries from `[shared.include_patterns]` and expands those arrays as required include patterns. During a normal invocation, every resulting required pattern must match at least one filesystem entry. A zero-match required pattern is an error.

### `include_if_exists` and `include_if_exists_pattern_refs`

`include_if_exists` directly declares optional include patterns. `include_if_exists_pattern_refs` names entries from `[shared.include_patterns]` and expands those arrays as optional include patterns. They use the same grammar as required includes, but zero matches are accepted and add nothing to the selection.

The same shared include pattern set may be referenced through `include_pattern_refs` in one selection and `include_if_exists_pattern_refs` in another. Required versus optional behavior is decided by the referring selection, not by the Shared definition.

### `exclude` and `exclude_pattern_refs`

`exclude` directly declares exclusion patterns. `exclude_pattern_refs` names entries from `[shared.exclude_patterns]` and expands those arrays as exclusions. Both forms filter entity names only inside areas already selected by includes and never select a path by themselves.

### Expansion and duplicates

Shared references are expanded in reference-array order, followed by direct patterns of the same kind. Referencing an unknown Shared name is a Configuration error. After expansion, duplicate effective patterns within required includes, optional includes, or excludes are Configuration errors. The same normalized pattern appearing in both the required and optional include sets is also a Configuration error.

### `if_empty`

`if_empty` defaults to `error`.

`if_empty = "allow"` is valid only for an optional-only selection with no required include patterns after Shared references have been expanded. When the final selected file count is zero and empty results are allowed, the source directory may be represented as an explicit empty directory entry in the Archive.

## 7. Include pattern grammar

Include patterns are relative POSIX-style paths from the Target or Companion directory. Absolute paths, `.` as the whole pattern, and `..` traversal are rejected. Backslashes are normalized to `/` before validation.

Each path element may contain at most one `*`. The wildcard matches zero or more characters inside exactly one filesystem name and never crosses a path separator. Consequently, the number of path levels written in the Configuration remains fixed.

Examples:

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

If the final matched entry is a file, that file is selected. If it is a directory, files below it are collected recursively subject to exclusions and symbolic-link rules. Hidden files, repository metadata, environment files, private keys, and other secret-like names receive no implicit filtering; if they are inside the selected tree and are not excluded, they are handled like ordinary files.

Multiple matches are all selected. Pattern matching is case-sensitive independently of the operating system.

`**`, `?`, character classes (`[]`), and `!` are not supported. dirpluck does not interpret versions, modification times, or other metadata when several entries match.

## 8. Exclude pattern grammar

Exclude patterns match a single entity name rather than a relative path.

A pattern ending in `/` applies to directory names. A pattern without `/` applies to file names.

Supported forms are:

```text
name      exact match
name*     prefix match
*name     suffix match
*name*    contains match
```

A bare `*`, `*/`, internal-wildcard forms such as `foo*bar`, `**`, `?`, character classes, `!`, backslashes, and path separators are rejected.

## 9. Filesystem boundaries and symbolic links

The cwd is the execution boundary.

The Target directory, when present, and every Companion directory must resolve within the cwd. Paths that escape through symbolic links are rejected.

Selected files must resolve within their own Target or Companion directory. A file symlink that resolves outside that directory is rejected.

During recursive directory collection, directory symlinks are never followed. A directory symlink resolving outside its source directory is an error. A directory symlink resolving inside the source directory is ignored to prevent cycles and duplicate traversal.

The Target may be the cwd itself by passing `.`. Archive paths still preserve the cwd directory's actual basename as their first component rather than flattening files into the ZIP root.

## 10. Archive planning and paths

Selected files preserve their actual cwd-relative filesystem paths in the ZIP.

If multiple sources resolve to the same actual directory, their selections are unioned by real Archive path. A physical file is written once even if multiple declared purposes select it.

The Archive root contains a generated `README.md` that acts only as a purpose-neutral index of the resolved plan. It records the active Case (`default` when none is selected), participating directories, configured descriptions, selected Configuration locations, directory sources, selection counts, and relevant empty-result policy. Its fixed wording does not name the generating tool or prescribe a downstream use; purpose-specific meaning comes only from the configured descriptions.

Archive planning is deterministic: selected entries and generated output are ordered consistently rather than depending on incidental filesystem enumeration order.

## 11. Output semantics

`[output]` is required and defines exactly one of two forms: fixed output or generated output. Fields from the two forms cannot be mixed.

### Fixed output

```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

Fixed output requires both `path` and `if_exists`. `path` must be one concrete cwd-relative path below the cwd; absolute paths, `..`, and glob syntax are rejected. Parent directories are created when necessary. An Output path that resolves outside the cwd through a symbolic link is rejected.

`if_exists` accepts only:

- `error`: fail without modifying an existing output;
- `overwrite`: write the new ZIP to a temporary file in the destination directory and replace the existing output only after the new Archive is complete.

For `error`, dirpluck checks that the destination does not exist before the build and checks again immediately before final placement. The ZIP is completed in a temporary file in the same output directory before it is moved to the final path. dirpluck does not provide locking or coordination between asynchronous or parallel invocations; concurrent writes to the same output path are unsupported.

### Generated output

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

Generated output requires `directory` and `timestamp = true`; `prefix` and `suffix` are optional. `path` and `if_exists` are not allowed.

`directory` must be one concrete cwd-relative directory inside the cwd. `.` may be used for the cwd itself. Absolute paths, `..`, and glob syntax are rejected. The directory is created when necessary, and symbolic-link escapes outside the cwd are rejected.

`prefix` and `suffix` must each be one non-empty portable filename fragment. `.`, `..`, path separators, control characters, and the characters `< > : " | ? *` are rejected.

Generated filenames use exactly this layout:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

The timestamp is the local process time, captured once at the start of the build. Custom timestamp formats, variable expansion, and general naming templates are not supported.

`N` comes from CLI `--sequence N` and must be an integer greater than or equal to 1. If it is not supplied, the sequence segment is omitted. dirpluck never inspects existing output names to infer the next number and never auto-renames a collision. `--sequence` is valid only with generated output and may be specified at most once.

If a generated destination already exists when dirpluck checks it, the run fails. Generated output has no overwrite policy. dirpluck does not synchronize competing processes, so callers that may run concurrently must ensure distinct output paths, for example by assigning distinct `--sequence N` values.

With either form, the output file itself cannot be selected as one of the Archive inputs.

## 12. Dry-run semantics

`--dry-run` uses the same source resolution, Case resolution, selection, and Archive planning logic as a normal invocation but does not create or modify the output.

Missing required `include` patterns are shown as `[missing]`. Missing optional patterns are shown as `[optional missing]`.

A source whose final selection is empty is shown as `empty, allowed` when permitted or `empty, would error` when a normal invocation would fail for emptiness.

Configuration contradictions, Target/DIRECTORY mismatches, invalid paths, unknown Case names, and `--sequence` on fixed output remain errors during dry-run. Because dry-run does not write the Archive, it does not resolve a timestamped filename or apply existing-output collision behavior.

## 13. CLI forms

Build a Configuration that defines a Target with one or more runtime directories:

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

Build a Companion-only Configuration:

```console
dirpluck --config NAME
```

Build with one named Case:

```console
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
```

or, for a Companion-only Configuration:

```console
dirpluck --config NAME --case NAME
```

Use another discoverable Configuration:

```console
dirpluck DIRECTORY [DIRECTORY ...] --config NAME
```

Preview without writing:

```console
dirpluck DIRECTORY [DIRECTORY ...] --dry-run
```

List discoverable Configurations:

```console
dirpluck --configs
```

For generated output, explicitly distinguish same-second runs when needed:

```console
dirpluck --config NAME --sequence N
```

`N` must be an integer greater than or equal to 1, and `--sequence` may be specified at most once. It is an error with fixed output.

Display the installed version:

```console
dirpluck --version
```

There is no `build` subcommand and no CLI option for temporarily overriding selection rules or the Output form. `--sequence` only supplies the optional runtime number slot defined by generated naming.
