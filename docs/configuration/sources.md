# Configuration sources

How Pluck, Scope, Layout, Namespace, and Always / Extra sources define where material comes from and where it appears in the Archive.

This guide explains source authoring, including Always sources that normally participate and Extra sources activated by an Always Case. The compatibility contract is defined by [Runtime Targets, Scopes, and Cases](../specification/runtime-targets.md), [Archive model and generated README](../specification/archive.md), [Namespace](../specification/namespace.md), and [Filesystem boundaries and entry types](../specification/filesystem.md). For operation, see the [CLI guide](../cli/INDEX.md); for filesystem and sharing boundaries, see the [Trust model](../TRUST.md).

## Pluck

`[pluck]` defines what to extract from **directory** Targets selected for the current run. It does not contain a source path itself; Targets are resolved from Scopes and CLI Target references. A file Target from a Scope with `target_kind = "file"` or `"both"` is atomic and does not use Pluck.

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents/", "metadata.json"]
may = ["attachments/"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

When multiple directory Targets are selected in one run, the same Pluck selection is applied independently to each directory Target. File Targets and directory Targets may be selected in the same run. A Configuration with no Pluck may still select file Targets from Scopes with `target_kind = "file"` or `"both"`, but it cannot select directory Targets.
## Scope

A Scope is a place where Targets are searched for. Configurations use an always-present default Scope and may add named Scopes.

The default Scope always exists and always uses the directory containing the Root Configuration file as its search root. The `[scope]` table configures the default Scope's optional `description`, `target_kind`, `ignore`, `layout`, and `namespace`; it has no `path` field. `target_kind` accepts `"directory"`, `"file"`, or `"both"` and defaults to `"directory"`. Omitting `[scope]`, or writing an empty `[scope]`, preserves the historical behavior: directory Targets, no description, `ignore = []`, and no Namespace. A `[scope]` written in a Base Configuration applies when that Configuration itself is used as the Root; it is not inherited by an outer Root Configuration.

```toml
[scope]
ignore = ["archive/", "tmp-*/"]
```

A named Scope has a `path`.

```toml
[scope.work]
path = "../work"
ignore = ["archive/", "tmp-*/"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*/"]
```

With `target_kind = "directory"`, a Scope exposes only eligible direct-child directories as Target candidates. With `target_kind = "file"`, it exposes only eligible direct-child regular files. With `target_kind = "both"`, it exposes both. `target_kind` therefore acts as the type filter for direct-child Target candidates. Scope `ignore` is intentionally broad: without a trailing `/` it excludes matching file and directory Target candidates, while a trailing `/` narrows the exclusion to directories only. Its role is different from file-selection `pluck.ignore`. `description` is shown once as README context for the Target group obtained from that Scope. A Scope name in the generated README identifies a selection range; it does not imply priority, importance, or hierarchy between Targets. If the name carries additional meaning, state it in `description`.

CLI Target references support single Targets, whole-Scope expansion, and Target selectors for every `target_kind`:

```text
NAME                    -> default-Scope file Target
./NAME                  -> default-Scope file Target (explicit form)
./NAME/                 -> default-Scope directory Target
SCOPE/NAME              -> named-Scope file Target
SCOPE/NAME/             -> named-Scope directory Target
/                       -> all Targets from the default Scope
SCOPE/                  -> all Targets from a named Scope
:[...]                  -> typed literal Target list in the default Scope
SCOPE:[...]             -> typed literal Target list in a named Scope
:<regex>                -> regular-expression Target selector in the default Scope
SCOPE:<regex>           -> regular-expression Target selector in a named Scope
```

Literal Target references use no trailing `/` for files and a trailing `/` for directories; dirpluck does not infer the type from the filesystem. Because `SCOPE/` is reserved for named-Scope expansion, a directory Target in the default Scope uses `./NAME/`. Expansion includes only direct children matching the Scope's `target_kind` and is not recursive: eligible directories in directory mode, eligible regular files in file mode, and both in both mode.

List items use the same type rule. `/` is also the item separator, so a non-final directory item naturally appears as `project//archive.zip`: one slash marks the directory and the next separates the following item. Three or more consecutive slashes are invalid. A regular-expression selector full-matches normalized candidate names: files are `NAME`, directories are `NAME/`. Expressions such as `/?` can therefore select either type explicitly. The expression may contain `/`, but candidate discovery remains limited to direct children of the Scope. Empty patterns, patterns longer than 512 characters, invalid regular expressions, and zero-match results are errors.

Along a base chain, only named Scopes are overlaid by name. A named Scope in an outer Configuration replaces the complete same-named Scope definition, including `description`, `target_kind`, `path`, `ignore`, `layout`, and `namespace`, while differently named Scopes coexist. The default Scope is not inherited from a Base Configuration; it always belongs to the Root Configuration. Therefore a Base Configuration's `[scope]` metadata and policy are not used by an outer Root, but remain valid when that Base Configuration itself is used as the Root. An inherited named Scope root remains anchored to the Configuration in which the Scope was declared and is not rebased to an outer Configuration.

A Scope may optionally specify `layout = "<name>"`. It takes precedence over `[about].targets_layout` and places Targets from that Scope below the declared Layout directory. If neither is present, Targets remain directly at the Archive root. The existing `namespace = "<name>"` field keeps its prefix semantics, but an effective Layout and Namespace cannot be combined on the same Scope.

Whether a named Scope path is currently available on the filesystem is checked only when that Scope is actually used by a Target reference. A named Scope that points to an unmounted or otherwise missing location does not prevent a run that uses only another Scope. The named Scope root location itself may contain a symbolic link or Windows directory junction. After that root is resolved, link-like entries discovered automatically directly under the Scope are not selected or expanded as Targets. See [Specification](../specification/INDEX.md) for exact rules on duplicate roots, Namespace references, and Target resolution.
## Namespace

A Namespace is a named Configuration concept that participates in Archive identity resolution. Define Namespaces as named empty tables:

```toml
[namespace.work]

[namespace.external]
```

The Namespace name is one Archive directory component. In the current schema, `[namespace.<name>]` has no fields. `/`, `\`, and ASCII control characters are rejected because they can break the one-component Archive boundary or the Archive entry name itself, but dirpluck does not independently enforce OS-specific reserved names or filename rules. When an Archive is intended for another OS or filesystem, choose names that are valid there. Namespace-name uniqueness is checked without regard to case. This keeps the declaration small while leaving the concept available for future Namespace-specific policy.

A Scope may reference a Namespace name explicitly:

```toml
[namespace.work]

[scope.work]
path = "/srv/work"
namespace = "work"
```

For a Scope, `namespace` prefixes each resolved Target Archive root when Layout is not in use. A Target `project/` from the example Scope is therefore placed under `work/project/`. Starting in 0.17.0, Namespace and Layout are not composed; a Configuration where the same Scope has both an effective Layout and Namespace is an error.

During the remaining 0.x series from 0.16.x onward, `[always.<name>].namespace` is still accepted only as pre-1.0 compatibility, but it is removed in 1.0.0. Write an Always source's Archive directory name directly in `[always.<name>]`. See [pre-1.0 compatibility](../specification/compatibility.md) and [Migrating to 0.16](../migration/0.16.md) for the temporary behavior and warnings.

The generated Archive README identifies each source by its final Archive root; it does not add separate provenance metadata that splits Namespace from the source root.

## Layout

Layout declares named top-level directories inside the Archive. Every name used as a placement destination must first be declared as `[layout.<name>]`.

```toml
[about]
always_layout = "dependencies"
targets_layout = "development-targets"

[layout.dependencies]
description = "Development dependencies."

[layout.development-targets]
description = "Repositories being changed."

[always.wheels]
path = "dist"
must = ["*.whl"]

[scope.external]
path = "../external"
layout = "development-targets"
```

A Layout name is one Archive directory component. `description` is optional, and an empty `[layout.<name>]` table is valid. Declaring a Layout does not create an empty directory in the ZIP. The `<name>/...` path appears only when a source actually uses that Layout. When a used Layout has a `description`, the generated README includes that description for the Layout directory.

`[about].always_layout` and `[about].targets_layout` provide default Layouts for Always / Extra sources and Targets respectively. An individual `[always.<name>].layout`, `[extra.<name>].layout`, `[scope].layout`, or `[scope.<name>].layout` overrides the corresponding default. A source with neither an individual Layout nor a default remains directly at the Archive root.

Layout references are resolved against the effective Layout set after Base composition; an unknown Layout is an error. Layout names must be unique under a case-insensitive comparison. Layout does not identify a source-side filesystem directory. It controls only the Archive destination.

## Always

`[always.<name>]` fixes a source directory in the Configuration and makes it participate on every run. Without Layout, `<name>` is the Always source's Archive directory identity. Its `path` specifies only the filesystem source directory and may be relative or absolute.

```toml
[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[always.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
must = ["*.md"]
```

The example above places selected files under `guidelines/` and `company_reference/`. The directory names `review-guidelines` and `reference` do not become Archive roots. A relative `path` is resolved from the directory containing the Configuration file in which the definition is written and may use `..` to reference an outer directory. An absolute `path` directly references a directory on the host filesystem. `path` must resolve to an existing directory; the filesystem root itself may be used explicitly. An explicitly configured root location may contain a symbolic link or Windows directory junction, and the referenced directory becomes the Selection boundary.

An Always source may specify `layout = "<name>"`; otherwise `[about].always_layout` is used when present. With an effective Layout, selected files are placed under `LAYOUT/ALWAYS_NAME/...`. Without either an individual or default Layout, placement remains `ALWAYS_NAME/...`.

An Always source may still specify `namespace = "<name>"` during the 0.x migration period from 0.16.0 onward. The Namespace name replaces the Always `<name>` as the effective Archive directory name and always reports `AlwaysMigrationWarning`. This is pre-1.0 compatibility behavior and is removed in 1.0.0. An effective Layout and compatibility `namespace` cannot be used together. New Configurations should use Layout for top-level placement and express the source identity directly with `[always.<name>]`.

The resolved source directory itself is the selection boundary. Allowing an alias for that explicit root does not enable link traversal inside the source. Entries recognized as symbolic links or Windows directory junctions during automatic Selection traversal are not selected, and their targets are not followed.

An Always source's Selection is evaluated independently of the Target Pluck. Even when the same physical file also exists under a Target, the Target's `ignore` rules and Selection result do not change the Always source's Selection. If both sources select the same physical file for different Archive paths, both entries are included. When selected files physically overlap, the generated Archive README records the Target-side Archive root and overlap count in the Always source section.

After Layout is applied, final Archive roots must be unique under a case-insensitive comparison regardless of source role. A Target and an Always or activated Extra source that resolve to the same final root are therefore an error rather than an intentional composition. A Configuration with only fixed sources and no Pluck is also valid.

## Extra

`[extra.<name>]` defines a fixed source that is available to an Always Case but does not participate merely because it is defined. Its canonical table schema is the same as `[always.<name>]`: required `path`, Selection fields `description` / `must` / `may` / `ignore` / `allow_empty`, and optional `layout`.

```toml
[always.guidelines]
path = "review-guidelines"
must = ["*.md"]

[extra.dev-tools]
path = "tooling"
description = "Tools needed only for development runs."
must = ["*.whl"]

[case.always.development]
add = ["dev-tools"]
```

An Extra remains inactive merely by being declared. It becomes active only for a run whose `[case.always.<name>]` references it through complete `include` or delta `add`, after which it behaves with the same fixed / Always role as an ordinary Always source. If no Always Case is selected, or the selected Case does not `include` / `add` that Extra, it remains inactive.

`include` completely enumerates the participating sources from the shared Always / Extra identifier namespace. `add` / `exclude` are deltas over the default set of all Always sources: `add` activates only Extra identifiers, while `exclude` removes only Always identifiers. `include` cannot be combined with `add` / `exclude`, but `add` and `exclude` may be used together. Wrong-kind references are Configuration errors. Because Always and Extra share this Case-reference namespace, ambiguous effective identifiers such as `[always.foo]` and `[extra.foo]`, including names that differ only by case, are invalid.

Layout follows the Always rules. `[extra.<name>].layout` takes precedence; otherwise `[about].always_layout` applies; if neither exists, the Extra is placed directly under the Archive root when activated. Once activated, README role detection, collision checks, Layout descriptions, and `description_no_always` handling treat the Extra as an Always source.

