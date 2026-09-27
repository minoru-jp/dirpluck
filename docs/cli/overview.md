# dirpluck CLI overview

This page covers the basic CLI form, Configuration selection, help/version, and process exit behavior. For Target and Case selection, see [Targets and Cases](targets.md). For reusable `.dirpluck-inv` calls, see [Invocation Templates](invocation-templates.md). For preview and runtime Output controls, see [Preview and runtime Output](output.md).

Exact document-selection rules are defined in the [document-selection specification](../specification/document-selection.md), while option-combination and exit-code requirements are defined in the [CLI contract](../specification/cli-contract.md).

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

## Help and version

```console
dirpluck --help
dirpluck --version
```

## Exit and errors

Successful execution exits with status 0. CLI argument errors and `dirpluck` validation/build errors exit with status 2 and display the reason after `dirpluck: error:`.

On a successful normal run that creates an Archive, the final output path is printed to standard output.
