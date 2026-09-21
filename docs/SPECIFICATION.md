# dirpluck Specification

This document defines the exact compatibility-supported behavior of the `dirpluck` CLI, the `.dirpluck` Configuration document format, and the `.dirpluck-inv` Invocation Template document format. Both document types use TOML syntax. The official package-root Python API surface and the calling contract of `run()` are defined in [PYTHON_API.md](PYTHON_API.md); the Configuration, Target, Case, Invocation, and Archive semantics executed by `run()` are the same semantics defined here. For purpose and positioning, see [../README.md](../README.md). For term meanings, see [../GLOSSARY.md](../GLOSSARY.md). For TOML authoring, see [CONFIGURATION.md](CONFIGURATION.md). For CLI operation, see [CLI.md](CLI.md). For the trust boundary around Configurations, Invocation Templates, and filesystem operations, see [TRUST.md](TRUST.md).

## 1. Public surface

The compatibility-supported public surface is the `dirpluck` CLI, the `.dirpluck` Configuration and `.dirpluck-inv` Invocation Template document formats defined by this document, and the package-root Python API explicitly defined in [PYTHON_API.md](PYTHON_API.md). Both document types use TOML syntax. Python modules and names that are not explicitly exported from the package root are internal implementation.

## 2. CLI document selection

A Configuration document filename ends in `.dirpluck`, while its contents use TOML syntax. When `--config` is omitted, the only Configuration dirpluck selects implicitly is `default.dirpluck` directly under the process cwd. It does not search another directory for `default.dirpluck`, search for differently named `*.dirpluck` files, or infer candidates from file contents. If `default.dirpluck` does not exist in the cwd, selection fails with a not-found error. No compatibility fallback to `.toml` files is provided.

When `--config PATH` is supplied, `PATH` is the path to one Configuration document and uses the same lexical filesystem-location rules as Section 4. A relative path is resolved from the runtime cwd, while an absolute path identifies a host-filesystem location directly. If the path does not end in `.dirpluck`, that suffix is appended. Thus `release-1.2` identifies `release-1.2.dirpluck` in the cwd, and `configs/release-1.2` identifies `configs/release-1.2.dirpluck` under the cwd. A dot in the stem is not treated as a conflicting extension. Directory forms that contain no document name, such as a trailing `/`, `.`, or `..`, are not accepted. After resolution, dirpluck uses only that one path: it does not search another directory for a same-named file or accept a directory and complete it with `default.dirpluck`. The document path follows the host OS's normal filesystem semantics; a path containing a symbolic link or Windows directory junction is not rejected merely for that reason. After suffix completion and lexical conversion to an absolute path, dirpluck retains that selected path as the Configuration location and uses its directory as the anchor for relative filesystem paths inside the document. The destination must be an existing regular file.

An Invocation Template document filename ends in `.dirpluck-inv`. An Invocation Template file is used only when explicitly selected with `-i PATH` or `--invocation-template PATH`; the file itself has no implicit default. The lexical rules and relative / absolute resolution for `PATH` are the same as for `--config PATH`, so a relative path is resolved from the runtime cwd. If the path does not end in `.dirpluck-inv`, that suffix is appended. Thus `set-2.1` identifies `set-2.1.dirpluck-inv` in the cwd, and `invocations/release` identifies `invocations/release.dirpluck-inv` under the cwd. After resolution, dirpluck uses only that one path and does not search another directory. The document path follows the host OS's normal filesystem semantics; symbolic links and Windows directory junctions are not rejected merely for appearing in the path. After suffix completion and lexical conversion to an absolute path, the selected path is retained as the Invocation Template location.

A `.dirpluck-inv` document requires a top-level `invocation` table. A completely empty document or a document without top-level `invocation` is an error. A TOML `[invocation.<name>]` declaration implicitly creates its parent `invocation` table and therefore satisfies this requirement.

The root `[invocation]` is the default Invocation selected when `-e` / `--entry` is omitted. `[invocation.<name>]` is a named Invocation entry selected with `-e NAME` / `--entry NAME`. A named entry is an independent Invocation rather than a difference or derivative of the root Invocation; omitted fields are not inherited or merged from the root. The names `config`, `targets`, `case`, and `archive_mtime` are reserved for root-Invocation fields and are not accepted as named Invocation entry names. Selecting a named entry that does not exist is an error. `-e` / `--entry` is accepted only when an Invocation Template file is selected and may be specified at most once.

The default Invocation and each named entry accept only `config`, `targets`, `case`, and `archive_mtime`, and all four fields are optional. An Invocation with no fields is valid both in the schema and at execution time. `targets` is an array whose elements are non-empty CLI Target-reference strings resolved at execution time by the Section 6 grammar. `case` is one non-empty default Case name. `archive_mtime` uses the same string grammar as CLI `--archive-mtime VALUE` in Section 13 and acts as the runtime default for Archive-entry timestamps. `config` is a concrete Configuration document path. As with CLI `--config PATH`, `.dirpluck` is appended when the path does not already end in that suffix. It uses the same filesystem-location notation as Section 4: `/` is the separator and glob or backslash is not accepted. A relative `config` path is resolved from the directory of the selected Invocation Template location, while an absolute path refers directly to a host-filesystem location. Tilde expansion and environment-variable interpolation are not performed. Symbolic links and Windows directory junctions in control-document paths follow the host OS's normal filesystem semantics.

When the selected Invocation omits `config`, dirpluck uses `default.dirpluck` in the runtime cwd. When it omits `targets`, the run has no positional Targets. When it omits `case`, normal default Case semantics apply. When it omits `archive_mtime`, normal Archive-entry timestamp semantics apply. If all four fields are omitted, CLI runtime values and those normal defaults are applied as usual. After a successful `--preview` or normal build in which the selected Invocation has no fields, the CLI emits a runtime note, not a warning, describing that state.

When an Invocation Template is selected, positional `TARGET` and `--config` are not accepted as differences or overrides. `--case` is accepted as an override of the selected Invocation's stored `case` and takes precedence when supplied. `--archive-mtime` is likewise accepted as an override of the selected Invocation's stored `archive_mtime`. `--preview`, `--sequence`, `--archive-mtime`, and `--paths` may be combined with the Template subject to their normal constraints because they are runtime modifiers rather than differences to its other stored fields.

Base Configuration references do not use CLI document selection. Each Configuration names a concrete Configuration file path ending in `.dirpluck` directly in `about.base`. Base paths follow the host OS's normal filesystem semantics, and a relative base path is anchored to the directory of the referring Configuration location. A `.dirpluck-inv` document is not a Configuration and does not participate in the base chain.

## 3. Configuration schema

The accepted top-level structure is:

```text
[about]
[shared.must]
[shared.may]
[shared.ignore]
[pluck]
[pluck.case.<name>]
[scope]
[scope.<name>]
[namespace.<name>]
[always.<name>]
[always.<name>.case.<name>]
[output]
[output.timestamp]
```

Unknown keys are errors.

`[about]` is optional and may contain only `description` and `base`. Each field is independently optional, but if `[about]` is present, at least one must be present. `description` is a non-empty string. `base` is one Configuration file path.

Each Configuration layer may contain zero or one Pluck and zero or more named Scopes, Always sources, Shared patterns, and Namespaces. `[scope]` is an optional `ignore` / `namespace` configuration for the always-present default Scope of the Root Configuration; it is not a declaration that creates a Scope. Pluck and Always sources may contain zero or more Cases.

Each Configuration may declare zero or one Output. When Output is declared, fixed Output and timestamp Output are mutually exclusive. Output is not required for schema validity, archive planning, or `--preview`. A build that actually writes an Archive requires the Root Configuration to directly declare its own Output. Output from a Base layer is not inherited by the root.

A single Configuration layer may have no local source definition. After base composition, the Effective Configuration must contain at least one of Pluck or an Always source. The default Scope always exists for the Root Configuration, so an effective Pluck does not require a separate Scope declaration.

## 4. Filesystem path notation

Filesystem locations in Configuration / Invocation Template TOML fields and CLI `--config PATH` / `-i PATH` use `/` as the path separator regardless of the host OS. Backslash is not accepted as a separator; `/` is used on Windows as well.

A relative filesystem path written in a Configuration is resolved from the **directory containing the Configuration file in which that field is written**. This rule applies at least to:

```text
about.base
scope.<name>.path
always.<name>.path
output.path
output.timestamp.path
```

A relative path written in an inner Configuration of a base chain is resolved from the inner Configuration's own directory and is not rebased to an outer Configuration's directory.

An absolute path uses `/` separators in a root form recognized by the host OS as a complete absolute path and refers directly to that location. Examples include `/opt/data` on a POSIX host and `C:/data` or `//server/share/data` on a Windows host. `dirpluck` does not automatically convert a root form from another OS. A Windows drive-relative form such as `C:foo` is not treated as an absolute path.

Filesystem-location notation does not perform `~` expansion or environment-variable interpolation and does not accept globs. `.` and `..` are resolved as ordinary path components when they satisfy the field- or option-specific file or directory requirements. A Configuration or CLI document selection that uses an absolute path depends on the referenced filesystem and is not guaranteed to be portable across operating systems.

Only CLI `--config PATH` and `-i PATH` use the runtime cwd as the resolution base for relative paths. A `config` path inside either the default or a named Invocation is resolved from the Template document's own directory. Runtime cwd is not used to resolve relative filesystem paths after a Configuration has been loaded.

Paths that **select or reference Configuration / Invocation Template documents themselves** follow the host OS's normal filesystem semantics; symbolic links and Windows directory junctions are not rejected merely for appearing in the path. For the runtime-cwd `default.dirpluck`, `--config PATH`, `-i PATH`, `about.base`, and an Invocation's `config`, dirpluck keeps the selected or referenced path as a lexical absolute document location rather than replacing it with the physical path of a link target. Relative document references and relative filesystem locations written in that document are anchored to the directory of this document location. Only internal checks that need path identity, such as base-chain cycle detection, resolve aliases to a physical path so equivalent document-path aliases are recognized.

This control-document rule is separate from source-root resolution and source-tree link handling. Explicit source-root locations written by a Configuration, such as `[scope.<name>].path` and `[always.<name>].path`, follow the host OS's normal filesystem semantics and are not rejected merely because an intermediate or final path component is a symbolic link or Windows directory junction. After an explicit location resolves to an existing directory, that directory becomes the source root or Selection boundary. During the automatic Target discovery or Selection traversal that begins from that root, recognized link-like entries are not selected or traversed under Section 9. Values that are not filesystem locations, including include patterns, ignore patterns, archive paths, and CLI Target references, follow their own rules.

## 5. Base chain and composition

A Base Configuration is declared as `[about].base`. `base` is a concrete Configuration file path; empty strings and globs are rejected. A relative path is resolved from the current Configuration file's directory according to Section 4, while an absolute path refers directly to a file on the host filesystem. The path must end in `.dirpluck`, follows the host OS's normal filesystem semantics, and must resolve to an existing regular file whose contents are a valid TOML Configuration schema.

Each Configuration may reference zero or one base. If the Base Configuration has another `base`, the result is a linear chain. There is no fixed depth limit.

### Cycle detection

During base resolution, dirpluck keeps each Configuration's selected document location for diagnostics and relative-path resolution, while cycle identity is compared using the physical file path after symbolic-link or junction aliases are resolved. If another document-path alias resolves to the same physical Configuration path already active in the chain, resolution fails with a cycle error and the diagnostic shows the selected document-location chain. Depth alone does not produce an error or warning.

### Definition composition

The deepest layer is used as the initial value, and definitions from each successively outer layer are overlaid to form the Effective Configuration.

`[about].description` is searched from the outermost layer inward; the first defined value becomes the effective description. If no layer defines one, there is no effective description. `about.base` is a chain link and is not itself shadowed or merged as an effective value. A `[scope]` written in a Base layer configures the default Scope only when that Configuration itself is the Root; it is not inherited into an outer Root's default Scope.

- Pluck: an outer Pluck shadows the entire inner Pluck definition.
- Always source: an outer source shadows the entire same-named inner source; differently named sources remain.
- Named Scope: an outer Scope shadows the entire same-named inner Scope; differently named Scopes remain. The default Scope is not composed from the base chain; its root is determined from the Root Configuration location by the rule in Section 6, and only the Root Configuration's `[scope].ignore` / `namespace` is used.
- Namespace: an outer Namespace shadows the entire same-named inner Namespace; differently named Namespaces remain. Scope and Always Namespace references are resolved against the effective Namespace set after composition.
- Shared pattern: `must`, `may`, and `ignore` are independent namespaces. Within each namespace, an outer same-named pattern set shadows the entire inner array.

Pluck, Always, named-Scope, and Namespace shadowing is not a field-by-field partial merge. Cases belonging to a source definition are replaced together with that source definition.

A named-Scope root or Always-source path is resolved from the directory containing the Configuration file in which that definition is written. A definition that remains from a Base Configuration retains the resolution implied by its origin and is not rebased to an outer layer. The default Scope has no `path` field; its root is determined by the dedicated rule in Section 6.

After composition, no two effective Scopes may resolve and normalize to the same filesystem location. This duplicate check is performed without requiring every named Scope path to exist. The rule also applies between the default Scope and named Scopes. Distinct locations that are merely in an ancestor/descendant relationship are not duplicates under this rule.

Selection Shared references are resolved against the effective Shared namespace after the entire chain has been overlaid, not against the source's origin layer. An outer layer can therefore provide or shadow a same-named pattern set referenced by an inner source.

### Output and the base chain

Output definitions are not composed like source definitions. A Configuration may omit Output and still be used as a Base Configuration that contributes shared definitions. Archive planning and `--preview` do not require Root Output. In a build that actually writes an Archive, only the Output declared directly by the Root Configuration is used, and the build fails if the root has no Output. Output from an inner layer is not inherited by the root.

Within a base chain, only Configurations that actually declare Output contribute a write-ownership boundary, and Section 11 validates that those declared write boundaries do not overlap. A layer without Output has no write boundary.

## 6. Runtime Targets, Scopes, and Cases

If the Effective Configuration contains a Pluck, one or more positional CLI `TARGET` references are required. If it has no Pluck, positional Target references are not accepted.

Each positional reference resolves one or more Targets from the effective Scopes, and the same effective Pluck selection is applied independently to each Target. Targets are not inferred automatically from the location of a Configuration file or from the origin of a Pluck definition.

### Scope

The default Scope always exists and uses the directory containing the Root Configuration file as the Scope root. No special case is based on the directory name. `[scope]` only configures the default Scope's optional `ignore` / `namespace` and has no `path`. Omitting `[scope]`, or writing an empty `[scope]`, gives the default Scope an empty `ignore` list and no Namespace reference.

A named `[scope.<name>]` has a required `path` and optional `ignore` / `namespace`. `path` is a concrete directory path; empty strings and globs are rejected. A relative `path` is resolved from the definition's Configuration-file directory according to Section 4, while an absolute path refers directly to a directory on the host filesystem. The explicitly configured Scope-root location may contain symbolic links or Windows directory junctions; under the host OS's normal filesystem semantics, it must resolve to an existing directory. An alias used for the Scope root itself is distinct from link-like Target candidates discovered automatically directly under that resolved root.

Whether a named Scope root exists and is a directory is checked only when that Scope is actually used by `SCOPE/NAME` or `SCOPE/`. The current filesystem availability of an unused named Scope does not fail the run. Duplicate effective Scope-root validation remains Configuration-level validation and does not require an unused Scope root to exist.

A Scope name is a non-empty name usable as one segment of a CLI Target reference. It must not contain `.`, `/`, or backslash; consequently `.` and `..` are also invalid.

`scope.ignore` matches the **name** of a direct-child Target candidate directory case-sensitively. A matching directory cannot be selected as a Target either by single-Target selection or by expansion. This is independent of file-selection `pluck.ignore` and `always.<name>.ignore`.

A Scope ignore pattern has one of four forms: `name` (exact), `name*` (prefix), `*name` (suffix), or `*name*` (substring). A bare `*`, path separator, backslash, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, and `!` are rejected. An empty array is valid.

### CLI Target reference resolution

Each positional `TARGET` argument must have exactly one of these four forms:

```text
NAME
SCOPE/NAME
/
SCOPE/
```

`NAME` selects one directory directly under the default Scope. `SCOPE/NAME` selects directory `NAME` directly under named Scope `SCOPE`. `/` expands all Targets from the default Scope, and `SCOPE/` expands all Targets from named Scope `SCOPE`.

`/` does not mean the filesystem root. It is the expansion marker for the default Scope in the CLI Target-reference grammar. Alternative spellings such as `./`, `./NAME`, and `/NAME`, multi-level references such as `SCOPE/team/NAME`, absolute filesystem paths, and backslash separators are not accepted.

`NAME` and `/` use the always-present default Scope. The `SCOPE` in `SCOPE/NAME` and `SCOPE/` must exist as an effective named Scope; an unknown name does not fall back to another relative-path interpretation.

For single-Target resolution, the specified entry must be an existing directory that is a **direct child** of the Scope root. An entry recognized as a symbolic link or Windows directory junction is not selectable as a Target; an explicit `NAME` or `SCOPE/NAME` that names such a link-like entry is an error.

The Scope name is an identifier used for Target lookup and is not implicitly part of the archive path. An outer Archive directory is added only when the Scope explicitly references a Namespace.

### Scope expansion

`/` or `SCOPE/` enumerates direct-child directory entries of the corresponding Scope root and expands each entry not matched by the Scope's `ignore` into an independent Target. Directory enumeration is not recursive, and regular files are not Targets.

Ignored entries and entries recognized as symbolic links or Windows directory junctions are not treated as Target candidates. The destination of a recognized link-like entry is not resolved and is not included in `/` or `SCOPE/` expansion. Expansion that yields zero eligible directories is an error.

Multiple positional Target references and expansions may be combined in the same run.

### Always source and Case

`[always.<name>].path` is a concrete directory path; empty strings and globs are rejected. A relative path is resolved from the definition's Configuration-file directory according to Section 4. `.` and `..` may be used, and an absolute path refers directly to a directory on the host filesystem. The explicitly configured Always source-root location may contain symbolic links or Windows directory junctions and is resolved to an existing directory under the host OS's normal filesystem semantics. That resolved directory itself becomes the Selection boundary. The filesystem root itself is rejected as an Always source. An alias may be used for the root location, but link-like entries encountered later during Selection traversal below that root remain non-selectable and non-traversable under Section 9.

Zero or one Case is active for the entire Effective Configuration and is selected by CLI `--case`. There is no field for choosing a different Case per layer.

Without a selected Case, Pluck uses `[pluck]` when present, and each Always source uses its base `[always.<name>]` selection.

When a Case is selected and Pluck exists, a same-named `[pluck.case.<name>]` is required. Each Always source uses `[always.<name>.case.<name>]` when present and otherwise falls back to its base selection. If no Pluck exists, at least one Always source must define the selected Case name.

A Case selection is a complete Selection, not a delta from its base Selection. It does not inherit `must`, `may`, `ignore`, Shared references, or `allow_empty`.

## 7. Namespace

A Namespace is defined as a named `[namespace.<name>]` table. In the current schema the table must be empty and accepts no fields. A bare empty parent `[namespace]` does not define a Namespace and is an error.

The Namespace name itself becomes one directory component in the ZIP. Empty names, `.`, `..`, `/`, backslash, control characters, and `< > : " | ? *` are rejected. A Namespace is not a filesystem path; it is exactly one Archive-path component.

A Scope or Always `namespace` field references an effective Namespace name. For a source that references a Namespace, the final Archive root is `NAMESPACE/SOURCE_ROOT`. The prefix is always applied, regardless of whether another source would otherwise collide. A source without a Namespace keeps `SOURCE_ROOT` as its final Archive root.

Several sources may reference the same Namespace. A Namespace is not an automatic collision resolver; uniqueness of final Archive roots is validated by the Archive-planning rules in Section 10.

## 8. Selection and Shared patterns

A base or Case Selection for Pluck or an Always source requires at least one candidate across `must` and `may`. A candidate may be a direct pattern or a Shared reference. `description` is optional; when present, it must be a non-empty string.

Each item in `must` or `may` is either a direct pattern string or a one-element Shared-reference array.

```text
"foo"       direct pattern
["foo"]     Shared reference
```

A direct string in `ignore` is a name pattern. A one-element nested array is a reference marker: if its string begins with `./`, it is a Selection-relative path reference; otherwise it is a `shared.ignore` Shared reference.

```text
"*.pyc"                         direct name pattern
["python-noise"]               Shared ignore reference
["./tests/fixtures/big.bin"]   file path reference
["./tests/fixtures/"]          directory path reference
```

A nested array must contain exactly one non-empty string. `[]`, `["foo", "bar"]`, and `[123]` are errors. In `must` and `may`, nested arrays are reserved for Shared references.

The Shared-reference namespace is determined uniquely by the containing field:

```text
must   -> shared.must
may    -> shared.may
ignore -> shared.ignore
```

A Shared pattern definition value is a non-empty array of direct patterns. Shared references and path references cannot be nested inside Shared pattern definitions.

Shared references are resolved against the effective Shared namespace after base composition. An unknown Shared reference is a Configuration error. Shared references are expanded in Selection-array order into their referenced pattern sets. A path reference does not use the Shared namespace; it is interpreted from that Selection's source root.

Duplicate identical pattern/reference declarations within expanded `must`, `may`, or `ignore`, and duplicate include patterns across `must` and `may`, are Configuration errors. By contrast, semantic overlap where different ignore conditions match the same filesystem entry is valid; the effective exclusion is the union of all ignore conditions.

`allow_empty` is a boolean with default `false`. `allow_empty = true` may be specified only for a Selection that has no `must` patterns after Shared-reference expansion.

### Include pattern grammar (`must` / `may`)

A direct or expanded pattern in `must` or `may` is a `/`-separated relative path from the source directory. Absolute paths, escaping through `.` or `..`, and backslashes are rejected.

Each path element may contain at most one `*`. `*` matches zero or more characters within one concrete name and never crosses a path separator, so the path hierarchy depth written in the Configuration remains fixed.

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

A `must` pattern must match one or more **non-ignored selectable entries** or the Selection fails. A `may` pattern may match zero candidates. If a pattern matches several candidates, only those remaining after `ignore` become Selection candidates.

If the final matched entity is a regular file, that file is selected. If it is a regular directory, regular files below it are collected recursively subject to `ignore`. `ignore` takes precedence over diagnostics based on filesystem-entry type: ignored entries do not count as selectable matches, link-only or special-entry-only matches, or skipped-link entries. Recognized **non-ignored** symbolic links or Windows directory junctions are not selectable. If a pattern matches only such non-ignored link-like entries, `must` raises an explanatory error that distinguishes this case from an ordinary missing match, while `may` records it as optional missing.

A **non-ignored** filesystem entry that is neither a regular file nor a regular directory, such as a FIFO, socket, or device, is also not selectable and is not included in the Archive. If `may` matches only such entries, they are treated as optional missing. If `must` matches only such entries, it raises an explanatory error stating that only unsupported special filesystem entries matched. Special entries encountered while recursively collecting a regular directory are silently excluded rather than traversed or archived. No implicit ignore is inferred from contents or filename meaning.

Matching is case-sensitive independently of the OS. `**`, `?`, character classes (`[]`), and `!` are unsupported. Multiple matches are not ranked by version, mtime, or other metadata.

### Ignore grammar

Selection `ignore` has two forms: name patterns and concrete Selection-relative path references.

A direct string matches one entity name case-sensitively. A pattern ending in `/` applies to a directory name; a pattern without `/` applies to a file name. Supported forms are:

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

A directory name pattern appends `/` to that body:

```text
.git/
__pycache__/
tmp-*/
```

A Selection-relative path reference is a one-element nested array whose string begins with `./`. For Pluck, the Selection root is the Target directory. For an Always source, it is the resolved Always-source directory. A trailing `/` denotes a concrete directory path; without the trailing `/`, the reference denotes a concrete file path. Dirpluck does not infer file-versus-directory meaning from current filesystem state.

```text
["./tests/fixtures/big.bin"]   exact file path
["./tests/fixtures/"]          exact directory path and its subtree
```

A path reference must stay inside the Selection root. Bare `./`, `..` components, absolute paths, globs, and backslashes are rejected; `/` is the separator. A matching directory path reference prunes that directory before subtree traversal. A file path reference excludes only the exact file path.

Name patterns, expanded Shared ignores, and path references are applied as a union of exclusion conditions. Several different conditions may match the same entry without error, and evaluation order is not observable semantics. Implementations may prune a subtree as soon as a directory exclusion matches.

`ignore` takes precedence over link-like and special-entry diagnostics. Ignored entries are not Selection candidates, do not cause link-only or special-entry-only errors, and are not included in the skipped-link count. Entries inside an ignored subtree are not enumerated or subjected to traversal-time validation. A name pattern without a trailing `/` also applies to a special filesystem entry with the same name. If a path reference matches a link-like entry itself, that entry is likewise treated as ignored.

For name patterns, a bare `*`, `*/`, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, `!`, backslash, and a path separator inside the body are rejected. Path references have no wildcard syntax.

## 9. Filesystem boundaries and non-regular entries

A Configuration file's directory is the resolution anchor for relative Configuration paths; it is not a shared boundary that confines all sources beneath it.

A runtime Target directory is resolved as a direct child of its corresponding Scope root. The Scope root is the base for finding Target candidates, while the boundary for selected files is the resolved Target directory itself.

Explicit named-Scope and Always source-root locations may resolve an existing directory through a relative or absolute `path` using the host OS's normal filesystem semantics, including locations that contain symbolic links or Windows directory junctions. For an Always source, the resolved source directory itself becomes the Selection boundary. Output locations do not participate in source boundaries.

Include resolution and selected files for each source are confined to that source directory. Only regular files are included in the Archive; regular directories are used only for traversal. An entry recognized as a symbolic link during Target discovery or Selection traversal is not selectable: `dirpluck` does not resolve or traverse its target and does not include the link in the Archive. On Windows, directory junctions are treated as the same kind of link-like entry. File symlinks, directory symlinks, broken symlinks, and recognized Windows directory junctions are all non-traversable. Other non-regular entries such as FIFOs, sockets, and devices are likewise not archived and are not traversed as directories.

To recognize Windows directory junctions while retaining Python 3.11 support, `dirpluck` uses the reparse tag returned by `lstat` on Windows. The decision is centralized in one internal helper used by Target discovery, Selection traversal, and other runtime filesystem checks that reject link-like entries. Control-document path resolution does not use this link-like test. If a supported Windows runtime cannot provide the reparse-tag constant or stat metadata required to distinguish junctions safely, `dirpluck` fails instead of treating the entry as an ordinary directory and continuing traversal. This is a safety boundary for known symbolic links and directory junctions; it does not guarantee complete detection of every possible reparse point or unknown redirection mechanism available on a platform.

Recognized **non-ignored** link-like entries excluded during Selection traversal are counted once per path even if the same path is observed through multiple patterns. `--preview` reports the total after the contents tree, and a normal build reports it after the output path. Individual link paths are not displayed, and the runtime note is not written to the Archive `README.md`. Link-like entries that match `ignore`, and entries inside a subtree pruned by directory `ignore`, are not included in the skipped-link count.

This rule applies to entries encountered while automatically traversing a source tree from its root. Explicit filesystem paths such as `about.base`, named Scope `path`, Always `path`, and Output `path` follow the path-resolution rules in Section 4 and their respective sections. In particular, an alias may be used for a named Scope or Always root location without implying that Target discovery or Selection traversal may follow another link-like entry below that root. Interpretation of entries or filesystem objects when the generated ZIP is extracted depends on the extractor and platform; `dirpluck` does not guarantee the behavior of third-party extraction software.

## 10. Archive planning

For a Target resolved through a Scope, the source root is the one-segment Target directory name. The logical Scope name is not implicitly included in the archive path.

An Always source's source root is derived from the source location explicitly written in the Configuration rather than from the physical target directory. If that source location is beneath the directory containing the Configuration file in which its definition is written, the source root is its lexical path relative to that Configuration directory. If an absolute path or `..` places the source location outside that base, the final directory name of the explicit location becomes the source root. When the final component is a symbolic link or Windows directory junction whose physical target has a different directory name, the Archive retains the explicit location's name. The filesystem root itself is rejected as an Always source because it has no such portable source root. Host absolute paths, drive names, and UNC share names themselves are not embedded in archive paths.

For a source without a Namespace, the final Archive root is the source root. For a source with a Namespace, the final Archive root is `NAMESPACE/SOURCE_ROOT`, and selected file paths relative to the source directory are placed beneath it. The Namespace is applied whenever it is configured, not only when a collision actually occurs.

If different resolved sources in one run resolve to the same final Archive root, planning fails with an ambiguity error even when their selected files would not directly collide. `dirpluck` does not silently merge sources into one directory and does not add automatic suffixes or implicitly qualify paths with Scope or Always names. Configure a Namespace when the final Archive roots need to be distinguished.

After final Archive roots are known to be unique, planning still rejects different physical files that collide at the same archive path, and rejects the same physical file when different source mappings place it at different archive paths. If the same physical file maps to the same archive path more than once, it is written once.

The root-level `README.md` path is reserved for the Archive index generated by `dirpluck`. If the first component of a resolved source's final Archive root matches `README.md` case-insensitively, planning fails instead of placing a source at or below that reserved path. This applies both to Namespace-derived roots and to source roots with no Namespace.

An Archive README is generated as `README.md` at the Archive root. It is an index of Archive contents, not a `dirpluck` resolution report. If an effective `[about].description` exists, its text appears immediately after `# Archive contents`. If none exists, that overall description is omitted.

Each resolved source is represented by one level-2 heading whose inline-code text is the final Archive root. The section records the selected file count as `Files: N`. When the Selection has a `description`, that text appears after the metadata as the section body. Descriptions are not compressed into table cells, so multi-line descriptions remain usable as section content. A source without a description has no description body.

When at least one source uses a Namespace, the README first explains that a Namespace is an Archive-only outer directory and is not part of the original source path, and that the source root is immediately below it. Each namespaced source section also records its `Namespace` and `Source root`; sources without a Namespace omit that metadata.

By default, the README does not record source filesystem paths, Configuration path/table, base chain, Scope/Pluck/Always names, selected Case, or similar `dirpluck`-specific information. Only CLI `--paths` adds a `Source` value to each source section containing the resolved source directory as a `/`-separated filesystem path. `--paths` does not change archive paths or file selection.

## 11. Output

A Configuration may omit Output. A Configuration without Output may also be used as the Root for archive planning or `--preview`. A build that actually writes an Archive requires the Root Configuration to directly declare exactly one of fixed Output or timestamp Output. Base Output is not inherited as the Root Output. Runtime checks of Output filesystem state, directory creation, and Archive writing are performed only for the Root Configuration's own Output during a build.

Within a base chain, only definitions that actually declare Output participate in write-boundary overlap validation. Relative Output paths are always resolved from the directory containing the Configuration file in which that Output is written.

### Fixed Output

```toml
[output]
path = "artifacts/context.zip"
overwrite = false
```

`path` is required. `overwrite` is an optional boolean and defaults to `false`. A `timestamp` subtable, `prefix`, and `suffix` cannot be specified in fixed mode.

`path` is a concrete file path. Directory notation ending in `/`, globs, and destinations that resolve as directories are rejected. Relative paths may resolve `.` and `..` normally. Required parent directories are created. The Output location is not restricted by a Configuration-directory boundary.

With `overwrite = false`, `dirpluck` checks that the destination does not exist both before the build and immediately before final placement. If an existing destination is observed at either check, the run fails without modifying that existing output. These existence checks and final placement are not a single atomic no-clobber operation against concurrent writers. If another process creates or replaces the same destination after the final check and before placement, `dirpluck` may replace that file.

With `overwrite = true`, the new ZIP is completed in a temporary file in the output directory before replacing the existing output. The existing destination's file mode is not inherited.

The generated Archive file follows the host OS's normal new-file creation semantics. On POSIX, the temporary output is created with the regular-file creation mode `0666` subject to the process `umask`, and that mode is preserved when it is moved into the final destination. New output and overwrite therefore both use a new-file mode derived from the `umask` of that run.

The filename extension is not used to determine ZIP format. In fixed mode, the filename written in the Configuration is not changed or expanded at runtime.

### Timestamp Output

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` is required. `prefix` and `suffix` are optional. `overwrite` cannot be specified.

`path` is a concrete directory path and must end in `/` in Configuration notation. Globs are rejected. Relative paths may resolve `.` and `..` normally. Required directories are created. The Output location is not restricted by a Configuration-directory boundary.

`prefix` and `suffix` are each one non-empty portable filename fragment. `.`, `..`, path separators, control characters, and `< > : " | ? *` are rejected.

The generated filename has this fixed form:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

The timestamp uses process local time and is determined once at build start. Arbitrary timestamp formats, variable expansion, and naming templates are not provided.

`N` is an integer of 1 or greater supplied by CLI `--sequence N`. When omitted, no number segment is emitted. `dirpluck` does not inspect existing outputs to infer a number and does not perform automatic numbering or automatic renaming. `--sequence` may be used only with timestamp Output.

If the generated filename already exists at the point it is checked, the run fails. Timestamp Output has no overwrite option. The generated Archive file uses the same host-OS new-file permission and mode semantics as fixed Output.

### Archive entry timestamp

`--archive-mtime VALUE` controls ZIP-entry timestamp metadata, not the Output path or filename. There is no corresponding Configuration field. The policy may be supplied as a CLI or Python-API runtime option, or stored as `archive_mtime` in an Invocation Template.

`VALUE` is `now`, `zip-epoch`, or a strict `YYYY-MM-DDTHH:MM:SS` string. An explicit timestamp is interpreted as a timezone-free literal; no timezone suffix, offset, or conversion is accepted. The supported range is the ZIP/DOS timestamp range from `1980-01-01T00:00:00` through `2107-12-31T23:59:59`. `zip-epoch` is equivalent to `1980-01-01T00:00:00`. `now` samples process-local current time once for the high-level run and uses that single value.

ZIP timestamps have two-second precision. If the resolved timestamp has an odd second, dirpluck rounds it down to the preceding even second; microseconds are discarded. The resolved timestamp is then applied uniformly to every ZIP entry written by that run, including the generated root `README.md`, empty-directory entries, and selected source files.

When `--archive-mtime` and Invocation `archive_mtime` are both omitted, existing semantics are preserved: selected source files use their filesystem mtimes, while entries generated by dirpluck use their generation time.

This option fixes entry timestamps so timestamp-driven byte differences can be removed. Source-file permission bits are retained in ZIP `external_attr`, so Archives with identical file contents and timestamps can still differ in bytes when those permissions differ. dirpluck does not normalize permission bits. It also does not guarantee byte-for-byte reproducibility across compressor implementations, runtime versions, platforms, or other ZIP metadata and serialization details. It is also independent of the process-local `YYYYMMDD-HHMMSS` used in timestamp Output filenames and does not change that filename timestamp. In preview mode no Archive is written, so archive mtime has no effect on the preview result.

### Static writable destination

Output naming maintains the invariant that the write boundary can be determined statically from the Configuration alone.

```text
fixed [output]
    -> one resolved complete file path

timestamp [output.timestamp]
    -> the directory tree rooted at the resolved output directory
```

With fixed Output, the user determines the entire filename and `dirpluck` does not fill in part of it at runtime. With timestamp Output, the user determines the output directory and `dirpluck` determines only a filename directly under that directory. Template modes such as `artifacts/{target}-{timestamp}.zip`, where the writable directory cannot be determined statically from the Configuration, are not provided.

### Base-chain write-boundary overlap

The resolved write boundary declared by each Configuration in a base chain must not overlap another Output in that chain. Comparison is performed on paths resolved and normalized using each Configuration file as its anchor, not on the strings written in TOML.

Two fixed Outputs conflict only when their complete file paths are identical. Different fixed filenames may share the same directory.

```text
out/base.zip
out/derived.zip
```

Two timestamp Outputs conflict when their directory boundaries are equal or one is an ancestor or descendant of the other.

```text
artifacts/
artifacts/release/
```

A fixed Output conflicts with a timestamp Output when the fixed Output's complete file path lies within the timestamp Output's directory boundary.

```text
artifacts/            timestamp boundary
artifacts/result.zip  fixed output -> conflict
```

This validation is limited to the one base chain currently being resolved. `dirpluck` does not search for or guarantee against unrelated Configuration chains declaring the same filesystem location.

### Concurrent writes and input collision

`dirpluck` does not provide inter-process locking or conflict arbitration. Concurrent writes to the same output path are unsupported. The existing-destination checks used by fixed Output with `overwrite = false` and by timestamp Output are not atomic no-clobber guarantees against another process. Callers that may run concurrently must choose different output destinations.

In either Output mode, the final output file generated by the run cannot itself be selected as an Archive input.

## 12. Preview

`--preview` uses the same base-chain resolution, cycle detection, definition composition, Scope lookup and expansion, Target direct-child resolution and Scope-ignore filtering, Case selection, file selection, and archive planning as a normal run, but does not create or modify output files or directories. It can be used when the Root Configuration has no Output declaration. Because preview does not generate an output filename, `--preview` cannot be combined with `--sequence`. `--archive-mtime` is still validated in preview mode, but no Archive is written, so it does not affect the preview result.

A missing `must` pattern is displayed as `[missing]`; a missing `may` pattern is displayed as `[optional missing]`. A final Selection containing zero files is displayed as either `empty, allowed` or `empty, would error` according to policy.

Configuration and planning errors remain errors in preview mode, including an invalid base path, base cycle, duplicate effective Scope root, an unavailable Scope root that is actually used, unknown Scope, invalid Target reference, Target outside the direct-child boundary, unresolved Shared reference, invalid source path, Case inconsistency, and Output schema or base-chain write-boundary conflict. An unused named Scope root being currently unavailable is not by itself an error. Base depth itself is not an error or warning.

## 13. CLI contract

The main accepted CLI forms are:

```console
dirpluck TARGET [TARGET ...]
dirpluck --config PATH
dirpluck TARGET [TARGET ...] --case NAME
dirpluck --config PATH --case NAME
dirpluck -i PATH [-e NAME] [--case NAME]
dirpluck --invocation-template PATH [--entry NAME] [--case NAME]
dirpluck ... --preview
dirpluck ... --paths
dirpluck ... --sequence N
dirpluck ... --archive-mtime VALUE
dirpluck --version
```

If the Effective Configuration contains a Pluck, positional arguments are resolved as `TARGET` references according to Section 6. If it has no Pluck, positional `TARGET` arguments are not accepted.

`--case`, `--sequence`, `--archive-mtime`, `-i` / `--invocation-template`, and `-e` / `--entry` may each be specified at most once. `-e` / `--entry` is accepted only together with an Invocation Template. When an Invocation Template is selected, positional `TARGET` and `--config` are not accepted. `--case` may be combined with an Invocation Template and overrides the selected Invocation's `case` when supplied. `--archive-mtime VALUE` may also be combined with a Template and overrides the selected Invocation's `archive_mtime`; `VALUE` follows the Archive-entry timestamp grammar in Section 11. `--sequence` accepts an integer of 1 or greater and cannot be combined with `--preview`. `--preview`, `--sequence`, `--archive-mtime`, and `--paths` may also be combined with an Invocation Template. `--paths` adds `Source` metadata to each source section in the Archive README generated by a normal build. When combined with `--preview`, no Archive is generated, so it does not add source filesystem paths to the displayed tree.

Argument-parsing errors and `dirpluck` Configuration/build errors exit with status 2. Successful builds and informational commands exit with status 0. A successful normal build prints the final output path to standard output. If the selected Invocation has no fields, a successful normal build prints an informational note after the output path, while `--preview` prints it after the tree; the note states that no stored Invocation inputs were provided and execution uses CLI runtime values and normal defaults.

No additional CLI path is provided for the base chain and no per-layer Case option is provided. The base chain is defined by TOML `about.base`, and a Case is applied to the composed Effective Configuration.
