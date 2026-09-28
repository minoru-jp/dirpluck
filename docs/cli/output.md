# Preview and runtime Output

This page covers preview, optional source paths in the generated Archive README, runtime Output, sequence values, and Archive entry timestamps. For Configuration-side Output authoring, see [Configuration output](../configuration/output.md). Exact behavior is defined in the [Output specification](../specification/output.md), [Preview specification](../specification/preview.md), and [Archive planning specification](../specification/archive.md). Review the [Trust model](../TRUST.md) before distributing Archives outside the local environment.

## Preview

`--preview` shows the resolved ZIP contents as a tree without creating an Archive file.

```console
dirpluck ./acme/ --preview
```

Use it after changing a Configuration or workspace to inspect the result before writing an Archive. The difference from a normal run is the write itself; the main resolution path for the base chain, Scope and Target handling, Cases, selection, and archive planning is shared. `--preview` can be used even when the selected Root Configuration has no Output declaration. Because preview does not resolve or write an Output, it cannot be combined with `--here`, `--output`, `--force`, or `--sequence`. If Selection traversal excludes non-ignored entries recognized as symbolic links or Windows directory junctions, the number skipped is reported as a note after the tree; individual paths are not listed. Entries matched by `ignore` are not included in that count. See [Specification](../specification/INDEX.md) and [Trust model](../TRUST.md) for exact preview and link-like-entry semantics.

## Source paths in the Archive index

By default, the generated Archive README is a compact index in which each final Archive root is a heading followed by the selected file count and optional `description`. It does not record `dirpluck`-specific resolution information such as Scope, Pluck, Always source, Configuration, or Case, nor does it record source filesystem paths.

Specify `--paths` only when source filesystem paths should also appear in each source section.

```console
dirpluck ./acme/ --paths
```

`--paths` adds the resolved source filesystem path to each source section: a directory path for directory sources and a file path for file Targets. Because this can leave local filesystem information such as absolute paths in the Archive, consider whether it is needed when the Archive will be distributed externally.

## Runtime Output

A normal build can temporarily choose its Output destination from the CLI. When Runtime Output is supplied, the Configuration's fixed output path or timestamp output directory is not used as the destination.

Use `--here` to write under the current runtime cwd.

```console
dirpluck ./acme/ --here
dirpluck ./acme/ --here=context.zip
```

`--here` alone creates an automatic timestamp filename in the cwd. An explicit filename is supplied only in the `--here=FILENAME` form with `=`; directory components are not accepted. Use `--output` when a path is needed. `-h` remains the short option for `--help`, so `--here` has no short form.

Use `-o PATH` / `--output PATH` to choose any runtime output path.

```console
dirpluck ./acme/ -o artifacts/context.zip
dirpluck ./acme/ -o artifacts/snapshots/
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

`--sequence` is not automatic numbering. It cannot be used with Configuration fixed Output, `--here=FILENAME`, or `--output PATH` without trailing `/`. See [Specification](../specification/INDEX.md) for exact filename placement and collision rules.

## Archive entry mtime

`--archive-mtime VALUE` assigns one common timestamp to every entry written to the ZIP. It is a runtime policy supplied by the CLI or an Invocation Template, not a field in Configuration `[output]` or `[output.timestamp]`.

```console
dirpluck ./example/ --archive-mtime 2026-01-01T00:00:00
dirpluck -i release --archive-mtime zip-epoch
dirpluck ./example/ --archive-mtime now
```

`VALUE` is one of:

- `YYYY-MM-DDTHH:MM:SS`: a timezone-free ZIP timestamp literal in the range `1980-01-01T00:00:00` through `2107-12-31T23:59:59`.
- `now`: sample local current time once for the run and use that one value for every entry.
- `zip-epoch`: use ZIP's minimum timestamp, `1980-01-01T00:00:00`.

ZIP timestamps have two-second precision, so an odd second is rounded down to the preceding even second. The resolved value is applied to generated `README.md`, empty-directory entries, and selected source files alike. When the option is omitted, source files keep their filesystem mtimes while entries generated by dirpluck use their generation time, matching the existing behavior.

A fixed timestamp or `zip-epoch` can remove byte differences caused by entry timestamps and can therefore help produce reproducible archives. Other ZIP metadata still matters: source-file permission bits are stored in ZIP `external_attr` and can change the archive bytes. dirpluck does not normalize those permission bits, and this option does not provide a byte-for-byte reproducibility guarantee across compressor implementations, runtime versions, platforms, or other metadata. `--archive-mtime` does not change the `YYYYMMDD-HHMMSS` used in timestamp Output filenames. It is accepted with `--preview`, but preview writes no Archive, so it does not affect the preview result.

An Invocation Template can store the same policy as `archive_mtime = "zip-epoch"`. When both are present, CLI `--archive-mtime` overrides the selected Invocation's value.
