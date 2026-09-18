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

Accepted top-level structures are:

```text
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[import.<name>.companion.<name>]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

Unknown keys are errors. Each Configuration may contain zero or one `[import.<name>]` and zero or one Target. Companions and Shared patterns are named and may appear multiple times under distinct names. Every Configuration still contains one `[output]`, but only the outermost Root Configuration's Output is executed.

When imports are present, dirpluck layers definitions from the deepest Configuration outward and produces one effective Configuration. Target uses the singleton key `target`; Companions resolve by Companion name; Shared include and exclude patterns resolve by name in separate namespaces. An outer definition with the same key shadows the inner definition as a whole. Distinct keys coexist.

Shadowing a Target or Companion replaces the complete source definition, including `path`, `description`, base selection, and all Case selections. Shadowing a Shared pattern replaces the entire array.

The Root Configuration may contain no local Target or Companion as long as resolution of the import chain leaves at least one effective Target or Companion.

## 4. Configuration imports and name resolution

Each Configuration may declare zero or one Configuration import using `[import.<name>]`. The import name is a non-empty identifier used for diagnostics and Archive indexing. In 0.5.0 it is not an automatic namespace prefix for Companion or Shared-pattern names.

Accepted fields are:

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

A `case` field is not accepted. One CLI `--case` is applied after the full chain is resolved.

### `root`

`root` is a directory path relative to the directory containing the Configuration file that declares that import. Empty strings, absolute paths, and globs are rejected. `.` and `..` are permitted. `/` is the canonical separator. POSIX absolute paths, Windows drive paths, and UNC paths are rejected regardless of host OS. The resolved path must be an existing directory.

The resolved root becomes the execution root and filesystem boundary of the directly imported Configuration. If that Configuration imports another Configuration, the next `root` is resolved by the same rule relative to that Configuration file.

### `configuration`

`configuration` is a relative TOML file path from the import root. Empty strings, absolute paths, escaping `..`, globs, and non-`.toml` extensions are rejected. The resolved file must exist and remain inside the import root. Import resolution reads exactly this file and does not perform Root Configuration discovery.

### Linear chain

An imported Configuration may itself contain one import. Import depth is unlimited.

During resolution, dirpluck keeps the normalized real path of every Configuration file on the active chain. If a file already present on that chain is encountered again, resolution fails with a cycle error that includes the cycle. Depth by itself never produces an error or warning.

### Definition resolution

The deepest Configuration initializes the effective definitions. Each outer layer is then applied in order:

- an outer Target shadows the inner Target;
- an outer Companion shadows an inner Companion with the same name, while different names remain;
- an outer Shared include pattern shadows the inner include pattern with the same name;
- an outer Shared exclude pattern shadows the inner exclude pattern with the same name in its independent namespace.

`include_pattern_refs`, `include_if_exists_pattern_refs`, and `exclude_pattern_refs` are resolved against the final effective Shared-pattern namespaces rather than only against the layer where the selection was written. An outer layer may therefore provide or override a Shared pattern referenced by an inner source. A reference still unresolved after the full chain is composed is a Configuration error.

### Import-root Companion overlay

`[import.<name>.companion.<companion-name>]` defines a Companion whose `path` is relative to the immediate import root. It uses the normal Companion selection schema and additionally permits `path = "."`. Absolute paths, `..`, and globs are rejected.

This definition participates in normal Companion-name resolution under `<companion-name>`, so it may shadow a same-named Companion from the directly imported Configuration. The same Configuration layer may not define both `[companion.x]` and `[import.<name>.companion.x]`.

### Target directory resolution

If the effective Target belongs to the Root Configuration, one or more CLI `DIRECTORY` arguments are required and the same Target selection is applied independently to all of them.

If the effective Target comes from an imported layer, CLI `DIRECTORY` is rejected. Its source directory is inferred from the owning Configuration file using only these forms:

```text
<project>/dirpluck.toml          -> <project>
<project>/dirpluck/<name>.toml   -> <project>
```

If an imported Target survives name resolution but its Configuration file is not in either form, the project directory cannot be determined and the run fails. An inner Target that is shadowed by an outer Target does not need project-directory resolution.

Outputs from inner layers are schema-validated but never executed. The final Output is always the Root Configuration's `[output]`.

## 5. Case semantics

A Case is a single flat named selection variation applied to the effective Configuration. At most one Case is selected through CLI `--case`. There is no per-import Case binding.

When a Target or Companion is shadowed by an outer layer, its base and all of its Case definitions are replaced together. Cases belonging to sources that survive shadowing remain part of the effective Configuration regardless of their origin layer.

Without a selected Case, the effective Target uses `[target]` if present and each Companion uses its base selection.

With a selected Case and an effective Target, the same-named `[target.case.<name>]` must exist. Each Companion uses its same-named Case when present and otherwise falls back to base. Without a Target, at least one effective Companion must define the selected Case.

Case selections are complete definitions, not deltas, and do not inherit include/exclude fields or Shared-pattern references from base.

## 6. Target and Companion semantics

Each Configuration may define at most one Target. Across a Configuration chain, an outer Target shadows the inner Target as a whole, so the effective Configuration contains at most one Target.

A Root-owned effective Target requires one or more CLI `DIRECTORY` arguments. An imported effective Target is bound to one project directory inferred from its owning Configuration file and does not accept CLI positional directories. If the effective Configuration has no Target, positional directories are also rejected.

Each Companion has a fixed `path`, non-empty `description`, and complete base selection. An ordinary Companion's `path` is relative to the execution root of the layer that owns it. An `[import.<name>.companion.<name>]` overlay is relative to the immediate import root.

An outer same-named Companion shadows the inner Companion including path, description, base, and Cases. Different Companion names coexist.

## 7. Selection definition

Every Target or Companion base/Case selection has a non-empty `description` and at least one effective `include` or `include_if_exists` candidate from direct patterns or Shared-pattern references.

`include_pattern_refs` and `include_if_exists_pattern_refs` reference names in the effective Shared-include namespace. `exclude_pattern_refs` references names in the effective Shared-exclude namespace. In 0.5.0, import names are not required as prefixes.

Shared namespaces are composed from inner to outer with same-name shadowing. A selection from an inner layer resolves its references against the final namespace, so an outer layer may provide or override a Shared pattern used by that source. A name that remains unresolved after the full chain is composed is a Configuration error.

Shared references expand in listed order, followed by direct patterns of the same kind. Duplicate effective patterns in required include, optional include, or exclude, and duplicates across required/optional include, are Configuration errors.

`if_empty = "allow"` is valid only for optional-only selections with no effective required include patterns.

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

The Root Configuration uses the process cwd as its execution root and filesystem boundary. Each imported layer uses the resolved `[import.<name>].root` from the layer that imports it.

Only an import `root` may explicitly cross the current layer's boundary. After an import root is resolved, the imported Configuration file, that layer's ordinary Companions, any effective imported Target project directory, and selected files must remain inside the corresponding execution root. A deeper import root is resolved relative to the Configuration file that declares it, so every layer establishes its own boundary independently.

An ordinary Companion keeps the execution root of the layer that defined it. An import-root overlay Companion uses the immediate import root. When a source is shadowed, the replacing outer definition also replaces this root context.

Source paths or selected files that escape their boundary through symbolic links are rejected. Directory symlinks are not traversed during recursion; links resolving outside the source boundary are errors, while links resolving inside are ignored to avoid cycles and duplicates.

## 11. Archive planning and paths

Selected files retain filesystem-relative paths from the execution root associated with their effective source definition. A source inherited from an inner layer uses that inner execution root; a source replaced by an outer definition uses the outer definition's root context.

If multiple sources select the same physical file at the same Archive path, it is written once. Different physical files resolving to the same Archive path are a collision error. The same physical file resolving to different Archive paths from different execution roots is also rejected as ambiguous.

The Archive-root `README.md` records the Configuration chain, execution roots, which layer's definitions survived into the effective Configuration, selected Case, participating sources, descriptions, and selection counts.

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

`--dry-run` uses the same import-chain resolution, cycle detection, definition layering, Target-directory resolution, Case selection, file selection, and Archive planning as a normal run, but does not create or modify output.

Missing required includes are shown as `[missing]`; missing optional patterns are `[optional missing]`. Empty selections are reported according to their policy.

Multiple imports in one Configuration, import cycles, invalid root/configuration paths, unresolved imported-Target project directories, unresolved Shared-pattern references, invalid source paths, and Case contradictions are errors even in dry-run. Import depth itself is never an error or warning.

## 14. CLI forms

When the Root Configuration's own Target survives into the effective Configuration, supply one or more runtime directories:

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

When an imported Target is effective, or when the effective Configuration has no Target, supply no positional directory:

```console
dirpluck --config NAME
```

Select one named Case for the effective Configuration with `--case`:

```console
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
dirpluck --config NAME --case NAME
```

`--config`, `--dry-run`, `--configs`, generated-output `--sequence N`, and `--version` otherwise keep their existing meanings.

There is no extra CLI path for import chains and no per-layer Case option. Imports are declared only in TOML and one Case is applied after name resolution.
