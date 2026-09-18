# dirpluck CLI Guide

This document explains how to use the `dirpluck` CLI. For TOML authoring, see [CONFIGURATION.md](CONFIGURATION.md). For exact resolution and validation semantics, see [SPECIFICATION.md](SPECIFICATION.md).

## Basic forms

```text
dirpluck [DIRECTORY ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
dirpluck --configs
dirpluck --version
```

When the selected Effective Configuration contains a Target, supply one or more `DIRECTORY` arguments. When it has no Target, do not supply positional directories.

```console
dirpluck projects/example
dirpluck projects/a projects/b
dirpluck --config snapshot
```

The concrete Target directory still comes from CLI `DIRECTORY` when the Target definition originated in an imported Configuration.

## Select a Configuration

By default, `dirpluck` uses `dirpluck.toml`. Select another Configuration with `--config NAME`; the `.toml` suffix may be omitted.

```console
dirpluck projects/example --config review
```

Root Configuration discovery checks only the current working directory and `./dirpluck/`. The same filename in both locations is treated as ambiguous.

List discoverable Configurations with:

```console
dirpluck --configs
```

`--configs` only lists candidates and cannot be combined with build options or `DIRECTORY`.

## Target directories

When a Configuration has a Target, the same Target selection is applied independently to every supplied `DIRECTORY`.

```console
dirpluck submissions/acme submissions/contoso
```

A Configuration without a Target can run using only fixed sources such as Companions.

```console
dirpluck --config project-snapshot
```

For exact path and filesystem-boundary rules, see [SPECIFICATION.md](SPECIFICATION.md).

## Case

Select one named Case with `--case NAME`.

```console
dirpluck projects/example --case audit
```

One Case may be supplied per run. How that Case applies to Targets and Companions is defined in [SPECIFICATION.md](SPECIFICATION.md).

## Dry run

`--dry-run` prints the resolved ZIP contents as a tree without creating an archive file.

```console
dirpluck projects/example --dry-run
```

It is useful after changing a Configuration or workspace and before writing an archive. The major planning steps are shared with a normal run; only the write is omitted. Exact dry-run semantics are in [SPECIFICATION.md](SPECIFICATION.md).

## Source paths in the archive index

The generated Archive README is a compact content index. By default it records only the archive path, the selected `description`, and the number of selected files. It does not record dirpluck-specific details such as Target or Companion roles, Configuration details, the selected Case, or source filesystem paths.

Use `--paths` only when the resolved source directories should also be included in the index.

```console
dirpluck projects/example --paths
```

`--paths` adds the resolved source directory to each index row. This can preserve local filesystem information, including absolute paths, in the Archive. Check whether that information is appropriate before using the option for an Archive that will be distributed externally.

## Sequence for generated output

For a Configuration using generated output, use a positive integer `--sequence N` when the caller deliberately needs to distinguish multiple runs started in the same second.

```console
dirpluck --config project-snapshot --sequence 2
```

`--sequence` is not automatic numbering and is invalid with fixed output. Exact filename placement and collision rules are defined in [SPECIFICATION.md](SPECIFICATION.md).

## Help and version

```console
dirpluck --help
dirpluck --version
```

## Exit status and errors

Successful commands exit with status 0. CLI argument errors and `dirpluck` Configuration or build errors exit with status 2 and print the reason after `dirpluck: error:`.

A successful normal build prints the final output path to standard output.

## Where to go next

- To create or modify a Configuration, read [CONFIGURATION.md](CONFIGURATION.md).
- To check terminology, read [../GLOSSARY.md](../GLOSSARY.md).
- For exact import resolution, matching, filesystem boundaries, Archive README behavior, output collisions, and validation, read [SPECIFICATION.md](SPECIFICATION.md).
