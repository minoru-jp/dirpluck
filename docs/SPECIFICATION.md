# dirpluck Specification

This document defines the exact compatibility-supported behavior of the `dirpluck` CLI and TOML Configuration format. For purpose, see [../README.md](../README.md). For terminology, see [../GLOSSARY.md](../GLOSSARY.md). For authoring TOML, see [CONFIGURATION.md](CONFIGURATION.md). For CLI operation, see [CLI.md](CLI.md).

## 1. Public surface

The compatibility-supported public surface is the `dirpluck` CLI and the TOML Configuration format defined here. Python modules inside the package are internal implementation unless explicitly documented as a public Python API in the future.

## 2. Root Configuration discovery

Discovery of the Root Configuration from the CLI is not recursive. It checks only these two locations relative to the process working directory:

- directly under the current working directory;
- directly under `./dirpluck/`.

When `--config` is omitted, the candidate filename is `dirpluck.toml`. With `--config NAME`, `NAME` is treated as a filename rather than an arbitrary path, and the `.toml` suffix may be omitted.

Zero matching candidates is an error. When the same candidate filename exists in both discovery locations, the result is ambiguous and is rejected rather than resolved by precedence.

`--configs` lists discoverable Root Configuration candidates. Directly under the current working directory, only TOML files with a top-level shape resembling a `dirpluck` Configuration are listed. Directly under `./dirpluck/`, TOML files are listed as candidates. The same filename in both locations is marked `ambiguous`.

Configuration imports do not use discovery. Each import explicitly names one relative TOML path inside its import root through `configuration`, and that file is loaded directly.

## 3. Configuration schema

The accepted top-level structures are:

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

Unknown keys are errors. Each Configuration may contain zero or one `[import.<name>]` and zero or one Target. Companions and Shared patterns are named and may have multiple definitions. Every Configuration contains one `[output]`.

A Root Configuration does not need to define a Target or Companion itself if, after import composition, the Effective Configuration contains at least one Target or Companion.

## 4. Configuration import and composition

A Configuration import is declared as `[import.<name>]`. `<name>` is a non-empty name used to identify the link in diagnostics and the Archive README; it is not a namespace prefix for Companion or Shared-pattern names.

Each import accepts:

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

A `case` field is not accepted.

### `root`

`root` is a relative directory path from the directory containing the Configuration file that declares the import. Empty strings, absolute paths, and globs are rejected. `.` and `..` are allowed, and `/` is the canonical path separator. POSIX absolute paths, Windows drive paths, and UNC paths are rejected regardless of the host OS. The resolved path must be an existing directory.

The resolved root becomes the execution root and filesystem boundary for the immediately imported Configuration. A later import in the chain follows the same rule and resolves from the Configuration file that declares that import.

### `configuration`

`configuration` is a relative TOML file path inside the import root. Empty strings, absolute paths, `..` that escapes the import root, globs, and extensions other than `.toml` are rejected. The result must be an existing regular file inside the import root. Root Configuration discovery is not performed for imports.

### Linear chain and cycles

An imported Configuration may itself contain zero or one `[import.<name>]`. There is no fixed import-depth limit.

During resolution, normalized real paths of Configuration files are tracked as the current chain. If the same file reappears in the current chain, resolution fails with a cycle error that includes the cyclic chain. Import depth by itself produces neither an error nor a warning.

### Definition resolution

The deepest Configuration provides the initial definitions, then each outer layer is applied in turn to construct the Effective Configuration.

- **Target:** an outer Target shadows the entire inner Target.
- **Companion:** an outer Companion shadows an inner Companion with the same name; differently named Companions remain.
- **Shared include patterns:** an outer definition replaces an inner array with the same name.
- **Shared exclude patterns:** the same rule applies in a namespace independent of Shared include patterns.

Target and Companion shadowing is not a partial merge. It replaces the complete source definition, including `path`, `description`, base selection, and all Case selections.

Shared-pattern references are resolved against the effective namespace after the full chain has been composed, not only against the source definition's origin layer. An outer layer may therefore provide or override a name referenced by an inner source. A reference still missing after composition is a Configuration error.

### Import-root Companion overlay

`[import.<name>.companion.<companion-name>]` defines a Companion whose path is anchored at the immediate import root. It uses the ordinary Companion selection schema and permits `path = "."`. Other absolute paths, `..`, and globs are rejected.

The overlay participates in definition resolution as Companion `<companion-name>` from the outer layer and may shadow a same-named Companion from the immediately imported Configuration. A single Configuration layer cannot define both `[companion.x]` and `[import.<name>.companion.x]`.

Each Configuration's `[output]` is schema-validated but is not composed. Only the outermost Root Configuration's output is used by the run.

## 5. Runtime sources and Case

When the Effective Configuration contains a Target, one or more CLI `DIRECTORY` arguments are required regardless of the layer where the Target definition originated. The same Target selection is applied independently to each directory. Every `DIRECTORY` is resolved inside the Root Configuration execution root, which is the process working directory.

The origin Configuration of the Target selection affects definition composition only. It is never used to infer a runtime Target directory. Even when an inner Configuration's Target survives as the effective Target, `dirpluck` does not infer a project directory from that Configuration file's location.

When the Effective Configuration has no Target, positional `DIRECTORY` arguments are rejected.

An ordinary Companion `path` is relative to the execution root of the Configuration layer that owns the definition. An import-root overlay Companion is relative to the immediate import root. An inner Companion that survives shadowing retains its inner execution root; a Companion replaced by an outer definition uses the root associated with the outer definition.

Zero or one Case is active for the Effective Configuration and is selected through CLI `--case`. There is no field for selecting a different Case per layer.

Without `--case`, the Target uses `[target]` when a Target exists and each Companion uses its base `[companion.<name>]` selection.

With a Case selected and a Target present, a same-named `[target.case.<name>]` is required. Each Companion uses the same-named Case when present and otherwise falls back to its base selection. Without a Target, at least one Companion must define the selected Case.

A Case selection is complete rather than a delta from base. It does not inherit include patterns, exclude patterns, or Shared-pattern references from the base selection.

## 6. Selection and Shared patterns

Every Target or Companion base selection and every Case selection requires a non-empty `description` and at least one include or include-if-exists candidate, whether written directly or supplied through Shared-pattern references.

`include_pattern_refs` and `include_if_exists_pattern_refs` refer to names in the effective Shared include namespace. `exclude_pattern_refs` refers to the effective Shared exclude namespace. Import names are not used as prefixes for these references.

Shared references are expanded in reference-array order, then direct patterns of the same kind are appended. After expansion, duplicates within required includes, optional includes, or excludes are Configuration errors. A pattern appearing in both required and optional includes is also a Configuration error.

`if_empty` defaults to `"error"`. `if_empty = "allow"` is valid only for an optional-only selection that has no required include pattern after Shared-pattern expansion.

### Include pattern grammar

An include pattern is a POSIX-form relative path from the source directory. Absolute paths, a pattern consisting of `.`, and traversal through `..` are rejected. Backslashes are normalized to `/` before validation.

Each path element may contain at most one `*`. The `*` matches zero or more characters within one filesystem entry name and does not cross a path separator, so the number of path levels written in the Configuration is fixed.

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

When the final matched entry is a file, that file is selected. When it is a directory, files below it are collected recursively subject to exclude and symbolic-link rules. There is no implicit exclusion for hidden files, repository metadata, environment files, private keys, or other secret-like names.

If a pattern matches multiple entries, all of them are selected. Matching is case-sensitive independently of the host OS. `**`, `?`, character classes (`[]`), and `!` are unsupported. Multiple matches are not ranked by version, modification time, or other metadata.

### Exclude pattern grammar

An exclude pattern matches one filesystem entry name rather than a relative path. A trailing `/` applies the pattern to directory names; a pattern without `/` applies it to filenames.

Supported forms are:

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

A bare `*`, `*/`, internal wildcards such as `foo*bar`, `**`, `?`, character classes, `!`, backslashes, and path separators are rejected.

## 7. Filesystem boundaries and symbolic links

The execution root and filesystem boundary of the Root Configuration is the process working directory. The execution root of each imported layer is the resolved `[import.<name>].root` that loaded that layer.

An import root is the only path that may establish a new boundary outside the current one. Once a root is established, the imported `configuration`, ordinary Companions owned by that layer, and files selected from those Companions are constrained to the corresponding execution root. Target directories are always resolved from CLI input inside the Root Configuration execution root.

A source path or selected file that escapes its boundary through a symbolic link is rejected. Directory recursion does not follow directory symlinks. A symlink resolving outside the boundary is an error; a symlink resolving inside it is ignored to prevent cycles and duplicate traversal.

## 8. Archive planning

Selected Target files retain their filesystem-relative paths from the Root Configuration execution root inside the ZIP, regardless of the layer where the Target definition originated. Selected Companion files retain paths relative to the execution root associated with their effective Companion definition.

When the same physical file resolves to the same archive path more than once, it is written once. When different physical files collide on the same archive path, or the same physical file resolves to different archive paths through different execution roots, planning fails with an ambiguity error.

An Archive README is generated as `README.md` at the archive root. It records facts from the resolved plan, including the Configuration chain, execution roots, effective definitions, selected Case, participating sources, descriptions, and selection counts.

## 9. Output

Each Configuration defines either fixed output or generated output. Filesystem resolution, collision checks, directory creation, and writing are performed only for the Root Configuration's output.

### Fixed output

```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

Both `path` and `if_exists` are required. The Root Configuration `path` must be a concrete path below the current working directory. Absolute paths, `..`, and globs are rejected. Missing parent directories are created. An output destination that resolves outside the current working directory through a symbolic link is rejected.

`if_exists` accepts only:

- `error`: fail without changing an existing output;
- `overwrite`: finish the new ZIP in a temporary file in the output directory, then replace the existing output.

With `error`, `dirpluck` verifies that the destination does not exist before the build and again immediately before final placement. The ZIP is completed in a temporary file in the same output directory before being moved to the final path.

### Generated output

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

`directory` and `timestamp = true` are required. `prefix` and `suffix` are optional. `path` and `if_exists` are not accepted in this form.

The Root Configuration `directory` must be a concrete directory inside the current working directory; `.` may represent the current working directory itself. Absolute paths, `..`, and globs are rejected. Missing directories are created, and symbolic-link escapes outside the current working directory are rejected.

`prefix` and `suffix` must each be one non-empty portable filename fragment. `.`, `..`, path separators, control characters, and `< > : " | ? *` are rejected.

The generated filename has this fixed form:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

The timestamp uses the process local time and is captured once at build start. Arbitrary timestamp formats, variable expansion, and naming templates are not supported.

`N` comes from CLI `--sequence N` and must be an integer greater than or equal to 1. When omitted, the number segment is absent. `dirpluck` does not scan existing outputs to infer a number and does not auto-number or auto-rename. `--sequence` is valid only with generated output and may be specified at most once.

If the generated filename already exists when checked, the run fails. Generated output has no overwrite option.

### Concurrent writes and input collision

`dirpluck` provides no inter-process locking or conflict arbitration. Concurrent writes to the same output path are unsupported; callers that may overlap must choose distinct output paths.

With either output form, the final output file itself cannot be selected as an archive input.

## 10. Dry run

`--dry-run` uses the same import-chain resolution, cycle detection, definition composition, Target-directory resolution, Case selection, file selection, and archive-planning logic as a normal run, but it does not create or modify output.

A missing required `include` is shown as `[missing]`. A missing optional pattern is shown as `[optional missing]`. A final zero-file selection is shown as `empty, allowed` or `empty, would error` according to policy.

Multiple imports in one Configuration, import cycles, invalid root or configuration paths, unresolved Shared-pattern references, invalid source paths, Case inconsistencies, and comparable validation failures are errors during dry-run as well. Import depth by itself is neither an error nor a warning.

## 11. CLI contract

The principal accepted forms are:

```console
dirpluck DIRECTORY [DIRECTORY ...]
dirpluck --config NAME
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
dirpluck --config NAME --case NAME
dirpluck ... --dry-run
dirpluck ... --sequence N
dirpluck --configs
dirpluck --version
```

`--case` and `--sequence` may each be specified at most once. `--sequence` accepts an integer greater than or equal to 1. `--configs` cannot be combined with `DIRECTORY`, `--case`, `--sequence`, `--config`, or `--dry-run`.

Argument parsing errors and `dirpluck` Configuration or build errors exit with status 2. Successful builds and informational commands exit with status 0. A successful normal build prints the final output path to standard output.

There are no additional CLI paths for import layers and no per-layer Case option. Imports are declared only through TOML `[import.<name>]`, and a Case is applied to the Effective Configuration after composition.
