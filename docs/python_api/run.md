# dirpluck.run

The official high-level entry point has this shape:

```python
run(
    *targets,
    config=None,
    case=None,
    sequence=None,
    invocation=None,
    entry=None,
    preview=False,
    paths=False,
    archive_mtime=None,
    output=None,
    force=False,
    cwd=None,
)
```

The arguments map to CLI inputs as follows:

```text
targets       positional TARGET
config        --config PATH
case          --case CASE
sequence      --sequence N
invocation    -i / --invocation-template PATH
entry         -e / --entry NAME
preview       --preview
paths         --paths
archive_mtime --archive-mtime VALUE
output        --output PATH
force         --force
cwd           Python API only: runtime anchor for relative control-document paths
```

When `invocation` is used, positional `targets` and `config` are not supplied at the same time. `entry` is valid only together with `invocation`. Because `preview=True` does not resolve or write an Output, it cannot be combined with `sequence`, `output`, or `force=True`. `sequence` must be an integer greater than or equal to 1. `output` uses the same `/`-separator path syntax as CLI `--output`, relative to `cwd`, and `force` is boolean.

When an Invocation Template is selected, the `case` argument overrides the stored Case and `archive_mtime` overrides the stored `archive_mtime`, following the same rules as the corresponding CLI options. `case` uses the same two-axis grammar: `"audit"` selects a Pluck Case, `".release"` selects an Always Case, and `"audit.release"` selects both. If the Invocation omits `config`, dirpluck uses `cwd/default.dirpluck`; if it omits `targets`, the run has no Targets; if it omits `case`, normal default Case semantics apply; if it omits `archive_mtime`, the normal per-entry timestamp behavior applies.

## Configuration deprecation warning

From 0.14.0 through releases before 1.0.0, if a loaded Configuration uses a deprecated one-element nested-array reference, `dirpluck.run()` reports one public `ConfigurationDeprecationWarning` per affected Configuration file through Python's warnings framework. It is a `FutureWarning` subclass, so Python's default warning filters display it. Configuration files loaded through the base chain are covered as well.

The warning location is attributed to the first caller frame outside the dirpluck package rather than to a fixed `stacklevel`. Callers that need explicit control can filter or promote `dirpluck.ConfigurationDeprecationWarning`. This is a Configuration-syntax lifecycle diagnostic, so it is not included in `RunResult.warnings`, which is reserved for planning diagnostics. The CLI collects the same diagnostic and renders its concise stderr warning instead of emitting an additional Python warning.

The legacy syntax becomes invalid in 1.0.0. Migrate Shared references to `{ shared = "..." }` and concrete relative `ignore` paths to `{ path = "..." }`. From 0.16.0 through releases before 1.0.0, legacy `[pluck.case.<name>]` reports the same warning category and should be migrated to canonical `[case.pluck.<name>]`.

## Always migration warning

From 0.16.0 through the release immediately before 1.0.0, `dirpluck.run()` reports Always migration through the public `AlwaysMigrationWarning` category in Python's warnings framework. Dirpluck compares the valid 0.14.x Always Archive identity with the 0.16.x effective Always name and emits a layout migration warning only for sources whose Archive root actually changes. The warning includes both the old and new roots. No layout warning is emitted when the old and new identities are the same. Starting in 0.17.0, an Always source with an explicit effective Layout suppresses this legacy layout warning because the Layout intentionally determines the current final Archive destination.

Using `[always.<name>].namespace` always reports a separate pre-1.0 compatibility warning, independent of the layout comparison. In 0.16.x the Namespace name temporarily replaces the Always name for Archive placement, but the field is removed in 1.0.0. Write the desired Archive directory name directly in `[always.<name>]`.

`AlwaysMigrationWarning` is a `FutureWarning` subclass. Its location is attributed to the first caller frame outside the dirpluck package, and callers may filter or promote `dirpluck.AlwaysMigrationWarning` to an error when migration-sensitive automation must detect layout changes explicitly. These lifecycle diagnostics are not included in `RunResult.warnings`. The CLI collects the same public warnings and renders them to stderr rather than emitting an additional Python warning.

## README-only Archive

`dirpluck.run()` may complete successfully with zero resolved sources. With no Target references and no Always sources, a build creates an Archive containing only the generated `README.md`; `preview=True` returns a tree containing only `README.md`. This is a normal result, not a warning or exception. The generated README records that no sources were selected, and `RunResult.archive_entries` is `("README.md",)`.

A valid Case may also produce a zero-source result. Case names that are not defined by the applicable Configuration rules remain errors.

## Runtime Output

`output` replaces the Configuration Output destination for one invocation.

```python
result = dirpluck.run(
    "example",
    output="artifacts/context.zip",
)
```

An `output` value without trailing `/` is an exact output file path. A value ending in `/` is an output directory, and dirpluck generates an automatic timestamp filename directly beneath it.

```python
result = dirpluck.run(
    "example",
    output="artifacts/snapshots/",
)
```

For automatic filenames, a Root Configuration with `[output.timestamp]` contributes its `prefix` / `suffix` naming rule, but not its configured output directory. Without Root timestamp Output, the name is `dirpluck-YYYYMMDD-HHMMSS.zip`. `sequence` is valid only with an automatic timestamp filename.

A build with `output` does not require an Output declaration on the Root Configuration. Runtime Output does not overwrite an existing destination by default; use `force=True` to allow replacement. `force=True` also applies when the build uses Configuration fixed or timestamp Output.

CLI `--here` has no dedicated Python argument. `output="./"` is equivalent to cwd plus an automatic filename, while `output="context.zip"` is equivalent to cwd plus an explicit filename. `output` uses `/` as the path separator on every OS and rejects backslashes.

## Invocation Template

Named Invocations can be selected in the same way as with the CLI:

```python
import dirpluck

result = dirpluck.run(
    invocation="calls/release",
    entry="review",
    case="audit",
    preview=True,
)
```

This is conceptually equivalent to:

```console
dirpluck -i calls/release -e review --case audit --preview
```

An Invocation with no fields is still valid. In that case, `RunResult.invocation_empty` is `True`. The CLI presents this state as a human-readable note; the Python API returns it as structured state.

## Archive entry mtime

`archive_mtime` is the Python API equivalent of CLI `--archive-mtime VALUE`.

```python
result = dirpluck.run(
    "example",
    archive_mtime="zip-epoch",
)
```

Accepted values are `YYYY-MM-DDTHH:MM:SS`, `"now"`, and `"zip-epoch"`. An explicit timestamp must be within ZIP's range from `1980-01-01T00:00:00` through `2107-12-31T23:59:59`; it is treated as a timezone-free literal and is not converted between time zones. `now` samples local current time once for a `run()` call. ZIP timestamps have two-second precision, so odd seconds are rounded down to the preceding even second.

When supplied, the resolved timestamp is applied uniformly to generated `README.md`, empty-directory entries, and selected source files. When omitted, source files keep their filesystem mtimes and generated entries use their generation time, preserving the existing behavior. A fixed value can remove byte differences caused by entry timestamps and can therefore help produce reproducible archives. Source-file permission metadata is not normalized and can still change the archive bytes; dirpluck does not guarantee byte-for-byte reproducibility of the Archive as a whole across runtime, platform, compressor, permission metadata, or other serialization differences. It also does not change the timestamp used in timestamp Output filenames. `preview=True` accepts the argument but writes no Archive, so the preview result is unaffected.
