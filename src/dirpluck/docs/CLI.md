# dirpluck CLI Quick Reference

This is the compact CLI reference included in the wheel.

```text
dirpluck [TARGET ...] [--config PATH] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck -i PATH [-e NAME] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck --version
```

- Supply one or more positional `TARGET` references when the Effective Configuration has a Pluck. Supply none when it has no Pluck.
- `project` selects `project` directly under the always-present default Scope; `work/project` selects `project` directly under named Scope `work`. The default Scope root is always the Root Configuration file's directory. A Target is limited to a direct child directory of its Scope root.
- `/` expands every eligible directory under the default Scope into Targets; `work/` does the same for named Scope `work`. Directories matching the Scope's `ignore` are excluded. An unknown Scope is an error. Unused named Scope roots are not required to exist.
- Without `--config`, dirpluck automatically uses only `default.dirpluck` in the cwd. `--config PATH` explicitly selects one Configuration document by a relative path from the cwd or an absolute path on the host filesystem and does not search another directory. If `PATH` does not end in `.dirpluck`, that suffix is appended, so paths such as `release-1.2` and `configs/release-1.2` are valid. Document paths follow the host OS's normal filesystem semantics, including symbolic links and Windows directory junctions; the selected document-path location remains the anchor for relative document references. Use `/` as the path separator even on Windows. There is no `.toml` compatibility fallback.
- `--case NAME` selects one named Case.
- `-i PATH` / `--invocation-template PATH` explicitly selects one `.dirpluck-inv` Invocation Template file by a relative path from the cwd or an absolute path on the host filesystem and does not search another directory. Document paths follow the host OS's normal filesystem semantics, including symbolic links and Windows directory junctions. If `PATH` does not end in `.dirpluck-inv`, that suffix is appended. Root `[invocation]` is the default Invocation selected when `-e` is omitted; `[invocation.<name>]` is a named Invocation selected with `-e NAME` / `--entry NAME`. Each Invocation independently stores optional `config` / `targets` / `case` / `archive_mtime`; named entries do not inherit fields from the root. These field names are reserved and cannot also be used as entry names. Relative `config` paths are anchored to the selected Template path's directory and may omit the `.dirpluck` suffix; control-document paths follow normal host filesystem semantics. An Invocation with no fields is valid, uses CLI runtime values and normal defaults, and produces an informational note after a successful preview or build. Do not combine a Template with positional `TARGET` or `--config`. CLI `--case NAME` overrides the selected Invocation's `case`, and `--archive-mtime VALUE` overrides its `archive_mtime`. `--here`, `--output`, `--force`, `--preview`, `--sequence`, `--archive-mtime`, and `--paths` remain available as runtime modifiers, subject to their normal combination constraints.
- `--here` writes to the cwd using `dirpluck-YYYYMMDD-HHMMSS.zip` by default. When the Root Configuration has `[output.timestamp]`, its `prefix` / `suffix` naming rule is reused. `--here=FILENAME` writes that filename directly under the cwd and does not accept path components.
- `-o PATH` / `--output PATH` selects Runtime Output. A trailing `/` means directory plus automatic timestamp filename; otherwise `PATH` is the exact output file path. Relative paths use the cwd, `/` is the separator even on Windows, and backslashes are rejected. `--here` and `--output` are mutually exclusive.
- `-f` / `--force` makes the effective Output overwriteable. Runtime Output defaults to no-overwrite, and `--force` also applies to Configuration fixed / timestamp Output. Automatic-name collisions are errors without `--force`; no automatic renaming is performed.
- `--preview` shows the planned ZIP contents without writing an Archive. The selected Root Configuration may omit Output, but because preview does not resolve or write an Output, it cannot be combined with `--here`, `--output`, `--force`, or `--sequence`. If Selection traversal excludes recognized non-ignored symbolic links or Windows directory junctions, preview reports the skipped count; a normal build reports the same count after the output path. Entries matched by `ignore` are not counted.
- `--paths` adds resolved source filesystem paths to the generated Archive README. Paths are omitted by default.
- `--sequence N` supplies an explicit positive sequence number for an automatic timestamp output name. It is not automatic numbering and cannot be used with an exact Runtime Output.
- `--archive-mtime VALUE` assigns one timestamp to every ZIP entry. `VALUE` is `YYYY-MM-DDTHH:MM:SS`, `now`, or `zip-epoch`. Explicit timestamps must be within ZIP's 1980..2107 range; odd seconds are rounded down to two-second precision. `zip-epoch` is `1980-01-01T00:00:00`, while `now` samples local current time once per run. Omitting the option preserves normal per-entry timestamps. A fixed timestamp can help produce reproducible archives, but source-file permission bits and other metadata can still change the ZIP bytes; dirpluck does not normalize those permission bits or guarantee byte-for-byte reproducibility. It does not change timestamp Output filenames.

```console
dirpluck example --preview
dirpluck work/example --case audit
dirpluck /
dirpluck work/
dirpluck --config snapshot
dirpluck -i release
dirpluck -i release -e docs
```

For the compact TOML reference, see the bundled `CONFIGURATION.md`; for the trust model, see the bundled `TRUST.md`. For detailed CLI semantics, the Configuration guide, the Glossary, and the Specification, see `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, and `docs/SPECIFICATION.md` in the source distribution for the same release.
