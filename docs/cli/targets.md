# Targets and Cases

This page explains positional Target references, Scope expansion, and Case selection from the CLI. For authoring Scope and Namespace declarations, see [Configuration sources](../configuration/sources.md). For authoring Cases, see [Configuration selection](../configuration/selection.md). Exact Target and Case semantics are defined in the [runtime-targets specification](../specification/runtime-targets.md).

## Specifying Targets

A positional `TARGET` resolves a directory, a regular file, or either kind according to the Scope's `target_kind`. The effective Pluck selection is applied independently to each directory Target. A file Target is included as an atomic file and does not use Pluck.

Literal Target references declare the entry type in the syntax. No trailing `/` means file; a trailing `/` means directory. Dirpluck does not infer that type from the current filesystem. In the default Scope, `NAME` or `./NAME` denotes a file and `./NAME/` denotes a directory. `NAME/` is reserved for named-Scope expansion, so default-Scope directories use the explicit `./` form. The default Scope always uses the directory containing the Root Configuration file as its root.

```console
dirpluck ./acme/ ./contoso/
```

In a named Scope, `<scope>/<name>` denotes a file and `<scope>/<name>/` denotes a directory.

```console
dirpluck work/acme/
```

`work/acme/` selects only directory `acme/` directly under Scope `work`. If Scope `work` is undefined, the command fails instead of falling back to another relative-path interpretation. A syntax-declared type that the Scope's `target_kind` does not permit is also an error. If a literal Target requests one type but an entry of the other type exists at the same name, the error diagnostic suggests adding or removing the trailing `/`.

To select every eligible Target directly under a Scope, use an expansion form.

```console
dirpluck /
dirpluck work/
```

`/` expands the default Scope, while `work/` expands named Scope `work`. `/` does not mean the filesystem root. With `target_kind = "directory"`, expansion includes only eligible direct-child directories. With `target_kind = "file"`, it includes only eligible direct-child regular files. With `target_kind = "both"`, it includes both. Expansion is never recursive, and candidates matching the Scope's `ignore` are removed. A missing named-Scope path does not affect a run that does not use that Scope.

Target selectors are available with every `target_kind`. `[...]` is a typed literal Target list. Each item uses the same type rule: no trailing `/` means file and a trailing `/` means directory. `/` is also the item separator, so a non-final directory item naturally produces two consecutive slashes: one directory marker and one separator. Three or more consecutive slashes are invalid. Only the outermost `[` and `]` are selector syntax; brackets and similar characters inside an item remain ordinary Target-name characters.

```console
dirpluck 'work:[repo-a//repo-b.zip]'
```

The example selects directory `repo-a/` and file `repo-b.zip`.

`<...>` is a regular-expression selector. Eligible direct-child files are matched as `NAME`, while directories are matched as `NAME/`. The Python-compatible regular expression is applied to that complete normalized name with full-match semantics. Therefore `<repo>` selects a file, `<repo/>` selects a directory, and `<repo/?>` can select either type explicitly. The pattern must be non-empty and no more than 512 characters. Invalid regular expressions and selectors that match no eligible Targets are errors. `/` may appear in the expression, but candidate discovery remains limited to direct children of the Scope and is never recursive.

This regular-expression Target selector has a different role from ordinary Selection strings. Ordinary Selection strings control predictable directory traversal and name-based exclusion; when needed, Selection also provides `{ match = "..." }` for regular expressions over full root-relative paths. By contrast, a `<...>` Target selector only performs additional filtering over normalized eligible direct-child Target names. See [Configuration selection](../configuration/selection.md) for ordinary Selection patterns and structured `match`.

```console
dirpluck 'work:<repo-.*/?>'
```

For the default Scope, forms such as `:[file-a/dir-b/]` and `:<regex>` are available. For a named Scope, use forms such as `work:[file-a/dir-b/]` and `work:<regex>`. Selector syntax is valid with `target_kind = "directory"`, `"file"`, or `"both"`. The Scope type filter, `ignore`, and link-like-entry exclusion determine the eligible Targets before the selector is applied. In `both` mode, directory results use Pluck while file results remain atomic sources.

When invoking dirpluck from a shell, quote the entire selector reference so the shell does not interpret `[]`, `<>`, or regular-expression metacharacters.

`./` by itself, `/acme`, `work/team/acme`, and absolute filesystem paths are not accepted as Target references. `./acme` and `./acme/` are valid explicit default-Scope file and directory forms, respectively.

Target references may be omitted entirely. A targetless run does not use Pluck for source selection; if ordinary Always sources or Extra sources activated by the selected Always Case through `include` / `add` participate, it archives only those fixed sources. If no fixed source participates, the run is still valid and produces a README-only Archive. A Configuration without a Pluck may still select file Targets from Scopes with `target_kind = "file"` or `"both"`. Directory Targets require Pluck.

```console
dirpluck --config project-snapshot
```

For Scope and `ignore` definitions, see [Configuration guide](../configuration/INDEX.md). For exact Target-reference, boundary, and archive-path rules, see [Specification](../specification/INDEX.md).

## Case

Select Cases with `--case CASE`. The selector has independent Pluck and Always axes: `PLUCK` selects only a Pluck Case, `.ALWAYS` selects only an Always Case, and `PLUCK.ALWAYS` selects both. An Always Case selects participating Always sources and can activate Extra sources.

```console
dirpluck ./acme/ --case audit
dirpluck --case .release
dirpluck ./acme/ --case audit.release
```

The two axes are validated independently. A defined Case may validly result in zero sources. [Specification](../specification/INDEX.md) defines the Configuration semantics for Pluck and Always Cases.
