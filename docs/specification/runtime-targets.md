# Runtime Targets, Scopes, and Cases

## SPEC_037

If the Effective Configuration contains a Pluck, one or more positional CLI `TARGET` references are required, preserving the existing contract. An Effective Configuration without a Pluck may still accept positional file Target references from Scopes with `target_kind = "file"`. If it has neither Pluck nor Always sources and contains only file-kind Scopes, one or more positional Target references are required for the run.

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

A named `[scope.<name>]` has a required `path` and optional `description` / `target_kind` / `ignore` / `namespace`. `target_kind` is `"directory"` or `"file"` and defaults to `"directory"`. `path` is a concrete directory path; empty strings and globs are rejected. A relative `path` is resolved from the definition's Configuration-file directory according to the Filesystem path notation rules, while an absolute path refers directly to a directory on the host filesystem. The explicitly configured Scope-root location may contain symbolic links or Windows directory junctions; under the host OS's normal filesystem semantics, it must resolve to an existing directory. An alias used for the Scope root itself is distinct from link-like Target candidates discovered automatically directly under that resolved root. `description`, when present, is a non-empty string and does not change Target discovery or Archive placement.

level: MUST

related: [SPEC_018](paths.md#spec_018), [SPEC_024](paths.md#spec_024)

### SPEC_041

Whether a named Scope root exists and is a directory is checked only when that Scope is actually used by `SCOPE/NAME` or `SCOPE/`. The current filesystem availability of an unused named Scope does not fail the run. Duplicate effective Scope-root validation remains Configuration-level validation and does not require an unused Scope root to exist.

level: MUST

condition: when a named Scope is actually used

### SPEC_042

A Scope name is a non-empty name usable as one segment of a CLI Target reference. It must not contain `.`, `/`, or backslash; consequently `.` and `..` are also invalid.

level: MUST

### SPEC_043

The optional `namespace` of the default or a named Scope references an effective `[namespace.<name>]`. A Namespace reference does not change the Target discovery root, Target candidates, or CLI Target-reference semantics; it is used only for Archive placement. An unknown Namespace reference is a Configuration error.

level: MUST

### SPEC_044

`scope.ignore` matches the **name** of a direct-child Target candidate for the Scope's `target_kind` case-sensitively. In directory mode it applies to directory names; in file mode it applies to regular-file names. A matching entry cannot be selected as a Target either by single-Target selection or by expansion. This is independent of file-selection `pluck.ignore` and `always.<name>.ignore`.

level: MUST

### SPEC_045

A Scope ignore pattern has one of four forms: `name` (exact), `name*` (prefix), `*name` (suffix), or `*name*` (substring). A bare `*`, path separator, backslash, an internal wildcard such as `foo*bar`, `**`, `?`, character classes, and `!` are rejected. An empty array is valid.

level: MUST

## SECTION_502

title: CLI Target reference resolution

### SPEC_046

Each positional `TARGET` argument must have exactly one of these four forms:

```text
NAME
SCOPE/NAME
/
SCOPE/
```

level: MUST

### SPEC_047

`NAME` selects one direct-child entry matching the default Scope's `target_kind`. `SCOPE/NAME` selects direct-child entry `NAME` matching named Scope `SCOPE`'s `target_kind`. `/` expands all Targets from the default Scope, and `SCOPE/` expands all Targets from named Scope `SCOPE`.

level: MUST

### SPEC_048

`/` does not mean the filesystem root. It is the expansion marker for the default Scope in the CLI Target-reference grammar. Alternative spellings such as `./`, `./NAME`, and `/NAME`, multi-level references such as `SCOPE/team/NAME`, absolute filesystem paths, and backslash separators are not accepted.

level: MUST

### SPEC_049

`NAME` and `/` use the always-present default Scope. The `SCOPE` in `SCOPE/NAME` and `SCOPE/` must exist as an effective named Scope; an unknown name does not fall back to another relative-path interpretation.

level: MUST

### SPEC_050

For single-Target resolution, the specified entry must be a **direct child** of the Scope root and must match the Scope's `target_kind`: an existing directory for `"directory"`, or an existing regular file for `"file"`. An entry recognized as a symbolic link or Windows directory junction is not selectable as a Target; an explicit `NAME` or `SCOPE/NAME` that names such a link-like entry is an error. A file in directory mode, a directory in file mode, or another special filesystem entry is also an error.

level: MUST

condition: when resolving a single Target

### SPEC_051

The Scope name is an identifier used for Target lookup and is not implicitly part of the archive path. An outer Archive directory is added only when the Scope explicitly references a Namespace.

level: MUST NOT

## SECTION_503

title: Scope expansion

### SPEC_052

`/` or `SCOPE/` enumerates direct-child entries of the corresponding Scope root and expands each eligible entry according to the Scope's `target_kind` and `ignore` into an independent Target. Directory mode includes only regular directories; file mode includes only regular files. Enumeration is not recursive.

level: MUST

### SPEC_053

Ignored entries and entries recognized as symbolic links or Windows directory junctions are not treated as Target candidates. The destination of a recognized link-like entry is not resolved and is not included in `/` or `SCOPE/` expansion. Expansion that yields zero eligible direct children for the active `target_kind` is an error.

level: MUST

### SPEC_054

Multiple positional Target references and expansions may be combined in the same run.

level: MAY

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
