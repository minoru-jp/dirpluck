# Runtime Targets, Scopes, and Cases

## SPEC_037

If the Effective Configuration contains a Pluck, one or more positional CLI `TARGET` references are required, preserving the existing contract. An Effective Configuration without a Pluck may still accept positional file Target references from Scopes with `target_kind = "file"` or `"both"`. If it has neither Pluck nor Always sources and contains only file-capable Scopes, one or more positional Target references are required for the run.

level: MUST

condition: depending on whether the Effective Configuration contains Pluck

## SPEC_038

Each positional reference resolves one or more Targets from the effective Scopes. The same effective Pluck selection is applied independently to each directory Target. A file Target does not use Pluck and instead includes the regular file itself as an atomic source. Resolving a directory Target without an effective Pluck is an error. Targets are not inferred automatically from the location of a Configuration file or from the origin of a Pluck definition.

level: MUST

## SECTION_501

title: Scope

### SPEC_039

The default Scope always exists and uses the directory containing the Root Configuration file as the Scope root. No special case is based on the directory name. `[scope]` configures the default Scope's optional `description` / `target_kind` / `ignore` / `namespace` and has no `path`. `target_kind` defaults to `"directory"`. Omitting `[scope]`, or writing an empty `[scope]`, means no description, directory Targets, an empty `ignore` list, and no Namespace reference.

level: MUST

related: [SPEC_030](composition.md#spec_030), [SPEC_032](composition.md#spec_032)

### SPEC_040

A named `[scope.<name>]` has a required `path` and optional `description` / `target_kind` / `ignore` / `namespace`. `target_kind` is `"directory"`, `"file"`, or `"both"` and defaults to `"directory"`. `path` is a concrete directory path; empty strings and globs are rejected. A relative `path` is resolved from the definition's Configuration-file directory according to the Filesystem path notation rules, while an absolute path refers directly to a directory on the host filesystem. The explicitly configured Scope-root location may contain symbolic links or Windows directory junctions; under the host OS's normal filesystem semantics, it must resolve to an existing directory. An alias used for the Scope root itself is distinct from link-like Target candidates discovered automatically directly under that resolved root. `description`, when present, is a non-empty string and does not change Target discovery or Archive placement.

level: MUST

related: [SPEC_018](paths.md#spec_018), [SPEC_024](paths.md#spec_024)

### SPEC_041

Whether a named Scope root exists and is a directory is checked only when that Scope is actually used by `SCOPE/NAME`, `SCOPE/NAME/`, `SCOPE/`, `SCOPE:[...]`, or `SCOPE:<...>`. The current filesystem availability of an unused named Scope does not fail the run. Duplicate effective Scope-root validation remains Configuration-level validation and does not require an unused Scope root to exist.

level: MUST

condition: when a named Scope is actually used

### SPEC_042

A Scope name is a non-empty name usable as one segment of a CLI Target reference. It must not contain `.`, `/`, or backslash; consequently `.` and `..` are also invalid.

level: MUST

### SPEC_043

The optional `namespace` of the default or a named Scope references an effective `[namespace.<name>]`. A Namespace reference does not change the Target discovery root, Target candidates, or CLI Target-reference semantics; it is used only for Archive placement. An unknown Namespace reference is a Configuration error.

level: MUST

### SPEC_044

`scope.ignore` case-sensitively matches direct-child Target-candidate names. A pattern without a trailing `/` applies to matching file and directory candidates; a pattern with a trailing `/` narrows the exclusion to directory candidates only. A matching entry cannot become a Target through single-Target selection, Scope expansion, or a Target selector. `target_kind` filters candidate types before this rule. This is independent of Selection `pluck.ignore` and `always.<name>.ignore`.

level: MUST

### SPEC_045

A Scope ignore pattern accepts the broad forms `name`, `name*`, `*name`, and `*name*`, plus corresponding directory-only forms with a trailing `/`. Broad forms apply to matching file and directory candidates. A bare `*`, `*/`, a path separator inside the body, backslash, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, and `!` are rejected. An empty array is valid.

level: MUST

## SECTION_502

title: CLI Target reference resolution

### SPEC_046

Each positional `TARGET` argument accepts the following forms:

```text
NAME
./NAME
./NAME/
SCOPE/NAME
SCOPE/NAME/
/
SCOPE/
:[ITEM/ITEM/...]
SCOPE:[ITEM/ITEM/...]
:<REGEX>
SCOPE:<REGEX>
```

For literal entry references, no trailing `/` means file and a trailing `/` means directory; the Target type is not inferred from the current filesystem. The `:[...]` / `SCOPE:[...]` and `:<...>` / `SCOPE:<...>` forms are Target selectors applied to eligible direct-child candidates and are valid with `target_kind = "directory"`, `"file"`, or `"both"`.

level: MUST

### SPEC_047

`NAME` or `./NAME` selects one direct-child **file** Target from the default Scope; `./NAME/` selects one direct-child **directory** Target from the default Scope. `SCOPE/NAME` selects a file Target and `SCOPE/NAME/` selects a directory Target from named Scope `SCOPE`. `/` expands all Targets from the default Scope, and `SCOPE/` expands all Targets from the named Scope. `:[...]` / `SCOPE:[...]` are typed literal Target lists, while `:<...>` / `SCOPE:<...>` are regular-expression selectors over normalized Target names.

level: MUST

### SPEC_048

`/` does not mean the filesystem root; it is the default-Scope expansion marker. Because `SCOPE/` is named-Scope expansion, a literal directory Target in the default Scope uses `./NAME/`. `./NAME` is accepted as the explicit default-Scope file form. `/NAME`, multi-level literal references such as `SCOPE/team/NAME`, and absolute filesystem paths are not accepted. Backslash is not accepted as a path separator in literal Target names or Target-list items. Inside a regular-expression selector, backslash may be used as a regex escape.

level: MUST

### SPEC_049

`NAME`, `./NAME`, `./NAME/`, `/`, `:[...]`, and `:<...>` use the always-present default Scope. The `SCOPE` in `SCOPE/NAME`, `SCOPE/NAME/`, `SCOPE/`, `SCOPE:[...]`, and `SCOPE:<...>` must exist as an effective named Scope; selector references and `SCOPE/` do not fall back to another relative-path interpretation.

level: MUST

### SPEC_050

Single-Target resolution requires a direct child that satisfies both the type declared by the syntax and the Scope's `target_kind`. A literal reference without a trailing `/` requires a regular file; a trailing `/` requires a regular directory. `target_kind = "directory"` rejects file references, `target_kind = "file"` rejects directory references, and `"both"` permits either. An entry recognized as a symbolic link or Windows directory junction is not selectable as a Target and is an error when referenced explicitly. Other special filesystem entries are also errors.

level: MUST

condition: when resolving a single Target

### SPEC_051

The Scope name is an identifier used for Target lookup and is not implicitly part of the archive path. An outer Archive directory is added only when the Scope explicitly references a Namespace.

level: MUST NOT

### SPEC_153

Target selector syntax is valid with `target_kind = "directory"`, `"file"`, or `"both"`, and operates only on candidates permitted by that Scope's type filter.

level: MUST

### SPEC_154

A list selector treats only the outermost `[` and `]` as selector syntax. An item without a trailing `/` denotes a file; an item with a trailing `/` denotes a directory. Because `/` is also the item separator, a non-final directory item appears as `NAME//NEXT`: one slash is the directory marker and the next is the separator. A final directory item appears as `NAME/]`. Three or more consecutive `/` characters, an empty list, an empty item, a missing closing `]`, a missing entry, an entry excluded by Scope `ignore`, or an entry type not permitted by the active `target_kind` is an error. Inner `[`, `]`, `<`, `>`, `,`, `:`, and similar characters are ordinary Target-name characters.

level: MUST

### SPEC_155

A regular-expression selector treats only its outermost `<` and `>` as selector syntax and compiles the contents as a Python-compatible regular expression. After Scope `ignore` and link-like-entry exclusion, the pattern is applied with full-match semantics to each eligible direct-child Target's normalized name. A regular-file candidate is matched as `NAME`; a regular-directory candidate is matched as `NAME/`. Ordinary regular-expression syntax such as `/?` can therefore select both types explicitly. The pattern must be non-empty and at most 512 characters. Invalid regular expressions and selectors that match zero eligible Targets are errors. `/` may appear as the directory type marker, but candidate discovery remains limited to direct children and never becomes recursive.

level: MUST

### SPEC_156

A Target selector does not replace Scope candidate discovery. The Scope first determines eligible direct-child Targets using its `target_kind` type filter, Scope `ignore`, regular-entry requirements, and link-like-entry exclusion. The selector is then applied to that eligible set. Selection is not recursive. In `both` mode, each resolved Target retains its actual directory/file kind.

level: MUST

### SPEC_157

`:` begins Target-selector syntax only when it appears at the Scope/selector boundary of a Target reference and is immediately followed by `[` or `<`. A `:` elsewhere, including inside the `NAME` portion of `SCOPE/NAME`, remains an ordinary literal Target-name character, preserving names such as `foo:bar` and `SCOPE/foo:[bar]`. If a literal default-Scope Target name has the same shape as selector syntax, it can be specified as one item in a list selector.

level: MUST

## SECTION_503

title: Scope expansion

### SPEC_052

`/` or `SCOPE/` enumerates direct-child entries of the corresponding Scope root and expands each eligible entry according to the Scope's `target_kind` and `ignore` into an independent Target. Directory mode includes only regular directories; file mode includes only regular files; both mode includes both. Enumeration is not recursive.

level: MUST

### SPEC_053

Ignored entries and entries recognized as symbolic links or Windows directory junctions are not treated as Target candidates. The destination of a recognized link-like entry is not resolved and is not included in `/` or `SCOPE/` expansion. Expansion that yields zero eligible direct children for the active `target_kind` is an error.

level: MUST

### SPEC_054

Multiple positional Target references, Scope expansions, and Target selectors may be combined in the same run.

level: MAY

### SPEC_158

If a Target selector overlaps a literal Target reference or another Target selector and resolves the same filesystem entry, that overlap is collapsed to one runtime Target. If only existing literal Target references duplicate the same filesystem entry and no selector is involved, the existing distinct-entry validation error is preserved.

level: MUST

## SECTION_504

title: Always source and Case

### SPEC_055

`[always.<name>].path` is a concrete directory path; empty strings and globs are rejected. A relative path is resolved from the definition's Configuration-file directory according to the Filesystem path notation rules. `.` and `..` may be used, and an absolute path refers directly to a directory on the host filesystem. The explicitly configured Always source-root location may contain symbolic links or Windows directory junctions and is resolved to an existing directory under the host OS's normal filesystem semantics. That resolved directory itself becomes the Selection boundary. The filesystem root itself is rejected as an Always source. An alias may be used for the root location, but link-like entries encountered later during Selection traversal below that root remain non-selectable and non-traversable under the link-like-entry rule in Filesystem boundary and entry types.

level: MUST

related: [SPEC_018](paths.md#spec_018), [SPEC_024](paths.md#spec_024), [SPEC_032](composition.md#spec_032)

### SPEC_056

An Always source may have an optional `namespace` string that references an effective `[namespace.<name>]`. It does not change the source filesystem path or Selection boundary. An unknown Namespace reference is a Configuration error.

level: MUST

### SPEC_057

Zero or one Case is active for the entire Effective Configuration and is selected by CLI `--case`. There is no field for choosing a different Case per layer.

level: MUST

### SPEC_058

Without a selected Case, Pluck uses `[pluck]` when present, and each Always source uses its base `[always.<name>]` selection.

level: MUST

condition: when no Case is specified

### SPEC_059

When a Case is selected and Pluck exists, a same-named `[pluck.case.<name>]` is required. Each Always source uses `[always.<name>.case.<name>]` when present and otherwise falls back to its base selection. If no Pluck exists, at least one Always source must define the selected Case name.

level: MUST

condition: when a Case is specified

### SPEC_060

A Case selection is a complete Selection, not a delta from its base Selection. It does not inherit `must`, `may`, `ignore`, Shared references, or `allow_empty`.

level: MUST
