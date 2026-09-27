# Targets and Cases

This page explains positional Target references, Scope expansion, and Case selection from the CLI. For authoring Scope and Namespace declarations, see [Configuration sources](../configuration/sources.md). For authoring Cases, see [Configuration selection](../configuration/selection.md). Exact Target and Case semantics are defined in the [runtime-targets specification](../specification/runtime-targets.md).

## Specifying Targets

A positional `TARGET` resolves either a directory or a regular file according to the Scope's `target_kind`. The effective Pluck selection is applied independently to each directory Target. A file Target is included as an atomic file and does not use Pluck.

To select one Target from the always-present default Scope, supply only the direct-child entry name. Whether that entry must be a directory or a regular file is determined by the Scope's `target_kind`. The default Scope always uses the directory containing the Root Configuration file as its root. Moving the Configuration to another directory therefore moves the default Scope with it; define a named Scope when a different Target root is needed.

```console
dirpluck acme contoso
```

To select from a named Scope, use `<scope>/<name>`.

```console
dirpluck work/acme
```

`work/acme` selects only `acme` directly under Scope `work`. If Scope `work` is undefined, the command fails instead of falling back to another relative-path interpretation.

To select every eligible Target directly under a Scope, use an expansion form.

```console
dirpluck /
dirpluck work/
```

`/` expands the default Scope, while `work/` expands named Scope `work`. `/` does not mean the filesystem root. With `target_kind = "directory"`, expansion includes only eligible direct-child directories. With `target_kind = "file"`, it includes only eligible direct-child regular files. Expansion is never recursive, and candidates matching the Scope's `ignore` are removed. A missing named-Scope path does not affect a run that does not use that Scope.

`./`, `./acme`, `/acme`, `work/team/acme`, and absolute filesystem paths are not accepted as Target references.

A Configuration without a Pluck may still use Target references from file-kind Scopes. Directory Targets require Pluck. An Always-only Configuration can continue to run without positional Target arguments.

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
