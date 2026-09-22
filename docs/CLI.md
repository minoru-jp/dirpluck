# dirpluck CLI Guide

This document explains how to use the `dirpluck` CLI. For TOML authoring, see [CONFIGURATION.md](CONFIGURATION.md). For exact resolution and validation semantics, see [SPECIFICATION.md](SPECIFICATION.md).

## Basic form

```text
dirpluck [TARGET ...] [--config PATH] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck -i PATH [-e NAME] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck --version
```

If the selected Effective Configuration has a Pluck, supply one or more `TARGET` references. If it has no Pluck, do not supply positional arguments.

```console
dirpluck example
dirpluck work/project-a work/project-b
dirpluck --config snapshot
```

A Target reference has one of four forms: `NAME`, `SCOPE/NAME`, `/`, or `SCOPE/`. Every form selects Targets from a Scope.

## Selecting a Configuration

Configuration documents use TOML syntax but the filename extension is `.dirpluck`. Only when `--config` is omitted does dirpluck automatically use `default.dirpluck` in the runtime cwd. This is the only Configuration the CLI selects implicitly.

Select any other Configuration explicitly with `--config PATH`. `PATH` uses the same `/`-separator notation as a filesystem location. A relative path is resolved from the runtime cwd, while an absolute path is resolved on the host filesystem. If the path does not end in `.dirpluck`, that suffix is appended, so document names containing dots can be used directly. Use `/`, not `\`, as the CLI path separator even on Windows.

```console
dirpluck example --config review
dirpluck example --config configs/release-1.2
dirpluck example --config ../shared/review.dirpluck
```

When `--config` is supplied, dirpluck uses only the single Configuration document named by that path. It does not search another directory for a file with the same name, and it does not accept a directory and complete it with `default.dirpluck`. Configuration document paths follow the host OS's normal filesystem semantics, including paths that contain symbolic links or Windows directory junctions. dirpluck retains the selected path's absolute spelling as the document location, and relative paths inside that document are anchored to that location's directory. It does not infer Configuration candidates from file contents, automatically select or enumerate arbitrary `*.dirpluck` files, or fall back to `.toml` Configuration files.

Output is not required for `--preview`. A normal build uses either the Root Configuration's own Output declaration or CLI Runtime Output (`--here` / `--output`). Base Configurations referenced through `about.base` are not selected implicitly by the CLI.

## Invocation Template

Reusable CLI invocations can be stored in an Invocation Template `.dirpluck-inv` document. The root `[invocation]` is the default Invocation for the file, and `[invocation.<name>]` adds named Invocation entries.

```toml
[invocation]
config = "release"
targets = ["work/frontend", "work/backend"]

[invocation.docs]
config = "release"
targets = ["docs/"]
case = "publish"
archive_mtime = "zip-epoch"
```

`config`, `targets`, `case`, and `archive_mtime` are all optional in both the default Invocation and every named entry. A named entry is an independent Invocation, not a difference from the default Invocation, so omitted fields are not inherited from `[invocation]`. The names `config`, `targets`, `case`, and `archive_mtime` are reserved field names and cannot also be used as named Invocation entries. `targets` stores the same four Target-reference forms accepted as normal CLI positional arguments. `config` may omit the `.dirpluck` suffix, just like CLI `--config PATH`; a relative path is resolved from the directory of the selected `.dirpluck-inv` path. Template paths and Configuration paths referenced by `config` follow the host OS's normal filesystem semantics even when they contain symbolic links or Windows directory junctions. When `config` is omitted, the runtime-cwd `default.dirpluck` is used; when `targets` is omitted, the run has no positional Targets; when `case` is omitted, normal default Case semantics apply; when `archive_mtime` is omitted, the normal per-entry timestamp behavior applies.

Select the Template file explicitly with `-i PATH` or `--invocation-template PATH`. `PATH` uses the same filesystem-path notation as `--config`: a relative path is resolved from the runtime cwd and an absolute path from the host filesystem. If the path does not end in `.dirpluck-inv`, that suffix is appended. Invocation Template document paths follow the host OS's normal filesystem semantics, and the directory of the selected path is the anchor for relative `config` paths inside the Template. The Invocation Template file itself has no implicit default and dirpluck does not search another directory for it.

Omitting `-e` / `--entry` selects the default `[invocation]`. `-e NAME` selects `[invocation.NAME]`. A file that contains only named entries still has an implicit parent `invocation` table in TOML, so omitting `-e` selects an empty default Invocation. A completely empty document is invalid because it has no `invocation` table at all.

```console
dirpluck -i release
dirpluck -i release -e docs
dirpluck -i invocations/release --entry docs --case audit
dirpluck --invocation-template ../shared/release --preview
```

An Invocation with no fields is valid. It contributes no stored execution inputs; execution uses CLI values and normal defaults. After a successful `--preview` or normal build, the CLI prints a note when the selected Invocation has no `config`, `targets`, `case`, or `archive_mtime`. This is informational rather than a warning because valid runs, such as an Always-only build, may need no stored Invocation values.

An Invocation Template is not a general difference-composition mechanism for stored invocations. Positional `TARGET` and `--config` cannot be combined with `-i` / `--invocation-template`. CLI `--case NAME` may override the selected Invocation's `case`, and `--archive-mtime VALUE` may override its `archive_mtime`. `--here`, `--output`, `--force`, `--preview`, `--sequence`, `--archive-mtime`, and `--paths` remain available as runtime modifiers, subject to their normal combination constraints. `-e` / `--entry` can be used only together with `-i` / `--invocation-template`.

A `.dirpluck-inv` document is not a Configuration and cannot be referenced by `about.base`. After the selected Invocation's Configuration, Targets, Case, and Archive-entry mtime policy are resolved, execution uses normal dirpluck semantics.

## Specifying Targets

When a Configuration has a Pluck, the same Pluck selection is applied independently to each source directory resolved from a positional `TARGET`.

To select one Target from the always-present default Scope, supply only the directory name. The default Scope always uses the directory containing the Root Configuration file as its root. Moving the Configuration to another directory therefore moves the default Scope with it; define a named Scope when a different Target root is needed.

```console
dirpluck acme contoso
```

To select from a named Scope, use `<scope>/<name>`.

```console
dirpluck work/acme
```

`work/acme` selects only `acme` directly under Scope `work`. If Scope `work` is undefined, the command fails instead of falling back to another relative-path interpretation.

To select every eligible directory directly under a Scope as a Target, use an expansion form.

```console
dirpluck /
dirpluck work/
```

`/` expands the default Scope, while `work/` expands named Scope `work`. `/` does not mean the filesystem root. Both forms expand only direct child directories and do not enumerate recursively. Directories matching the Scope's `ignore` are removed from Target candidates. A missing named-Scope path does not affect a run that does not use that Scope.

`./`, `./acme`, `/acme`, `work/team/acme`, and absolute filesystem paths are not accepted as Target references.

A Configuration without a Pluck can run using only fixed sources such as Always sources.

```console
dirpluck --config project-snapshot
```

For Scope and `ignore` definitions, see [CONFIGURATION.md](CONFIGURATION.md). For exact Target-reference, boundary, and archive-path rules, see [SPECIFICATION.md](SPECIFICATION.md).

## Case

Select a named Case with `--case NAME`.

```console
dirpluck acme --case audit
```

Only one Case can be selected per run. [SPECIFICATION.md](SPECIFICATION.md) defines how Pluck and Always sources select Cases.

## Preview

`--preview` shows the resolved ZIP contents as a tree without creating an Archive file.

```console
dirpluck acme --preview
```

Use it after changing a Configuration or workspace to inspect the result before writing an Archive. The difference from a normal run is the write itself; the main resolution path for the base chain, Scope and Target handling, Cases, selection, and archive planning is shared. `--preview` can be used even when the selected Root Configuration has no Output declaration. Because preview does not resolve or write an Output, it cannot be combined with `--here`, `--output`, `--force`, or `--sequence`. If Selection traversal excludes non-ignored entries recognized as symbolic links or Windows directory junctions, the number skipped is reported as a note after the tree; individual paths are not listed. Entries matched by `ignore` are not included in that count. See [SPECIFICATION.md](SPECIFICATION.md) and [TRUST.md](TRUST.md) for exact preview and link-like-entry semantics.

## Source paths in the Archive index

By default, the generated Archive README is a compact index in which each final Archive root is a heading followed by the selected file count and optional `description`. It does not record `dirpluck`-specific resolution information such as Scope, Pluck, Always source, Configuration, or Case, nor does it record source filesystem paths.

Specify `--paths` only when source filesystem paths should also appear in each source section.

```console
dirpluck acme --paths
```

`--paths` adds the resolved source directory to each source section. Because this can leave local filesystem information such as absolute paths in the Archive, consider whether it is needed when the Archive will be distributed externally.

## Runtime Output

A normal build can temporarily choose its Output destination from the CLI. When Runtime Output is supplied, the Configuration's fixed output path or timestamp output directory is not used as the destination.

Use `--here` to write under the current runtime cwd.

```console
dirpluck acme --here
dirpluck acme --here=context.zip
```

`--here` alone creates an automatic timestamp filename in the cwd. An explicit filename is supplied only in the `--here=FILENAME` form with `=`; directory components are not accepted. Use `--output` when a path is needed. `-h` remains the short option for `--help`, so `--here` has no short form.

Use `-o PATH` / `--output PATH` to choose any runtime output path.

```console
dirpluck acme -o artifacts/context.zip
dirpluck acme -o artifacts/snapshots/
```

A `PATH` without trailing `/` is an exact output file path. A `PATH` ending in `/` is an output directory, and an automatic timestamp filename is generated directly beneath it. dirpluck does not infer file versus directory form from existing filesystem state. `/` is the directory marker on every OS, relative paths are resolved from the runtime cwd, and backslash is not accepted as a path separator.

When an automatic filename is generated, a Root Configuration with `[output.timestamp]` contributes its `prefix` / `suffix` naming rule, but not its configured output directory. Without Root timestamp Output, the default name is `dirpluck-YYYYMMDD-HHMMSS.zip`. `--sequence N` can also be used with these automatic names. It cannot be used with an exact Runtime Output filename.

Runtime Output does not overwrite an existing destination by default. Use `-f` / `--force` only when an existing destination may be replaced. `--force` also applies to normal builds that use Configuration fixed or timestamp Output. A collision on an automatic filename does not trigger automatic numbering, renaming, or resampling of the timestamp.

`--here` and `--output` are mutually exclusive. A Root Configuration without an Output declaration can still perform a normal build when Runtime Output is supplied.

## Sequence for timestamp Output

When the effective Output generates an automatic timestamp filename and multiple runs in the same second need to be distinguished intentionally, supply a positive integer with `--sequence N`.

```console
dirpluck --config project-snapshot --sequence 2
```

`--sequence` is not automatic numbering. It cannot be used with Configuration fixed Output, `--here=FILENAME`, or `--output PATH` without trailing `/`. See [SPECIFICATION.md](SPECIFICATION.md) for exact filename placement and collision rules.

## Archive entry mtime

`--archive-mtime VALUE` assigns one common timestamp to every entry written to the ZIP. It is a runtime policy supplied by the CLI or an Invocation Template, not a field in Configuration `[output]` or `[output.timestamp]`.

```console
dirpluck example --archive-mtime 2026-01-01T00:00:00
dirpluck -i release --archive-mtime zip-epoch
dirpluck example --archive-mtime now
```

`VALUE` is one of:

- `YYYY-MM-DDTHH:MM:SS`: a timezone-free ZIP timestamp literal in the range `1980-01-01T00:00:00` through `2107-12-31T23:59:59`.
- `now`: sample local current time once for the run and use that one value for every entry.
- `zip-epoch`: use ZIP's minimum timestamp, `1980-01-01T00:00:00`.

ZIP timestamps have two-second precision, so an odd second is rounded down to the preceding even second. The resolved value is applied to generated `README.md`, empty-directory entries, and selected source files alike. When the option is omitted, source files keep their filesystem mtimes while entries generated by dirpluck use their generation time, matching the existing behavior.

A fixed timestamp or `zip-epoch` can remove byte differences caused by entry timestamps and can therefore help produce reproducible archives. Other ZIP metadata still matters: source-file permission bits are stored in ZIP `external_attr` and can change the archive bytes. dirpluck does not normalize those permission bits, and this option does not provide a byte-for-byte reproducibility guarantee across compressor implementations, runtime versions, platforms, or other metadata. `--archive-mtime` does not change the `YYYYMMDD-HHMMSS` used in timestamp Output filenames. It is accepted with `--preview`, but preview writes no Archive, so it does not affect the preview result.

An Invocation Template can store the same policy as `archive_mtime = "zip-epoch"`. When both are present, CLI `--archive-mtime` overrides the selected Invocation's value.

## Help and version

```console
dirpluck --help
dirpluck --version
```

## Exit and errors

Successful execution exits with status 0. CLI argument errors and `dirpluck` validation/build errors exit with status 2 and display the reason after `dirpluck: error:`.

On a successful normal run that creates an Archive, the final output path is printed to standard output.

## What to read next

- To create or change a Configuration: [CONFIGURATION.md](CONFIGURATION.md)
- To use the same execution model from Python: [PYTHON_API.md](PYTHON_API.md)
- To check the meanings of terms: [../GLOSSARY.md](../GLOSSARY.md)
- To review the trust boundary for Configurations and filesystem operations: [TRUST.md](TRUST.md)
- To check exact rules for base composition, matching, filesystem boundaries, Archive README generation, Output collisions, and related behavior: [SPECIFICATION.md](SPECIFICATION.md)
