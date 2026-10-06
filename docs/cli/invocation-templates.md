# Invocation Templates

This page explains how to store, select, and override reusable CLI invocations in `.dirpluck-inv` documents. Exact document-selection and schema rules are defined in the [document-selection specification](../specification/document-selection.md), and runtime modifier combinations are defined in the [CLI contract](../specification/cli-contract.md).

## Invocation Template

Reusable CLI invocations can be stored in an Invocation Template `.dirpluck-inv` document. The root `[invocation]` is the default Invocation for the file, and `[invocation.<name>]` adds named Invocation entries.

```toml
[invocation]
config = "release"
targets = ["work/frontend/", "work/backend/"]

[invocation.docs]
config = "release"
targets = ["docs/"]
case = "publish"
archive_mtime = "zip-epoch"
```

`config`, `targets`, `case`, and `archive_mtime` are all optional in both the default Invocation and every named entry. A named entry is an independent Invocation, not a difference from the default Invocation, so omitted fields are not inherited from `[invocation]`. The names `config`, `targets`, `case`, and `archive_mtime` are reserved field names and cannot also be used as named Invocation entries. `targets` stores the same Target-reference grammar accepted as normal CLI positional arguments, including literal-list and regular-expression Target selectors. `config` may omit the `.dirpluck` suffix, just like CLI `--config PATH`; a relative path is resolved from the directory of the selected `.dirpluck-inv` path. Template paths and Configuration paths referenced by `config` follow the host OS's normal filesystem semantics even when they contain symbolic links or Windows directory junctions. When `config` is omitted, the runtime-cwd `default.dirpluck` is used; when `targets` is omitted, the run has no positional Targets; when `case` is omitted, normal default Case semantics apply; when `archive_mtime` is omitted, the normal per-entry timestamp behavior applies.

Select the Template file explicitly with `-i PATH` or `--invocation-template PATH`. `PATH` uses the same filesystem-path notation as `--config`: a relative path is resolved from the runtime cwd and an absolute path from the host filesystem. If the path does not end in `.dirpluck-inv`, that suffix is appended. Invocation Template document paths follow the host OS's normal filesystem semantics, and the directory of the selected path is the anchor for relative `config` paths inside the Template. The Invocation Template file itself has no implicit default and dirpluck does not search another directory for it.

Omitting `-e` / `--entry` selects the default `[invocation]`. `-e NAME` selects `[invocation.NAME]`. A file that contains only named entries still has an implicit parent `invocation` table in TOML, so omitting `-e` selects an empty default Invocation. A completely empty document is invalid because it has no `invocation` table at all.

```console
dirpluck -i release
dirpluck -i release -e docs
dirpluck -i invocations/release --entry docs --case audit
dirpluck --invocation-template ../shared/release --preview
```

An Invocation with no fields is valid. It contributes no stored execution inputs; execution uses CLI values and normal defaults. After a successful `--preview` or normal build, the CLI prints a note when the selected Invocation has no `config`, `targets`, `case`, or `archive_mtime`. This is informational rather than a warning because valid runs, including fixed-source-only and README-only builds, may need no stored Invocation values.

An Invocation Template is not a general difference-composition mechanism for stored invocations. Positional `TARGET` and `--config` cannot be combined with `-i` / `--invocation-template`. CLI `--case CASE` uses the same `PLUCK` / `.ALWAYS` / `PLUCK.ALWAYS` grammar and may override the selected Invocation's `case`, and `--archive-mtime VALUE` may override its `archive_mtime`. `--here`, `--output`, `--force`, `--preview`, `--sequence`, `--archive-mtime`, and `--paths` remain available as runtime modifiers, subject to their normal combination constraints. `-e` / `--entry` can be used only together with `-i` / `--invocation-template`.

A `.dirpluck-inv` document is not a Configuration and cannot be referenced by `about.base`. After the selected Invocation's Configuration, Targets, Case, and Archive-entry mtime policy are resolved, execution uses normal dirpluck semantics.
