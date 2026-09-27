# Targets and Cases

This page explains positional Target references, Scope expansion, and Case selection from the CLI. For authoring Scope and Namespace declarations, see [Configuration sources](../configuration/sources.md). For authoring Cases, see [Configuration selection](../configuration/selection.md). Exact Target and Case semantics are defined in the [runtime-targets specification](../specification/runtime-targets.md).

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

For Scope and `ignore` definitions, see [Configuration guide](../configuration/INDEX.md). For exact Target-reference, boundary, and archive-path rules, see [Specification](../specification/INDEX.md).

## Case

Select a named Case with `--case NAME`.

```console
dirpluck acme --case audit
```

Only one Case can be selected per run. [Specification](../specification/INDEX.md) defines how Pluck and Always sources select Cases.
