# Configuration sources

How Pluck, Scope, Namespace, and Always sources define where material comes from and where it appears in the Archive.

This guide explains source authoring. The compatibility contract is defined by [Runtime Targets, Scopes, and Cases](../specification/runtime-targets.md), [Namespace](../specification/namespace.md), and [Filesystem boundaries and entry types](../specification/filesystem.md). For operation, see the [CLI guide](../cli/INDEX.md); for filesystem and sharing boundaries, see the [Trust model](../TRUST.md).

## Pluck

`[pluck]` defines what to extract from **directory** Targets selected for the current run. It does not contain a source path itself; Targets are resolved from Scopes and CLI Target references. A Target from a Scope with `target_kind = "file"` is atomic and does not use Pluck.

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents", "metadata.json"]
may = ["attachments"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

When multiple directory Targets are selected in one run, the same Pluck selection is applied independently to each directory Target. File Targets and directory Targets may be selected in the same run. A Configuration with no Pluck may still use positional Target references for file-kind Scopes, but it cannot select directory Targets.
## Scope

A Scope is a place where Targets are searched for. Configurations use an always-present default Scope and may add named Scopes.

The default Scope always exists and always uses the directory containing the Root Configuration file as its search root. The `[scope]` table configures the default Scope's optional `description`, `target_kind`, `ignore`, and `namespace`; it has no `path` field. `target_kind` accepts `"directory"` or `"file"` and defaults to `"directory"`. Omitting `[scope]`, or writing an empty `[scope]`, preserves the historical behavior: directory Targets, no description, `ignore = []`, and no Namespace. A `[scope]` written in a Base Configuration applies when that Configuration itself is used as the Root; it is not inherited by an outer Root Configuration.

```toml
[scope]
ignore = ["archive", "tmp-*"]
```

A named Scope has a `path`.

```toml
[scope.work]
path = "../work"
ignore = ["archive", "tmp-*"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*"]
```

With `target_kind = "directory"`, a Scope exposes only eligible direct-child directories as Target candidates. With `target_kind = "file"`, it exposes only eligible direct-child regular files. A Scope never mixes directory and file Targets. `ignore` matches the direct-child candidate name for the active Target kind. Its role is different from file-selection `pluck.ignore`. `description` supplies README context for Targets obtained from the Scope.

CLI Target references have four forms combining unnamed or named Scope selection with one Target or all Targets:

```text
NAME        -> one Target from the default Scope
SCOPE/NAME  -> one Target from a named Scope
/           -> all Targets from the default Scope
SCOPE/      -> all Targets from a named Scope
```

Expansion includes only direct children matching the Scope's `target_kind` and is not recursive: eligible directories in directory mode, eligible regular files in file mode.

Along a base chain, only named Scopes are overlaid by name. A named Scope in an outer Configuration replaces the complete same-named Scope definition, including `description`, `target_kind`, `path`, `ignore`, and `namespace`, while differently named Scopes coexist. The default Scope is not inherited from a Base Configuration; it always belongs to the Root Configuration. Therefore a Base Configuration's `[scope]` metadata and policy are not used by an outer Root, but remain valid when that Base Configuration itself is used as the Root. An inherited named Scope root remains anchored to the Configuration in which the Scope was declared and is not rebased to an outer Configuration.

A Scope may optionally specify `namespace = "<name>"`. This does not change where Targets are searched for. Instead, it prefixes the Archive root of every Target obtained from that Scope with a separately defined Namespace. A Namespace is applied whenever it is configured, not only when a collision happens.

Whether a named Scope path is currently available on the filesystem is checked only when that Scope is actually used by a Target reference. A named Scope that points to an unmounted or otherwise missing location does not prevent a run that uses only another Scope. The named Scope root location itself may contain a symbolic link or Windows directory junction. After that root is resolved, link-like entries discovered automatically directly under the Scope are not selected or expanded as Targets. See [Specification](../specification/INDEX.md) for exact rules on duplicate roots, Namespace references, and Target resolution.
## Namespace

A Namespace is an Archive-only prefix used to place source roots distinctly when they would otherwise resolve to the same Archive path. Define Namespaces as named empty tables:

```toml
[namespace.work]

[namespace.external]
```

The Namespace name itself becomes one directory name in the Archive. In the current schema, `[namespace.<name>]` has no fields. This keeps the declaration small while leaving the table available for future Namespace-specific policy.

Scopes and Always sources reference Namespace names explicitly:

```toml
[namespace.work]
[namespace.external]

[scope.work]
path = "/srv/work"
namespace = "work"

[always.docs]
path = "../docs"
namespace = "external"
description = "External documentation."
must = ["*.md"]
```

If `work/project` has source root `project/`, it is placed at `work/project/`. If an Always source would normally have source root `docs/`, the example above places it at `external/docs/`. A source without a Namespace keeps its source root as its Archive root.

If different resolved sources still produce the same final Archive root, `dirpluck` fails rather than silently merging them. A Namespace is an explicit way to avoid that collision, but it does not guarantee uniqueness by itself; two sources may still collide if they use the same Namespace and the same source root.

When at least one Namespace is used, the generated Archive README explains that Namespace directories are Archive-only and not part of the original source path. Each source uses its final Archive root as a heading, and namespaced sources identify the Namespace and Source root separately as metadata.
## Always

`[always.<name>]` fixes a source directory in the Configuration and makes it participate on every run. Its `path` may be relative or absolute.

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

A relative `path` is resolved from the directory containing the Configuration file in which the definition is written. It may use `..` to reference an outer directory. An absolute `path` directly references a location on the host filesystem. An explicitly configured Always root location may contain a symbolic link or Windows directory junction, and the referenced directory is used as the source root. The Archive source-root name is taken from the location written in the Configuration rather than being replaced by the physical target directory's name.

The resolved source directory itself is the selection boundary. Allowing an alias for that explicit root does not enable link traversal inside the source. Entries recognized as symbolic links or Windows directory junctions during automatic Selection traversal are not selected, and their targets are not followed.

An Always source's Selection is evaluated independently of the Target Pluck. Even when the same physical file also exists under a Target, the Target's `ignore` rules and Selection result do not change the Always source's Selection. If both sources select the same physical file for different Archive paths, both entries are included. When selected files from an Always source physically overlap selected files from a Target, the generated Archive README records the Target-side Archive root and overlap count in the Always source section.

Define multiple Always sources with different names. A Configuration with only Always sources and no Pluck is also valid.
