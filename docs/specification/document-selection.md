# CLI document selection

## SPEC_002

A Configuration document filename ends in `.dirpluck`, while its contents use TOML syntax. When `--config` is omitted, the only Configuration dirpluck selects implicitly is `default.dirpluck` directly under the process cwd. It does not search another directory for `default.dirpluck`, search for differently named `*.dirpluck` files, or infer candidates from file contents. If `default.dirpluck` does not exist in the cwd, selection fails with a not-found error. No compatibility fallback to `.toml` files is provided.

level: MUST

## SPEC_003

When `--config PATH` is supplied, `PATH` is the path to one Configuration document and uses the lexical rules defined by Filesystem path notation. A relative path is resolved from the runtime cwd, while an absolute path identifies a host-filesystem location directly. If the path does not end in `.dirpluck`, that suffix is appended. Thus `release-1.2` identifies `release-1.2.dirpluck` in the cwd, and `configs/release-1.2` identifies `configs/release-1.2.dirpluck` under the cwd. A dot in the stem is not treated as a conflicting extension. Directory forms that contain no document name, such as a trailing `/`, `.`, or `..`, are not accepted. After resolution, dirpluck uses only that one path: it does not search another directory for a same-named file or accept a directory and complete it with `default.dirpluck`. The document path follows the host OS's normal filesystem semantics; a path containing a symbolic link or Windows directory junction is not rejected merely for that reason. After suffix completion and lexical conversion to an absolute path, dirpluck retains that selected path as the Configuration location and uses its directory as the anchor for relative filesystem paths inside the document. The destination must be an existing regular file.

level: MUST

condition: when `--config PATH` is specified

related: [SPEC_017](paths.md#spec_017), [SPEC_022](paths.md#spec_022), [SPEC_023](paths.md#spec_023)

## SPEC_004

An Invocation Template document filename ends in `.dirpluck-inv`. An Invocation Template file is used only when explicitly selected with `-i PATH` or `--invocation-template PATH`; the file itself has no implicit default. The lexical rules and relative / absolute resolution for `PATH` are the same as for `--config PATH`, so a relative path is resolved from the runtime cwd. If the path does not end in `.dirpluck-inv`, that suffix is appended. Thus `set-2.1` identifies `set-2.1.dirpluck-inv` in the cwd, and `invocations/release` identifies `invocations/release.dirpluck-inv` under the cwd. After resolution, dirpluck uses only that one path and does not search another directory. The document path follows the host OS's normal filesystem semantics; symbolic links and Windows directory junctions are not rejected merely for appearing in the path. After suffix completion and lexical conversion to an absolute path, the selected path is retained as the Invocation Template location.

level: MUST

## SPEC_005

A `.dirpluck-inv` document requires a top-level `invocation` table. A completely empty document or a document without top-level `invocation` is an error. A TOML `[invocation.<name>]` declaration implicitly creates its parent `invocation` table and therefore satisfies this requirement.

level: MUST

## SPEC_006

The root `[invocation]` is the default Invocation selected when `-e` / `--entry` is omitted. `[invocation.<name>]` is a named Invocation entry selected with `-e NAME` / `--entry NAME`. A named entry is an independent Invocation rather than a difference or derivative of the root Invocation; omitted fields are not inherited or merged from the root. The names `config`, `targets`, `case`, and `archive_mtime` are reserved for root-Invocation fields and are not accepted as named Invocation entry names. Selecting a named entry that does not exist is an error. `-e` / `--entry` is accepted only when an Invocation Template file is selected and may be specified at most once.

level: MUST

## SPEC_007

The default Invocation and each named entry accept only `config`, `targets`, `case`, and `archive_mtime`, and all four fields are optional. An Invocation with no fields is valid both in the schema and at execution time. `targets` is an array whose elements are non-empty CLI Target-reference strings resolved at execution time by the CLI Target reference grammar in Runtime Target, Scope, and Case. `case` is one non-empty Case selector using the same two-axis grammar as CLI `--case CASE`: `PLUCK`, `.ALWAYS`, or `PLUCK.ALWAYS`. `archive_mtime` uses the same string grammar as CLI `--archive-mtime VALUE` defined by the Archive entry timestamp rules in Output and acts as the runtime default for Archive-entry timestamps. `config` is a concrete Configuration document path. As with CLI `--config PATH`, `.dirpluck` is appended when the path does not already end in that suffix. It uses the Filesystem path notation: `/` is the separator and glob or backslash is not accepted. A relative `config` path is resolved from the directory of the selected Invocation Template location, while an absolute path refers directly to a host-filesystem location. Tilde expansion and environment-variable interpolation are not performed. Symbolic links and Windows directory junctions in control-document paths follow the host OS's normal filesystem semantics.

level: MUST

related: [SPEC_017](paths.md#spec_017), [SPEC_021](paths.md#spec_021), [SPEC_022](paths.md#spec_022), [SPEC_023](paths.md#spec_023)

## SPEC_008

When the selected Invocation omits `config`, dirpluck uses `default.dirpluck` in the runtime cwd. When it omits `targets`, the run has no positional Targets. When it omits `case`, normal default Case semantics apply. When it omits `archive_mtime`, normal Archive-entry timestamp semantics apply. If all four fields are omitted, CLI runtime values and those normal defaults are applied as usual. After a successful `--preview` or normal build in which the selected Invocation has no fields, the CLI emits a runtime note, not a warning, describing that state.

level: MUST

condition: when the selected Invocation omits a field

## SPEC_009

When an Invocation Template is selected, positional `TARGET` and `--config` are not accepted as differences or overrides. `--case` is accepted as an override of the selected Invocation's stored `case` and takes precedence when supplied. `--archive-mtime` is likewise accepted as an override of the selected Invocation's stored `archive_mtime`. `--here`, `--output`, `--force`, `--preview`, `--sequence`, `--archive-mtime`, and `--paths` may be combined with the Template subject to their normal constraints because they are runtime modifiers rather than differences to its other stored fields.

level: MUST

condition: when an Invocation Template is used

## SPEC_010

Base Configuration references do not use CLI document selection. Each Configuration names a concrete Configuration file path ending in `.dirpluck` directly in `about.base`. Base paths follow the host OS's normal filesystem semantics, and a relative base path is anchored to the directory of the referring Configuration location. A `.dirpluck-inv` document is not a Configuration and does not participate in the base chain.

level: MUST
