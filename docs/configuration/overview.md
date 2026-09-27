# Configuration overview

The `.dirpluck` document format, its basic shape, metadata, and path notation.

This guide explains authoring. The Specification defines the compatibility contract: see [Configuration schema](../specification/configuration-schema.md), [Filesystem path notation](../specification/paths.md), and [CLI document selection](../specification/document-selection.md). For operation, see the [CLI guide](../cli/INDEX.md); for filesystem and sharing boundaries, see the [Trust model](../TRUST.md).

## Configuration document

Save a Configuration as a document whose filename ends in `.dirpluck`; its contents use TOML syntax. A `.toml` filename is not accepted as a dirpluck Configuration.

```text
default.dirpluck
review.dirpluck
configs/common.dirpluck
```

`default.dirpluck` is the special filename used automatically from the runtime cwd only when `--config` is omitted. Select a differently named Configuration or one in another directory explicitly with `--config PATH`. Relative CLI paths are resolved from the cwd, while relative filesystem paths inside a Configuration are resolved from that Configuration file's directory. Paths that select or reference Configuration documents follow the host OS's normal filesystem semantics, including symbolic links and Windows directory junctions. Relative paths are anchored to the selected or referenced document path's directory rather than to the physical location of a link target. See [CLI guide](../cli/INDEX.md) and [Specification](../specification/INDEX.md) for the exact selection rules. A Base Configuration does not need the special default name; `[about].base` references a concrete `.dirpluck` path.

A `.dirpluck-inv` file is a separate Invocation Template document type, not a Configuration. It does not participate in the Configuration schema or base chain. See [CLI guide](../cli/INDEX.md) for authoring and selecting Invocation Templates.
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

See [Specification](../specification/INDEX.md) for base-chain composition and cycle detection.
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

This rule applies at least to `about.base`, `scope.<name>.path`, `always.<name>.path`, `output.path`, and `output.timestamp.path`. Not only `about.base`, which references another Configuration document, but also explicitly configured source-root locations such as named Scopes and Always sources follow the host OS's normal filesystem semantics and may include symbolic links or Windows directory junctions. Resolving an alias used as an explicit root is separate from the rule that recognized link-like entries are not selected during automatic traversal below that root. Values that are not filesystem locations, such as patterns and CLI Target references, follow their own rules. See [Specification](../specification/INDEX.md) for exact validation.
