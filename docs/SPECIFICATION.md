# dirpluck Specification

This document defines the exact compatibility-supported behavior of the `dirpluck` CLI and TOML Configuration format. For purpose, see [../README.md](../README.md). For terminology, see [../GLOSSARY.md](../GLOSSARY.md). For authoring TOML, see [CONFIGURATION.md](CONFIGURATION.md). For CLI operation, see [CLI.md](CLI.md). For the trust boundary around Configurations and filesystem operations, see [TRUST.md](TRUST.md).

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
[about]
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[import.<name>.companion.<name>]
[target]
[target.location.<name>]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

Unknown keys are errors. `[about]` is optional; when present, it contains only a non-empty `description`. Each Configuration may contain zero or one `[import.<name>]` and zero or one Target. A Target may define zero or more named Target locations. Companions and Shared patterns are also named and may have multiple definitions. Every Configuration contains one `[output]`.

The `<name>` in `[target.location.<name>]` must be a non-empty name usable as one CLI path segment and must not contain `.`, `..`, `/`, or a backslash. Locations belong to the Target and are not defined separately per Case.

A Root Configuration does not need to define a Target or Companion itself if, after import composition, the Effective Configuration contains at least one Target or Companion.

## 4. Configuration filesystem path notation

TOML fields that identify filesystem locations use `/` as the path separator regardless of the host OS. Backslash is not accepted as a separator.

A relative path is resolved from the base directory defined by that field. An absolute path uses a complete absolute-root form recognized by the host OS, written with `/` separators, and refers directly to that location. Examples include `/opt/data` on a POSIX host, and `C:/data` or `//server/share/data` on a Windows host. `dirpluck` does not translate root notation from another OS. A Windows drive-relative form such as `C:foo` is not treated as an absolute path.

Filesystem-location fields do not perform `~` expansion or environment-variable interpolation and do not accept globs. `.` and `..` are accepted or rejected according to the field-specific rule. A Configuration that uses an absolute path depends on the referenced filesystem and is not guaranteed to be portable across operating systems.

This notation applies to Target-location `path`, import `root`, ordinary and import-root-overlay Companion `path`, and Root output `path` / `directory`. Values defined separately as relative notation, including imported `configuration`, include patterns, archive paths, and CLI Target references, follow their own rules.

## 5. Configuration import and composition

A Configuration import is declared as `[import.<name>]`. `<name>` is a non-empty name used to identify the link in diagnostics; it is not a namespace prefix for Companion or Shared-pattern names.

Each import accepts:

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

A `case` field is not accepted.

### `root`

`root` is a concrete directory path. Empty strings and globs are rejected. A relative `root` is resolved from the directory containing the Configuration file that declares the import and may use `.` and `..`. An absolute `root` refers directly to a directory on the host filesystem. The resolved path must be an existing directory.

The resolved root becomes the execution root of the immediately imported Configuration. A later import in the chain uses the Configuration file that declares that import as the base for its relative `root`.

### `configuration`

`configuration` is a relative TOML file path from the import root using `/` separators. Empty strings, backslashes, absolute paths, `.` or `..` components, escapes outside the import root, globs, and extensions other than `.toml` are rejected. The resolved path must be an existing regular file inside the import root. Root Configuration discovery is not performed for imports.

### Linear chain and cycles

An imported Configuration may itself contain zero or one `[import.<name>]`. There is no fixed import-depth limit.

During resolution, normalized real paths of Configuration files are tracked as the current chain. If the same file reappears in the current chain, resolution fails with a cycle error that includes the cyclic chain. Import depth by itself produces neither an error nor a warning.

### Definition resolution

The deepest Configuration provides the initial definitions, then each outer layer is applied in turn to construct the Effective Configuration.

For `[about].description`, resolution searches from the outermost layer inward and uses the first defined value as the effective description. If no layer defines it, the effective description is absent. The `about` table is not treated as a whole-definition shadowing unit; at present this optional value is resolved independently.

- **Target:** an outer Target shadows the entire inner Target.
- **Companion:** an outer Companion shadows an inner Companion with the same name; differently named Companions remain.
- **Shared include patterns:** an outer definition replaces an inner array with the same name.
- **Shared exclude patterns:** the same rule applies in a namespace independent of Shared include patterns.

Target and Companion shadowing is not a partial merge. A Target replacement includes its `description`, base selection, every Case selection, and every Target location. A Companion replacement includes its `path`, `description`, base selection, and every Case selection.

Shared-pattern references are resolved against the effective namespace after the full chain has been composed, not only against the source definition's origin layer. An outer layer may therefore provide or override a name referenced by an inner source. A reference still missing after composition is a Configuration error.

### Import-root Companion overlay

`[import.<name>.companion.<companion-name>]` defines a Companion whose relative `path` is based at the immediate import root. It uses the ordinary Companion selection schema and filesystem-location path notation. A relative `path` may use `.` and `..`; an absolute `path` may name any concrete directory on the host filesystem. Globs are rejected.

The overlay participates in definition resolution as Companion `<companion-name>` from the outer layer and may shadow a same-named Companion from the immediately imported Configuration. A single Configuration layer cannot define both `[companion.x]` and `[import.<name>.companion.x]`.

Each Configuration's `[output]` is schema-validated but is not composed. Only the outermost Root Configuration's output is used by the run.

## 6. Runtime sources and Case

When the Effective Configuration contains a Target, one or more positional CLI `TARGET` arguments are required regardless of the layer where the Target definition originated. A positional `TARGET` is not necessarily a raw source-directory path; it is resolved into one or more runtime Target directories by the rules below.

When the Effective Configuration has no Target, positional `TARGET` arguments are rejected.

The origin Configuration of the Target selection affects definition composition and the base for relative Target-location paths, but it is never used to infer a runtime Target directory automatically. Even when an inner Configuration's Target survives as the effective Target, the runtime Target is selected from positional CLI arguments.

### Target location

`[target.location.<name>]` contains only `path`. The value is a concrete directory path; empty strings and globs are rejected. A relative `path` is resolved from the execution root of the Configuration layer that owns the effective Target definition and may use `.` and `..`. An absolute `path` refers directly to a directory on the host filesystem. The resolved location must be an existing directory.

Target locations are part of the Target definition. When an outer Target shadows an inner Target, the full location set is replaced with the rest of the Target definition. Case selection does not change the location set.

### CLI Target-reference resolution

Each positional `TARGET` argument is resolved independently in this order:

1. If the argument begins with `./`, location lookup is skipped and the argument is treated as an explicitly cwd-relative Target reference.
2. If the argument has exactly the form `<name>/`, meaning one non-dot segment followed by a trailing `/`, it is a named-location expansion. If the Effective Target has no location named `<name>`, resolution fails and does not fall back to cwd.
3. Otherwise, if the first segment matches an Effective Target location name and a relative path follows it, that remaining path is resolved from the location directory.
4. Otherwise, the entire argument is resolved relative to the process working directory.

Absolute positional Target references are not accepted. To select a Target outside cwd, define a Target location.

A cwd-relative Target must remain inside the process working directory after resolution. A location-relative Target must remain inside its location directory. A Target reference that escapes its resolution base through `..` or a symbolic link is rejected. The resolved Target must be an existing directory.

A location prefix is a locating namespace, not a Target name. If `work/project` uses a location named `work`, the runtime Target is the resolved `project` directory.

### Named-location expansion

`<name>/` enumerates the directory entries immediately below the corresponding Target location and expands each directory into an independent runtime Target. Enumeration is not recursive, and regular files are not Targets.

A directory symlink is eligible only when it resolves inside the same Target location; a link resolving outside the location is an error. An expansion that yields no Target directories is an error.

Multiple positional `TARGET` arguments and location expansions may be combined in one run. The same Effective Target selection is applied independently to every runtime Target directory produced by resolution.

### Companion and Case

An ordinary Companion relative `path` is resolved from the execution root of the Configuration layer that owns the definition. An import-root overlay Companion relative `path` is resolved from the immediate import root. Both may use `.` and `..`; an absolute `path` refers directly to a directory on the host filesystem without depending on either base. The resolved path must be an existing directory, and the filesystem root itself is rejected as a Companion source. An inner Companion that survives shadowing retains the path base of its inner layer; a Companion replaced by an outer definition uses the base associated with the outer definition.

Zero or one Case is active for the Effective Configuration and is selected through CLI `--case`. There is no field for selecting a different Case per layer.

Without `--case`, the Target uses `[target]` when a Target exists and each Companion uses its base `[companion.<name>]` selection.

With a Case selected and a Target present, a same-named `[target.case.<name>]` is required. Each Companion uses the same-named Case when present and otherwise falls back to its base selection. Without a Target, at least one Companion must define the selected Case.

A Case selection is complete rather than a delta from base. It does not inherit include patterns, exclude patterns, or Shared-pattern references from the base selection.

## 7. Selection and Shared patterns

Every Target or Companion base selection and every Case selection requires a non-empty `description` and at least one include or include-if-exists candidate, whether written directly or supplied through Shared-pattern references.

`include_pattern_refs` and `include_if_exists_pattern_refs` refer to names in the effective Shared include namespace. `exclude_pattern_refs` refers to the effective Shared exclude namespace. Import names are not used as prefixes for these references.

Shared references are expanded in reference-array order, then direct patterns of the same kind are appended. After expansion, duplicates within required includes, optional includes, or excludes are Configuration errors. A pattern appearing in both required and optional includes is also a Configuration error.

`if_empty` defaults to `"error"`. `if_empty = "allow"` is valid only for an optional-only selection that has no required include pattern after Shared-pattern expansion.

### Include pattern grammar

An include pattern is a relative path from the source directory using `/` separators. Absolute paths, `.` or `..` traversal, and backslashes are rejected.

Each path element may contain at most one `*`. The `*` matches zero or more characters within one filesystem entry name and does not cross a path separator, so the number of path levels written in the Configuration is fixed.

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

When the final matched entry is a file, that file is selected. When it is a directory, files below it are collected recursively subject to exclude and symbolic-link rules. There are no implicit exclusions based on content or filename meaning. The trust boundary is described in [TRUST.md](TRUST.md).

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

## 8. Filesystem boundaries and symbolic links

The Root Configuration execution root is the process working directory. The execution root of each imported layer is the resolved `[import.<name>].root` that loaded that layer. An execution root is a resolution base for relative Configuration paths, not a universal boundary that constrains every source below it.

A runtime Target that does not use a Target location is resolved inside the process working directory, and the resolved Target directory becomes its selection boundary. A runtime Target that uses a Target location is resolved inside that location directory, and the resolved Target directory again becomes its selection boundary. A location is therefore a boundary for locating Targets; the final Target directory is the boundary for selected files.

Imported `configuration` remains constrained to the import root. A Companion may resolve any existing directory from a relative or absolute `path`, and the resolved Companion source directory itself becomes its selection boundary. Output locations do not participate in source boundaries.

Include resolution and selected files for each source are constrained to that source directory. A file or directory that escapes the source boundary through a symbolic link is rejected. Directory recursion does not follow directory symlinks. A symlink resolving outside the boundary is an error; a symlink resolving inside it is ignored to prevent cycles and duplicate traversal.

## 9. Archive planning

For a cwd-relative Target, selected files retain their filesystem-relative paths from the process working directory inside the ZIP, regardless of the layer where the Target definition originated. For a Target resolved through a Target location, selected files retain their filesystem-relative paths from the location directory. The logical location name itself is not included in the archive path. For example, if `work/team/project` resolves through location `work`, the archive path is `team/project/...`, not `work/team/project/...`. Direct children produced by `work/` expansion use the same rule.

When a Companion source directory lies inside the resolution base for that Companion's relative path, selected files retain their paths relative to that base as before. When an absolute path or `..` resolves the source directory outside that base, the final directory name of the resolved source becomes the archive root, and selected files are placed below it using paths relative to the source directory. The filesystem root itself is not accepted as a Companion source because it has no portable archive root. The host absolute path, drive, or UNC share name is never embedded in the archive path.

When the same physical file resolves to the same archive path more than once, it is written once. When different physical files collide on the same archive path, or the same physical file resolves to different archive paths through different source mappings, planning fails with an ambiguity error.

An Archive README is generated as `README.md` at the archive root. It is a content index, not a dirpluck resolution report. If an effective `[about].description` exists, its text appears immediately below `# Archive contents`, before the index table. If no effective description exists, this overall description is omitted.

By default the table has three columns: `Path`, `Description`, and `Files`. Each resolved source contributes one row containing its archive root, the selected selection `description`, and the number of files selected from that source. If multiple sources share the same archive root, their descriptions remain as separate rows.

By default the index does not record source filesystem paths, Configuration paths or tables, the Configuration chain, execution roots, Target or Companion names, the selected Case, or other dirpluck-specific resolution details. When CLI `--paths` is specified, a `Source` column is added containing each resolved source directory as a filesystem path using `/` separators. `--paths` does not change archive paths or file selection.

## 10. Output

Each Configuration defines either fixed output or generated output. Filesystem resolution, collision checks, directory creation, and writing are performed only for the Root Configuration's output.

### Fixed output

```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

Both `path` and `if_exists` are required. The Root Configuration `path` must be a concrete file path. A relative path is resolved from the current working directory; an absolute path names a destination directly on the host filesystem. A relative path may use `..`. `.`, globs, and destinations that resolve to directories are rejected. Missing parent directories are created. Output locations have no current-working-directory boundary.

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

The Root Configuration `directory` must be a concrete directory path. A relative path is resolved from the current working directory; an absolute path names a directory directly on the host filesystem. A relative path may use `.` and `..`. Globs are rejected. Missing directories are created. Output locations have no current-working-directory boundary.

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

## 11. Dry run

`--dry-run` uses the same import-chain resolution, cycle detection, definition composition, Target-location lookup and expansion, Target-directory resolution, Case selection, file selection, and archive-planning logic as a normal run, but it does not create or modify output.

A missing required `include` is shown as `[missing]`. A missing optional pattern is shown as `[optional missing]`. A final zero-file selection is shown as `empty, allowed` or `empty, would error` according to policy.

Multiple imports in one Configuration, import cycles, invalid root or configuration paths, invalid host absolute paths, unknown location expansions, Target references that escape a location boundary, unresolved Shared-pattern references, invalid source paths, Case inconsistencies, and comparable validation failures are errors during dry-run as well. Import depth by itself is neither an error nor a warning.

## 12. CLI contract

The principal accepted forms are:

```console
dirpluck TARGET [TARGET ...]
dirpluck --config NAME
dirpluck TARGET [TARGET ...] --case NAME
dirpluck --config NAME --case NAME
dirpluck ... --dry-run
dirpluck ... --paths
dirpluck ... --sequence N
dirpluck --configs
dirpluck --version
```

When the Effective Configuration contains a Target, positional arguments are `TARGET` references and are resolved by the rules in section 6. When there is no Target, positional `TARGET` arguments are rejected.

`--case` and `--sequence` may each be specified at most once. `--sequence` accepts an integer greater than or equal to 1. `--paths` adds the `Source` column to the Archive README produced by a normal build. When combined with `--dry-run`, no Archive is created, so it does not change the displayed tree. `--configs` cannot be combined with `TARGET`, `--case`, `--sequence`, `--config`, `--dry-run`, or `--paths`.

Argument parsing errors and `dirpluck` Configuration or build errors exit with status 2. Successful builds and informational commands exit with status 0. A successful normal build prints the final output path to standard output.

There are no additional CLI paths for import layers and no per-layer Case option. Imports are declared only through TOML `[import.<name>]`, and a Case is applied to the Effective Configuration after composition.
