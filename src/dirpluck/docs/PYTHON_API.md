# dirpluck Python API

This document describes the official Python API for dirpluck 0.9.x. The API is intentionally small: it exposes the same execution model as the CLI without making the Configuration parser or builder pipeline part of the general compatibility contract.

## Positioning

The center of the official API is `dirpluck.run()`. It accepts the same kinds of runtime inputs as the CLI: Targets, Configuration, Case, Invocation Template, Entry, preview, and Output modifiers, and executes them through the same application layer.

The CLI remains responsible for human-facing argument parsing, help, exit status, and stdout / stderr formatting. The Python API does not use `SystemExit` as its normal control flow. It returns a `RunResult` and raises expected dirpluck failures as `DirpluckError` subclasses.

For 0.9.x, only names explicitly exported from the package root are official Python API. Lower-level modules and underscore-prefixed names are implementation details and are not compatibility-supported during Beta.

## Basic form

```python
import dirpluck

result = dirpluck.run("example")
print(result.output_path)
```

This is conceptually equivalent to:

```console
dirpluck example
```

When `config` is omitted, dirpluck uses `default.dirpluck` in the runtime cwd. The Python API also provides an API-only `cwd` argument when you want to choose the anchor for relative control-document paths without changing the process working directory.

```python
from pathlib import Path
import dirpluck

result = dirpluck.run(
    "example",
    config="configs/review",
    cwd=Path("/work/project"),
)
```

Here, `config` selects `/work/project/configs/review.dirpluck`. The `cwd` argument does not rebase relative source paths written inside a Configuration; those continue to resolve from the location of the Configuration document that contains them.

## `run()`

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
    cwd=None,
)
```

The arguments map to CLI inputs as follows:

```text
targets       positional TARGET
config        --config PATH
case          --case NAME
sequence      --sequence N
invocation    -i / --invocation-template PATH
entry         -e / --entry NAME
preview       --preview
paths         --paths
archive_mtime --archive-mtime VALUE
cwd           Python API only: runtime anchor for relative control-document paths
```

When `invocation` is used, positional `targets` and `config` are not supplied at the same time. `entry` is valid only together with `invocation`. `preview=True` cannot be combined with `sequence`, and `sequence` must be an integer greater than or equal to 1.

When an Invocation Template is selected, the `case` argument overrides the stored Case and `archive_mtime` overrides the stored `archive_mtime`, following the same rules as the corresponding CLI options. If the Invocation omits `config`, dirpluck uses `cwd/default.dirpluck`; if it omits `targets`, the run has no Targets; if it omits `case`, normal default Case semantics apply; if it omits `archive_mtime`, the normal per-entry timestamp behavior applies.

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

When supplied, the resolved timestamp is applied uniformly to generated `README.md`, empty-directory entries, and selected source files. When omitted, source files keep their filesystem mtimes and generated entries use their generation time, preserving the existing behavior. A fixed value can remove byte differences caused by entry timestamps and can therefore help produce reproducible archives. Source-file permission bits are stored in ZIP `external_attr` and can still change the archive bytes; dirpluck does not normalize them and does not guarantee byte-for-byte reproducibility of the Archive as a whole. It also does not change the timestamp used in timestamp Output filenames. `preview=True` accepts the argument but writes no Archive, so the preview result is unaffected.

## Preview and `RunResult`

`preview=True` performs the same planning semantics as CLI `--preview` without writing an Archive file.

```python
result = dirpluck.run("example", preview=True)
print(result.preview_text)
```

`RunResult` exposes these public fields:

```text
output_path         ZIP path created by a build; None for preview
preview_text        the same tree representation used by CLI --preview
archive_entries     tuple of final entry paths that belong in the Archive
archive_readme      Markdown generated as the root README.md
skipped_link_count  number of link-like entries excluded during automatic traversal
invocation_empty    whether the selected Invocation had no config / targets / case / archive_mtime
```

A normal build also returns `preview_text` and `archive_readme` from the exact plan used for the build. Callers therefore do not need to parse CLI output to inspect the main public information about the planned or generated Archive.

## Errors

Catch `DirpluckError` when one caller wants to handle expected dirpluck failures uniformly.

```python
import dirpluck

try:
    result = dirpluck.run("example", preview=True)
except dirpluck.DirpluckError as exc:
    print(exc)
```

Invalid Configurations, Target or Selection resolution failures, Invocation Template failures, and incompatible `run()` argument combinations raise a `DirpluckError` subclass. CLI status 2 and the `dirpluck: error:` prefix are presentation details of the CLI adapter and are not part of the Python API contract.

## Official surface and compatibility

The official package-root exports for 0.9.x are exactly:

```python
from dirpluck import DirpluckError, RunResult, __version__, run
```

`dirpluck.builder`, `dirpluck.config`, `dirpluck.invocation`, underscore-prefixed modules, and models or helpers importable from those modules are not official API. Code that depends on them may need changes as internal refactoring continues during Beta.

Keeping the official surface deliberately small provides the same high-level capability as the CLI while preserving room to change Configuration models and archive-planning internals later.

## What to read next

- CLI arguments and human-readable output: [CLI.md](CLI.md)
- Writing Configurations: [CONFIGURATION.md](CONFIGURATION.md)
- Exact Configuration, Target, Case, traversal, Archive, and Output semantics: [SPECIFICATION.md](SPECIFICATION.md)
- Trust boundaries for filesystem operations and distribution: [TRUST.md](TRUST.md)
- Term meanings: [../GLOSSARY.md](../GLOSSARY.md)
