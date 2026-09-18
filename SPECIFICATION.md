# dirpluck Specification

This document defines the exact operational semantics of dirpluck's supported CLI and Configuration format. README explains the uses and design model, while CONFIGURATION.md explains how to write the TOML. Use this document when exact behavior matters.

## 1. Public surface

The compatibility-supported public interface is the `dirpluck` CLI together with the TOML Configuration format described here. Python modules under the package are implementation internals unless a Python API is explicitly documented in the future.

## 2. Root Configuration discovery

CLI discovery for the Root Configuration is non-recursive and checks only these two locations relative to the cwd:

- the cwd itself
- the immediate `./dirpluck/` directory

When `--config` is omitted, the candidate filename is `dirpluck.toml`. With `--config NAME`, `NAME` is treated as a filename rather than an arbitrary path, and `.toml` may be omitted.

Zero matching candidates is an error. If the same candidate name exists in both locations, the result is ambiguous and rejected; neither location has implicit precedence.

`--configs` lists discoverable Root Configuration candidates. In the cwd it lists TOML files that structurally resemble dirpluck Configurations; under `./dirpluck/` it lists TOML candidates. Duplicate names across the two locations are reported as ambiguous.

Configuration imports do not use this discovery mechanism. Each import names one exact relative TOML file with `configuration` inside its import root.

## 3. Top-level Configuration shape

Only the following forms are accepted:

```text
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

Unknown keys are errors at every validated level.

A Configuration represents one extraction intent and contains:

- zero or more named Shared patterns;
- zero or more Configuration imports;
- zero or one logical Target definition;
- zero or more Companions;
- for a Root Configuration, at least one local source or Configuration import;
- exactly one Output definition.

The Target is runtime-bound: one logical `[target]` definition is instantiated by one or more CLI directories only when that Configuration is run as the Root Configuration. An imported Configuration's Target is validated as part of its schema but is not used by the importing run. Each Companion is configuration-bound: its directory is fixed by its `path` relative to that Configuration's execution root.

Shared patterns reuse named pattern arrays only; they are not complete shared selection definitions. Within one Configuration they are referenced by local name. A Root Configuration may also reference Shared patterns from an explicitly imported Configuration under qualified names of the form `<import>.<pattern>`. A Configuration import explicitly reuses Companions and Shared patterns declared by another complete Configuration. It is not Configuration inheritance or merging, and there are no CLI selection overrides.

`[shared.include_patterns]` and `[shared.exclude_patterns]` are each optional. If `[shared]` is present, at least one of these tables must be present, and every present table must contain at least one named array. Each name must be a non-empty string and each array must contain at least one string. Include arrays are validated using the include pattern grammar and exclude arrays using the exclude pattern grammar when the Configuration is loaded. Merely defining a Shared pattern does not apply it to any selection.

## 4. Configuration imports

A Root Configuration may declare zero or more Configuration imports using `[import.<name>]`. `<name>` is a non-empty import identifier used in configuration locations, errors, and the Archive index. It is not an Archive-path prefix or selection pattern.

Each import accepts only these fields:

```text
root            required string
configuration   required string
case            optional non-empty string
companion.<name> zero or more Root-owned Companion tables
```

### `root`

`root` is a directory path relative to the directory containing the Root Configuration file itself. Empty strings, absolute paths, and globs are rejected. `.` and `..` path elements are allowed, so an import may explicitly select a directory outside the cwd. `/` is the canonical path separator. POSIX absolute paths, Windows drive paths, and UNC paths are rejected regardless of the host OS. The resolved path must be an existing directory.

`root` is the only Configuration-import field that expands the parent filesystem boundary. Its resolved real directory becomes the imported Configuration's execution root and filesystem boundary. If the root path itself traverses symbolic links, the resolved directory is the boundary.

### `configuration`

`configuration` is a relative TOML file path from the import root. Empty strings, absolute paths, traversal with `.` / `..`, globs, and non-`.toml` extensions are rejected. The resolved path must be an existing regular file inside the import root.

Imports do not run normal Configuration discovery. The named file is loaded directly and fully parsed and validated as a normal Configuration. The imported Configuration's `[shared.include_patterns]` and `[shared.exclude_patterns]` continue to use local names inside that Configuration. In addition, the Root Configuration may reference them as `<import-name>.<pattern-name>`. Root-local and imported Shared-pattern tables are not merged, and references owned by the imported Configuration are not rebound into the Root namespace.

The imported Configuration's Target, if present, is still schema-validated but is not a source in the importing run. The imported Configuration still requires `[output]` as part of the normal schema. That Output is schema-validated but is not selected for the importing run: its filesystem path is not resolved for output, collisions are not checked, parent directories are not created, and nothing is written there.

The Root Configuration may declare zero or more `[import.<name>.companion.<companion-name>]` tables to define additional Companions inside the same import root. Their schema matches ordinary Companion tables, except that `path = "."` is permitted so the import root itself can be selected as a Companion. Other absolute paths, `..`, and globs are rejected, and the resolved directory must remain inside the import root. A Root-defined import Companion is owned by the Root Configuration, so its selection may reference Root-local Shared patterns by local name or any imported Shared pattern by a qualified `<import>.<pattern>` name. Companions declared by an imported Configuration resolve only that Configuration's own Shared patterns by local name.

The import name is the logical namespace for both Companions and Root-visible Shared patterns. Root `[companion.x]` is logically `x`; Companion `x` under `[import.a]` is logically `a.x`, regardless of whether it was declared in the imported Configuration or under `[import.a.companion.x]`. Shared pattern `p` from that imported Configuration is referenced from the Root side as `a.p`. If both Companion origins define the same Companion name within one import, the logical name is duplicated and the Configuration is rejected. The same local Companion name may appear under another import or at Root scope because those logical names differ. If a Root-local Shared pattern name is exactly the same string as a qualified imported Shared-pattern name of the same kind, the reference is ambiguous and the Configuration is rejected. Companion logical names are not used as Archive-path prefixes.

Each import namespace must contain at least one Companion from either origin.

### `case`

When `case` is omitted, all Companions in the import namespace use their base selections. When supplied, at least one Companion from either the imported Configuration or Root-defined import Companions must define that Case. Every Companion with the same Case uses it; a Companion without that Case falls back to its base selection. The imported Target and its Target Cases are not used.

The Root Configuration's CLI `--case` never propagates into imports. Every import selects at most one Companion Case through its own `case` field, so the Root Configuration and multiple imports may use different Cases in the same run.

### Recursive imports

An imported Configuration containing any `[import.<name>]` is a Configuration error. The import graph is limited to one level; cycles, transitive imports, and depth-dependent Case propagation are not provided.

A Root Configuration may contain only imports and no local Target or Companion. An imported Configuration, however, must contain at least one Companion.

## 5. Case semantics

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

Every Target Case and Companion Case is a complete selection definition. It does not inherit from or merge with the source's base selection. Shared pattern references on the base selection are not inherited either; a Case that needs the same Shared pattern must explicitly reference the same name. Root-owned Case selections may reference Root-local Shared patterns and qualified imported Shared patterns, but no Shared-pattern definitions are inherited or merged across Configuration boundaries.

## 6. Target and Companion semantics

The Target is optional. When `[target]` and/or `[target.case.<name>]` is present, the Configuration defines one logical runtime-bound Target rule. No Target `path` is stored in TOML, and TOML cannot define multiple separately configured Targets.

If the Root Configuration defines a Target, the CLI requires one or more positional `DIRECTORY` values. The selected Target definition is applied independently to every supplied directory, in CLI order. All runtime Target directories must resolve to distinct actual directories. If the Root Configuration does not define a Target, supplying any positional `DIRECTORY` is an error. CLI positional directories are never assigned to an imported Configuration; an imported Target definition is unused during that importing run.

`[target]`, when present, is the default Target selection used when `--case` is omitted. A Target may omit `[target]` and define only named Cases; in that form, invoking without `--case` is an error.

Every runtime Target directory must exist at execution time and is resolved according to the filesystem boundary rules below.

Each `[companion.<name>]` must define one concrete `path` relative to that Configuration's execution root, a non-empty `description`, and one complete base selection. The execution root is cwd for the Root Configuration and the corresponding import `root` for an imported Configuration. A Companion is always part of the Configuration's source set, whether or not a Target exists, and its directory must exist at execution time.

A Companion may additionally define zero or more complete Case selections under `[companion.<name>.case.<case-name>]`. Case selection follows the Configuration-wide rules in section 4. A missing Companion Case never removes the Companion; it causes that Companion to use its base selection.

## 7. Selection definition

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

## 8. Include pattern grammar

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

## 9. Exclude pattern grammar

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

## 10. Filesystem boundaries and symbolic links

The Root Configuration uses the process cwd as the execution root and filesystem boundary for its own sources. Each `[import.<name>].root` is resolved relative to the directory containing the Root Configuration file itself, and the resulting real directory becomes the execution root and filesystem boundary for that imported Configuration.

Ordinary Target, Companion, include, and Output paths may not escape the execution root of the Configuration that owns them. The only path allowed to explicitly cross the Root Configuration's cwd boundary is an import's `root`. Once the import root is established, its `configuration`, imported Companions, and selected files are confined inside that root again.

All used Target and Companion directories must exist and resolve inside the execution root of the Configuration that owns them. Source paths that escape that root through symbolic links are rejected.

Selected files must resolve inside their respective Target or Companion directory. File symbolic links resolving outside are rejected.

During recursive collection, directory symbolic links are not traversed. A directory link resolving outside its source directory is an error; a link resolving inside is ignored to avoid cycles and duplication.

A Target may use `.` for the execution root itself. In that case, the root contents are not flattened at the ZIP root: the execution root's actual directory name is preserved as the leading Archive path element.

## 11. Archive planning and paths

Selected files preserve their actual filesystem paths relative to the execution root of the Configuration that selected them. Root-local sources are cwd-relative; imported sources are relative to that import's `root`.

If multiple sources resolve to the same actual directory, their selections are unioned by real Archive path. A physical file is written once even if multiple declared purposes select it.

The Archive root contains a generated `README.md` that acts only as a purpose-neutral index of the resolved plan. It records the active Case (`default` when none is selected), participating directories, configured descriptions, selected Configuration locations, directory sources, selection counts, and relevant empty-result policy. Its fixed wording does not name the generating tool or prescribe a downstream use; purpose-specific meaning comes only from the configured descriptions.

Archive planning is deterministic: selected entries and generated output are ordered consistently rather than depending on incidental filesystem enumeration order.

## 12. Output semantics

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

## 13. Dry-run semantics

`--dry-run` uses the same source resolution, Case resolution, selection, and Archive planning logic as a normal invocation but does not create or modify the output.

Missing required `include` patterns are shown as `[missing]`. Missing optional patterns are shown as `[optional missing]`.

A source whose final selection is empty is shown as `empty, allowed` when permitted or `empty, would error` when a normal invocation would fail for emptiness.

Configuration contradictions, Target/DIRECTORY mismatches, invalid paths, unknown Case names, and `--sequence` on fixed output remain errors during dry-run. Because dry-run does not write the Archive, it does not resolve a timestamped filename or apply existing-output collision behavior.

## 14. CLI forms

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
