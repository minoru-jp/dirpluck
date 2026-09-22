# dirpluck Configuration Quick Reference

This is the compact Configuration reference included in the wheel. Configuration documents use the `.dirpluck` filename extension and TOML syntax; `.toml` filenames are not accepted as Configurations. A `.dirpluck-inv` file is a separate Invocation Template document type and does not participate in the Configuration schema or base chain.

```toml
[about]
description = "Materials prepared for reviewing the current project."

[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive", "tmp-*"]

[scope.work]
path = "/srv/work"
ignore = ["archive"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[about].description` is an optional description of the Archive as a whole. If several Configurations in the base chain define it, the first value found from the outermost Configuration inward is used and appears before the index in the generated Archive README. To base the Configuration on another Configuration, add `base = "../common/common.dirpluck"` to the same `[about]` table. `description` and `base` are independently optional.

Review selections before creating an Archive that will be shared. `dirpluck` does not infer which files are sensitive; explicitly ignore material that should not be collected.

```toml
[pluck]
ignore = [".git/", ".env*", "*.pem", "*.key"]
```

This is only an example. See the bundled `TRUST.md` for the trust model and filesystem responsibilities.

The concrete Pluck Target is selected by a positional CLI `TARGET`. The default Scope always uses the Root Configuration file's directory as its root. `[scope]` only configures the default Scope's optional `ignore` and `namespace`, and the default Scope remains available when `[scope]` is omitted. A Base Configuration's `[scope]` is root-local and is not inherited into an outer Root Configuration. `project` selects `project` in the default Scope; `work/project` selects `project` directly under named Scope `work`; `/` expands all eligible direct child directories of the default Scope; and `work/` does the same for named Scope `work`. Multi-level Target references and undefined Scopes are errors. `scope.ignore` applies to Target candidate directory names and is separate from selection `ignore`. A named Scope path is checked for existence only when that Scope is actually used. Entries recognized as symbolic links or Windows directory junctions directly under a Scope are not Target candidates.

When different source roots would otherwise resolve to the same Archive root, define an explicit Namespace. Namespaces are named empty tables whose names become Archive-only outer directory names:

```toml
[namespace.work]

[namespace.external]

[scope.work]
path = "/srv/work"
namespace = "work"

[always.docs]
path = "../docs"
namespace = "external"
```

A Namespace is always applied when referenced. For example, a Target with source root `project/` in the `work` Namespace is archived under `work/project/`, while an Always source with source root `docs/` in the `external` Namespace is archived under `external/docs/`. Different resolved sources must have distinct final Archive roots; dirpluck does not silently merge them or invent suffixes. When any Namespace is used, the Archive README uses each final Archive root as a heading, identifies the Namespace and source root separately for namespaced sources, and explains that the Namespace directory exists only in the Archive.

An Always source fixes its `path` in the Configuration. Filesystem locations use `/` as the separator; even on Windows, backslash is not a path separator in Configuration notation. Relative paths are resolved from the directory containing the Configuration file in which the field is written. Absolute paths may also be specified. Explicit named-Scope and Always root locations may contain symbolic links or Windows directory junctions, but automatic Target discovery and Selection traversal below the resolved root do not follow link-like entries. `about.base`, which references another Configuration document, also follows the host OS's normal filesystem semantics, and a relative reference is anchored to the directory of the selected Configuration path.

Always sources and Targets are selected independently. If the same physical file is selected by both and maps to different Archive paths, both entries are included; a Target-side `ignore` does not suppress the Always source. The Archive `README.md` records the Target-side Archive root and overlap count in an Always source section when their actually selected files physically overlap.

Selections can use:

- `description`: an optional non-empty string, including multi-line text, shown in the Archive README section for that source or selection.
- `must`: candidates that are required to exist.
- `may`: candidates whose absence is allowed.
- `ignore`: file or directory names that should not be collected from selected candidate areas. A one-element nested array such as `["./path/to/file"]` or `["./path/to/directory/"]` instead names one concrete path from the Selection root.
- `allow_empty = true`: permit zero files for a selection that has no `must` entries.
- `["name"]`: a Shared pattern reference in the same field category. In `ignore` only, a nested-array string beginning with `./` is a Selection-relative path reference instead.

Define reusable patterns under `[shared.must]`, `[shared.may]`, or `[shared.ignore]`. Define named variations as complete selections under `[pluck.case.<name>]` or `[always.<name>.case.<name>]`. For a Selection-relative path reference, `./` means the Target root in Pluck and the Always-source root in an Always Selection; a trailing `/` explicitly marks a directory. Name, Shared, and path ignore conditions may overlap and are combined as a union.

Selection `ignore` takes precedence over diagnostics based on filesystem-entry type, so ignored entries are not included in the skipped-link count and do not cause special-entry-only errors. Non-ignored entries recognized as symbolic links or Windows directory junctions while discovering Targets or traversing a Selection are not followed and are not included in the Archive. Special entries that are neither regular files nor regular directories, such as FIFOs, sockets, and devices, are also not archived; a `must` pattern matching only such entries fails with an explanatory error.

Use another Configuration as a base with:

```toml
[about]
base = "../base/base.dirpluck"
```

Output is optional. A Base Configuration and a Root Configuration used with `--preview` or Runtime Output may omit it. A normal build without Runtime Output requires the Root Configuration to directly declare either fixed mode or timestamp mode. Output from a Base Configuration is not inherited. Fixed mode specifies the complete filename, and `overwrite` defaults to `false`. Generated Archive files use normal new-file permission semantics, so POSIX systems apply the process `umask`; overwriting does not inherit the existing file mode. With automatic Runtime Output from CLI `--here` / `--output` or Python `output=`, a Root `[output.timestamp]` contributes its `prefix` / `suffix` naming rule, but not its configured `path`.

```toml
[output]
path = "artifacts/review.zip"
overwrite = true
```

Timestamp mode specifies a directory whose notation must end in `/`.

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

For pattern grammar, base composition, Scope shadowing, Case semantics, filesystem boundaries, and Output write-boundary collisions, see `docs/CONFIGURATION.md` and `docs/SPECIFICATION.md` in the source distribution for the same release. The trust model is in the bundled `TRUST.md`, and the bundled `CLI.md` is the compact CLI reference.
