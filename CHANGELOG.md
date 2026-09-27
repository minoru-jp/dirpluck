# dirpluck CHANGELOG

Release history for dirpluck.

## 0.11.0

Add an opt-in Scope mode for treating direct-child regular files as atomic Targets. This supports workflows such as collecting several returned ZIP archives together with existing Always sources without unpacking those archives first, while preserving the directory-only behavior of existing Scopes by default.

### Added

- Add Scope `target_kind = "directory" | "file"`. The default remains `"directory"`, so existing Configurations keep their previous Target discovery and `SCOPE/` expansion behavior. A file-kind Scope exposes only eligible direct-child regular files as Targets; directories, link-like entries, and other special filesystem entries are not file Targets.
- Add optional Scope `description` metadata. For directory Targets, the generated Archive README shows the Scope description before the Pluck description. For file Targets, each atomic file receives its own README section and shows the Scope description without a Pluck description.

### Changed

- Clarify Pluck as content Selection for directory Targets. File Targets bypass Pluck and are included as atomic files, so a Configuration without Pluck may still accept positional Target references from file-kind Scopes. Directory Targets continue to require Pluck.
- Apply the existing Scope Namespace mechanism to file Targets. A file Target uses its file name as the source root, or `NAMESPACE/FILENAME` when the Scope references a Namespace.
- Extend Scope `ignore` and `SCOPE/` expansion according to the active Target kind. Directory mode retains the existing direct-child-directory behavior; file mode applies the same candidate-name policy to direct-child regular files.

## 0.10.2

Clarify the responsibilities of the release artifacts and standardize the build backend on Hatchling. The wheel provides the implementation and the complete published documentation set, while the sdist provides the complete source needed to rebuild and validate the release.

### Changed

- Migrate the build backend from setuptools to Hatchling. `dirpluck.__version__` remains the version source of truth and Hatchling reads it for project metadata. Remove the setuptools-specific `MANIFEST.in` and generated `*.egg-info` from the distribution design.
- Remove the compact documentation channel that existed only for wheels. Delete `src/dirpluck/docs/`, `canonical_sources/package_cli/`, `canonical_sources/package_configuration/`, `canonical_sources/package_trust/`, and the independent `canonical_documents/package/` publication channel so the published documentation no longer has to be maintained in two forms.
- Bundle the repository's published `README.md`, `GLOSSARY.md`, `CHANGELOG.md`, `STATUS.md`, and the complete `docs/` tree under `dirpluck/_docs/` in the wheel, in addition to the implementation. CLI, Configuration, Python API, Trust, Specification, and Glossary documentation can therefore be read from the wheel for the same release.
- Change the sdist from an explicitly enumerated set of directories to the complete release source selected with VCS ignore rules. It includes `tests/`, `tools/`, `devdocs/`, published documentation, and the implementation, while repository-operation-only `.github/` content is excluded.

## 0.10.1

Synchronize release metadata and published documentation for the 0.10.1 release while preserving the runtime behavior and public API / Configuration semantics of 0.10.0.

### Changed

- Update the package version and documentation current-version snapshot to 0.10.1. This release makes no functional changes to runtime behavior, the official Python API, CLI, Configuration language, or Archive semantics.
- Align release-preparation documentation with the current shikumi / shikumi-devdoc baseline, including the STATUS documentation-tooling wording for the release baseline of Shikumi 0.2.0 and shikumi-devdoc 0.3.0.

## 0.10.0

Allow the runtime to choose the Output destination and overwrite policy so a Configuration's extraction definition can be reused while changing where an invocation writes its Archive.

### Added

- Add CLI `--here[=FILENAME]`, `-o PATH` / `--output PATH`, and `-f` / `--force`. `--here` uses the runtime cwd, while `--output` supplies an explicit path resolved from the runtime cwd. A trailing `/` on `--output` selects a directory and generates a timestamp filename. `--here=FILENAME` accepts only a filename directly under the cwd; use `--output` when a path is needed.
- Add `output` and `force` to the official Python `run()` API. `output` follows the same path semantics as CLI `--output`: a trailing `/` generates an automatic timestamp filename in that directory, while a path without trailing `/` is an exact output file path. Relative `output` values are resolved from the API `cwd`.

### Changed

- A build with Runtime Output no longer requires an Output declaration on the Root Configuration. Exact Runtime Output keeps the supplied filename unchanged. Automatic Runtime Output reuses the Root Configuration's `[output.timestamp]` `prefix` / `suffix` naming rule when one is declared; otherwise the default name is `dirpluck-YYYYMMDD-HHMMSS.zip`. The configured output directory or fixed path is not carried into the runtime destination.
- Extend `--sequence N` to automatic timestamp filenames produced by `--here` and trailing-`/` Runtime Output in addition to Configuration timestamp Output. Using a sequence with an exact Runtime Output is an error. Generated-name collisions do not trigger automatic numbering, renaming, or a new timestamp sample.
- Runtime Output defaults to no-overwrite. `--force` / `force=True` makes the effective Output overwriteable and applies to both Runtime Output and Configuration fixed / timestamp Output. Runtime Output paths use `/` separators on every OS, matching Configuration path notation, and reject backslashes.
- Reject `--preview` / `preview=True` when combined with Runtime Output (`--here`, `--output`, or `output=`), overwrite forcing (`--force` / `force=True`), or `--sequence`. Preview does not resolve or write an Output, so these runtime Output modifiers are no longer silently ignored.
- Reorganize the public documentation by moving the end-to-end README example to `docs/GETTING_STARTED.md` and replacing the single `docs/CONFIGURATION.md` with a collection rooted at `docs/configuration/INDEX.md`. The collection separates overview, sources, selection, base composition, Output, and a complete example, while the compact wheel-bundled `dirpluck/docs/CONFIGURATION.md` remains a single quick reference.
- Split the CLI guide from the single `docs/CLI.md` into a collection rooted at `docs/cli/INDEX.md`, separating basic operation, Invocation Templates, Target / Case operation, and preview / runtime Output. Keep the wheel-bundled `dirpluck/docs/CLI.md` as a compact quick reference. Public collection `INDEX.md` files now stay limited to translations of the canonical indexes generated by shikumi-devdoc; explanatory navigation lives in canonical `overview.md` documents instead.
- Remove legacy numbered-section references left over from the former monolithic Specification. Cross-references now name the relevant normative area, such as Filesystem path notation, Runtime Target, Archive planning, or Output. Genuine rule dependencies are retained in `related` metadata where they do not create circular imports, and a regression test rejects reintroduction of numbered section references.
- Synchronize the development-document canonical sources with the current shikumi-devdoc 0.3.0 authoring contract. Nested titles now use `title @= ...` instead of `@title(...)`; every canonical source declares `heading="title"` or `heading="identity"`; document fragments intended for direct verification by ordinary tests use presentation-neutral `test_target_field` values with Markdown fences kept in docstrings; Vocabulary terms are public in the Glossary by default; and the Specification uses identity headings so semantic references remain stable across title and Vocabulary changes.

## 0.9.1

Allow Targets and Always sources to include the same physical material in independent roles, and correct Archive planning and generated README handling for that overlap.

This version was an unpublished development milestone and was not published to PyPI.

### Fixed

- Stop rejecting the same physical file when a Target and an Always source select it for different Archive paths. Target Pluck and Always-source Selection are evaluated independently, so Target-side `ignore` or non-selection does not suppress the Always source. Different physical files that collide at one archive path remain an error, while the same physical file mapped to the same archive path is still written once. When actually selected files overlap physically between an Always source and a Target, the generated Archive README records the Target-side final Archive root and overlapping file count in the Always source section.

## 0.9.0

Prepare the Configuration language vocabulary and filesystem model for 1.0, moving the public Configuration surface to the new Pluck / Scope / Always / Base / Output model. Advance the Development Status to Beta.

### Changed

- Rename the no-write archive inspection option from `--dry-run` to `--preview` without a compatibility alias. Expand `--help` for positional `TARGET` arguments so the four accepted forms, `NAME`, `SCOPE/NAME`, `/`, and `SCOPE/`, are visible directly in the CLI help.
- Reject a run when different resolved sources produce the same final Archive root, even when their selected files would not otherwise collide. dirpluck no longer silently merges such sources and does not invent suffixes or implicitly qualify them with Scope or Always names. Use an explicit Namespace to keep source roots distinct. When any Namespace is used, the generated Archive README uses the final Archive root as the section heading, records Namespace and Source root separately as metadata, and explains that the Namespace is an Archive-only outer directory.
- Rework the Configuration vocabulary. Replace `[target]` with `[pluck]`, `[companion.<name>]` with `[always.<name>]`, and Target locations with Configuration-level `[scope]` / `[scope.<name>]`. Replace Selection `include` / `include_if_exists` / `exclude` with `must` / `may` / `ignore`, and replace `if_empty` with boolean `allow_empty`. No compatibility layer is provided for the old schema.
- Simplify Configuration layering to a linear base chain declared with `[about].base`. Remove the former `[import.<name>]`, `root`, and `configuration` structure and import-overlay Companion behavior. Relative filesystem paths for `about.base`, Scopes, Always sources, and Outputs now resolve from the directory containing the Configuration file in which each field is written. Definitions inherited from a Base Configuration are not rebased to the outer Configuration.
- Separate Target discovery into independent Scope definitions. The default Scope always uses the Root Configuration directory as its search root, and `[scope]` configures its optional `ignore`. Named Scopes add search roots through `path`; along a base chain, an outer same-named named Scope shadows the entire inner definition. CLI Target references now have exactly four forms: `NAME`, `SCOPE/NAME`, `/`, and `SCOPE/`. `/` expands direct children of the default Scope. Scope `ignore` applies to both single selection and expansion.
- Split Shared patterns into `[shared.must]`, `[shared.may]`, and `[shared.ignore]` namespaces and remove dedicated `*_pattern_refs` fields. A normal string in a Selection array is a direct pattern; a one-element nested array (`["name"]`) is a Shared reference in the same field category and is expanded against the effective Shared namespace.
- Split Output into mutually exclusive fixed `[output]` and timestamp `[output.timestamp]` modes. Fixed Output has a concrete file `path` and optional `overwrite`, which defaults to `false`. Timestamp Output has a directory `path` ending in `/` and optional `prefix` / `suffix`. Remove the former `directory` field and boolean `timestamp = true`.
- Validate static writable destinations across the base chain. A fixed Output owns its complete file path; a timestamp Output owns its output directory tree. The same fixed file, overlapping timestamp directories, and a fixed file inside a timestamp boundary are conflicts. Different fixed filenames in the same directory are allowed. Only the Root Configuration's own Output is still written during a run.
- Make Output optional at the Configuration-schema level. A Configuration without Output can be used as a shared Base, and a Root Configuration without Output can still be used for archive planning or `--preview`. A build that actually writes an Archive must directly declare the Root Configuration's own fixed or timestamp Output; Base Output is not inherited. Only layers that actually declare Output participate in base-chain write-boundary validation.
- Split the internal Selection representation into parsed `SelectionDefinition`, which may still contain Shared references, and effective `Selection`, whose Shared references have been materialized. Remove the duplicated `must_items` / `may_items` / `ignore_items` state and the type suppressions it required.
- Rename semantic/package-interface tests to describe the current Configuration model rather than the release stage in which they were introduced.
- Change the project metadata Development Status classifier from `3 - Alpha` to `4 - Beta`.
- Stop following symbolic links during filesystem traversal. Symbolic links directly under a Scope are not Target candidates, and file or directory symbolic links encountered by Selection are not selectable and are not included in the Archive. An explicit Target reference naming a symbolic link is an error; a `must` / `may` pattern that matches only symbolic links is treated as required missing / optional missing respectively.
- Allow `--preview` and internal archive planning to run when the Root Configuration has no Output declaration. Only a build that writes an Archive requires Root Output. Because preview does not generate an output filename, `--preview` cannot be combined with `--sequence`.
- Remove `--configs`, which inferred and listed Configuration candidates. The only Configuration selected implicitly by the CLI is now `default.dirpluck` in the runtime cwd. A single differently named Configuration is not treated as an implicit default, and dirpluck no longer heuristically classifies files by content. Select a differently named Configuration or one in another directory explicitly with `--config PATH`. No compatibility alias is provided.
- Treat an Invocation's `case` as a default rather than a fixed value, and allow CLI `--case` to be combined with `-i` / `--invocation-template`. When supplied, the CLI Case takes precedence over the selected default or named Invocation's `case`; otherwise the selected Invocation value is used.
- Stop using `Path.suffix` to classify CLI Configuration and Invocation Template paths. If the required suffix is not already at the end, append `.dirpluck` or `.dirpluck-inv` directly. As a result, `--config release-1.2` selects `release-1.2.dirpluck` in the cwd, `--config configs/release-1.2` selects `configs/release-1.2.dirpluck` under the cwd, and `-i set-2.1` selects `set-2.1.dirpluck-inv` in the cwd instead of rejecting a dot in the stem as a conflicting extension.
- Simplify CLI document selection. When `--config` is omitted, automatically select only `default.dirpluck` in the runtime cwd. Do not treat `./.dirpluck/` as a reserved discovery or control directory, and give a directory named `.dirpluck` no special Scope semantics. `--config PATH` and `-i PATH` accept the same `/`-separator, no-glob, no-backslash path notation as Configuration filesystem locations; relative paths are resolved from the runtime cwd and absolute paths from the host filesystem to select exactly one document. Do not complete a directory with a default document or search another location for a same-named file. The default Scope root is always the Root Configuration file's directory.
- Define Configuration / Invocation Template control-document paths using the host OS's normal filesystem semantics. The runtime-cwd `default.dirpluck`, `--config PATH`, `-i PATH`, `[about].base`, and an Invocation's `config` use those normal semantics even when the path contains a symbolic-link or Windows-junction alias. dirpluck retains the selected or referenced lexical absolute path as the document location for relative references, while internal checks that require file identity, such as base-chain cycle detection, use the physical path. The source-tree symbolic-link / junction non-traversal policy remains an independent extraction boundary.
- Apply the same suffix completion used by CLI `--config PATH` to an Invocation's `config` field, so `.dirpluck` may be omitted there as well. For example, `config = "configs/release-1.2"` refers to `configs/release-1.2.dirpluck` relative to the Invocation Template document. `[about].base` remains an explicit Configuration-schema reference and still requires the `.dirpluck` extension.
- Clarify link handling at source roots versus during traversal. A root location explicitly written in `[scope.<name>].path` or `[always.<name>].path` follows the host OS's normal filesystem semantics and may itself contain a symbolic link or Windows directory junction. After that root is resolved, automatic Target discovery and Selection traversal continue to exclude and not follow recognized link-like entries below it. For an Always source reached through an alias, the Archive source root preserves the lexical name or relative path written in the Configuration rather than adopting the physical target directory's name.
- Make `description` optional metadata for Pluck, Always-source, and Case Selections. Selection validity now depends on `must` / `may` candidates and `allow_empty`, not on descriptive text. The generated Archive README now uses one section per final Archive root instead of a table, records the selected file count as metadata, and places an optional `description` in the section body so multi-line descriptions remain readable.
- Reorganize the documentation-development workspace from `_internal/document_source` / `_internal/document_build/ja` into the public repository structure under `devdocs/`. Canonical Python sources now live in `devdocs/canonical_documents/`, repository configuration passed to shikumi-devdoc in `devdocs/config/`, and Japanese intermediate Markdown in `devdocs/intermediate_documents/`. `canonical_documents` is the import package itself, with generated Vocabulary `terms.py` at its package root. Intermediate documents mirror repository publication paths while wheel-facing artifacts remain separated under the `package/` namespace. `devdocs/README.md` is itself generated from a canonical source. `devdocs/` is included in the sdist and excluded from wheels.

### Fixed

- Allow ZIP creation to complete when a selected file has an mtime outside the ZIP timestamp range by clamping it to the supported range instead of raising a traceback. Also convert an `OSError` raised while adding a selected file to the Archive into `SelectionError`, so the CLI reports a normal error and removes the temporary Archive instead of exposing a raw traceback.
- Simplify Scope handling by making the default Scope always present at the Root Configuration directory. This removes the need to distinguish an explicitly written `[scope]` from the parent table implicitly created by `[scope.<name>]`. Also defer named-Scope root existence and directory checks until that Scope is actually used for Target resolution or expansion, so an unavailable unused Scope does not block runs that use another Scope.
- Apply directory `ignore` during traversal instead of filtering only after recursive collection. An ignored directory is pruned before its contents are enumerated, avoiding unnecessary work for large ignored subtrees and preventing traversal-time errors from entries inside them.
- Add the `[pluck]` table header to the sensitive-file `ignore` example in the README and bundled Configuration quick reference so the snippet is valid when copied into a Configuration.
- Remove the unused `cwd` parameters from the internal `resolve_sources`, `plan_archive`, and `build_archive` functions. Those parameters only validated the supplied directory and never affected resolution, which incorrectly suggested that runtime cwd could control Configuration-relative paths. Runtime cwd remains relevant only to implicit `default.dirpluck` selection and as the base for relative CLI document paths; source and Output resolution continue to use Configuration-file anchors.
- Reserve root-level `README.md` for the generated Archive index. Planning now rejects any resolved source whose final Archive root begins with `README.md` case-insensitively, whether the conflicting first component comes from a Namespace or from an unnamespaced source root.
- Clarify that default-Scope `[scope].ignore` / `namespace` settings are root-local: a Base Configuration may contain `[scope]`, but those settings apply only when that Configuration itself is used as the Root and are not inherited into an outer Root Configuration.
- Extend the non-traversal policy from symbolic links to Windows directory junctions, using a shared link-like-entry check that works on Python 3.11 through Windows reparse tags. `--preview` and normal builds now report how many recognized link-like entries were skipped without listing their paths, and a `must` pattern that matches only link-like entries reports that reason instead of a generic `no matches` error. The trust documentation also states that unknown platform-specific link mechanisms cannot be guaranteed absent and that extraction behavior belongs to the third-party extractor and platform.
- Fix internal type inconsistencies found by type checking. Effective Configuration validation now uses distinct loop variables for Scope bindings and Always bindings instead of reusing one name across different binding types, the Configuration-table key validation helper accepts `Mapping[str, object]` to match TOML table keys, and Windows-only `stat_result.st_reparse_tag` metadata is obtained with `getattr` so type checking on non-Windows platforms does not treat it as an unconditional attribute access. Runtime behavior and the public API are unchanged.
- Move Archive-build Output preflight back ahead of archive planning. Validate Root Output presence, `--sequence`, the resolved output path, and the overwrite policy for an existing output before traversing source trees, so a build that is already known to fail returns promptly. Checks that require the completed plan, such as rejecting an output that is also a selected input, and side effects such as directory creation and ZIP writing remain after planning.
- Clarify Selection `ignore` precedence. An ignored entry no longer contributes to the link-like skipped count or to a link-only `must` diagnostic; a `must` pattern that matches only ignored entries fails as an ordinary unsatisfied pattern. This gives an explicit `ignore` directive priority over runtime link diagnostics, consistent with traversal pruning for ignored directories.
- Make the Windows directory-junction safety boundary fail closed. If a supported Windows runtime cannot provide `IO_REPARSE_TAG_MOUNT_POINT` or `st_reparse_tag`, dirpluck reports an error instead of silently disabling junction detection. The Windows junction integration test now treats failure to create the junction as a test failure rather than a skip.
- Keep the CLI build-and-plan helper internal instead of introducing a public-looking module API, and add Ruff's preview E3 blank-line rules (`E301` through `E306`) explicitly to the repository lint configuration while normalizing blank lines across `src`, `tests`, and `tools`. Runtime behavior and the package-root public interface are unchanged.
- Clarify the filesystem-object boundary for Selection. Only regular files are archived and regular directories are traversed; FIFOs, sockets, devices, and other non-regular entries are excluded. Such entries are silently ignored during recursive traversal and optional `may` matching, while a `must` pattern that matches only non-ignored special entries reports an explanatory unsupported-entry error instead of a generic `no matches`. `ignore` continues to take precedence over type-specific diagnostics.
- Change Configuration document identity from `.toml` to the `.dirpluck` filename extension while keeping TOML syntax for the contents. When `--config` is omitted, the only implicitly used document is `default.dirpluck` in the runtime cwd; `about.base` requires a concrete `.dirpluck` path. No compatibility alias or fallback is provided for `.toml` Configurations, the old `dirpluck.toml` name, or the old `./dirpluck/` discovery location.
- Improve the diagnostic for an empty `.dirpluck-inv` document from `[invocation]: expected a table` to `[invocation] table is required`, distinguishing a missing required table from a present `invocation = ...` value of the wrong type. An empty `[invocation]` table with no fields remains valid.
- Resolve the ambiguity where `[invocation.config]`, `[invocation.targets]`, or `[invocation.case]` was reported as a field-value type error. `config`, `targets`, and `case` are now explicitly reserved as root Invocation field names and cannot be used as named Invocation entry names, with a dedicated diagnostic.
- Improve the backslash rejection diagnostic for filesystem-location notation to state explicitly that `/` is the required path separator even on Windows. The accepted path grammar is unchanged, and the message is shared by CLI `--config PATH` / `-i PATH` and filesystem-location fields in Configuration / Invocation Template documents.
- Stop leaking the atomic-write temporary file's `0600` mode into the final ZIP. Temporary output is now created with ordinary new-regular-file creation semantics, so POSIX systems apply the process `umask` and the resulting mode is retained by the final Archive. With `overwrite = true`, the existing destination's mode is not inherited; each run uses fresh new-file creation semantics.
- Clarify the concurrent-writer boundary for Output. Fixed Output with `overwrite = false` and timestamp Output check for an existing destination before the build and again before final placement, but the check and final placement are not an atomic no-clobber operation against another process. Concurrent writes to the same output path are outside dirpluck's coordination boundary, so callers that may run concurrently must assign different destinations. The Output implementation and policy are otherwise unchanged.

### Added

- Add named `[namespace.<name>]` definitions dedicated to Archive placement. A Namespace is currently an empty table whose name becomes one Archive directory component. The default Scope, named Scopes, and Always sources may reference a Namespace with `namespace = "<name>"`; the Namespace is then always placed outside that source's source root.
- Add `.dirpluck-inv` Invocation Template documents together with `-i PATH` / `--invocation-template PATH` and `-e NAME` / `--entry NAME` for reusable CLI invocations. One file may hold the root `[invocation]` as the default Invocation and multiple `[invocation.<name>]` named entries. Each Invocation independently stores optional `config` / `targets` / `case` / `archive_mtime`; named entries do not inherit fields from the root. The CLI explicitly selects the Template file by a cwd-relative or absolute path, uses the root when `-e` is omitted, and selects a named entry when `-e` is supplied. Relative `config` paths are anchored to the Template file. An Invocation with no fields is valid, uses CLI runtime values and normal defaults, and produces an informational note after a successful preview or build. Positional Target and `--config` overrides, as well as general difference layering, are not provided, while `--case` and `--archive-mtime` may override the selected Invocation's stored runtime values. `--preview`, `--sequence`, `--archive-mtime`, and `--paths` also remain available as runtime modifiers.
- Add concrete Selection-root-relative path references to Selection `ignore`. A one-element nested array whose string begins with `./`, such as `ignore = [["./tests/fixtures/big.bin"], ["./src/generated/"]]`, is interpreted as a path reference rather than a Shared ignore reference. The base is the Target root for Pluck and the source root for an Always source; a trailing `/` explicitly marks a directory. Path references must stay inside the Selection root and reject `..`, absolute paths, globs, and backslashes. Semantic overlap between name patterns, Shared ignores, and path references is valid and acts as a union of exclusions; directory references may prune subtrees before traversal.
- Add a minimal official Python API at the package root for the Beta public surface. `dirpluck.run()` executes the same Configuration / Target / Case / Invocation Template / Entry / preview / Output semantics as the CLI and returns a `RunResult` containing the output path, preview tree, Archive entries, generated README, link-like skip count, and empty-Invocation state. The official package-root exports are limited to `run`, `RunResult`, `DirpluckError`, and `__version__`; lower-level builder, config, invocation, and internal modules remain outside the compatibility contract. The CLI now acts as an argparse adapter over the same application layer.
- Add runtime Archive-entry timestamp control through `--archive-mtime VALUE`, Python `run(archive_mtime=...)`, and Invocation Template `archive_mtime`. `VALUE` accepts `YYYY-MM-DDTHH:MM:SS`, `now`, or `zip-epoch`; a CLI/Python value overrides the selected Invocation's stored value. `now` samples local current time once per run, while `zip-epoch` uses ZIP's minimum timestamp `1980-01-01T00:00:00`. Odd seconds are rounded down to ZIP's two-second precision, and the resolved timestamp is applied to generated README, empty-directory, and source-file entries alike. Omitting the option preserves the existing per-entry timestamp behavior. Fixed mtimes can remove timestamp-driven byte differences and help produce reproducible Archives, but source-file permission bits and other metadata are not normalized and can still change the ZIP bytes. dirpluck does not guarantee byte-for-byte reproducibility of the Archive as a whole.

## 0.8.0

Simplify Target discovery to a direct-child model and add explicit rules for directories that must not become Targets.

### Added

- Add optional `[target].skip` and `[target.location.<name>].skip`. Skip patterns operate on direct child directory names before Target selection, using case-sensitive exact (`name`), prefix (`name*`), suffix (`*name`), or substring (`*name*`) matching. They are distinct from selection `exclude`, which operates inside an already selected Target. Explicit Target references and location expansion both honor the applicable `skip` rules.

### Changed

- Limit positional Target references to `NAME`, `LOCATION/NAME`, and `LOCATION/`. A Target is always exactly one direct child of cwd or of a named Target location. Multi-level Target references, `.` / `..`, `./` forms, and absolute positional Target paths are rejected. `LOCATION/NAME` requires a defined location and never falls back to cwd.
- Make every Target archive root exactly the selected direct child directory name and keep logical Target-location names out of Archive paths. `LOCATION/` expansion applies only to eligible direct child directories after that location's `skip` rules, remains non-recursive, and fails when no eligible direct child Targets remain.

## 0.7.0

Allow Targets to live independently from the Configuration workspace by introducing named Target locations and logical CLI Target references.

### Added

- Add `[target.location.<name>]`. A location is a named filesystem base owned by the Target definition. A relative `path` resolves from the execution root of the Configuration layer that owns that Target; an absolute `path` refers directly to a host filesystem directory. When an outer Target shadows an inner Target, the location set is replaced together with the rest of the Target definition, including its Cases.
- Add named-location expansion with `<location>/`. It expands only the direct child directories of that location into independent runtime Targets; it does not recurse and does not turn regular files into Targets. An undefined location, an expansion with no directories, or a directory symbolic link that resolves outside the location boundary is an error. Normal Target references and expansions may be combined in one run.

### Changed

- Resolve each positional CLI argument as a Target reference rather than as a raw directory path. If the first segment of `work/project` matches an effective Target location, the remaining path resolves from that location; otherwise the whole reference resolves relative to cwd as before. `./work/project` explicitly bypasses location lookup. Absolute positional Target references are rejected; use a Target location for Targets outside cwd.
- For a Target resolved through a Target location, preserve Archive paths relative to the location directory and omit the logical location name. cwd-relative Targets continue to preserve paths relative to cwd. In both cases, the final resolved Target directory remains the file-selection boundary.

## 0.6.2

Adjust documentation distribution after the 0.6.1 publication so sharing guidance is visible at the entry points and the wheel can provide the trust model directly. There are no runtime behavior changes in this release.

### Changed

- Add a short sharing reminder and an example `exclude = [".git/", ".env*", "*.pem", "*.key"]` to the README and the wheel's Configuration quick reference. Bundle `docs/TRUST.md` itself in the wheel so the compact references can link directly to the trust model without requiring the source distribution.

## 0.6.1

Clarify the role of LLM-assisted work and the Configuration trust boundary in the documentation, and remove an unnecessarily strong reproducibility claim. There are no runtime behavior changes in this release.

### Added

- Add `docs/TRUST.md` to explain that a Configuration is an execution instruction for filesystem operations, that `dirpluck` does not infer sensitivity or appropriateness and alter those instructions, and that OS permissions plus explicitly referenced paths form the actual authority boundary. The document distinguishes structural checks such as source-boundary and schema validation from a guard that judges intent or content.

### Changed

- Clarify the README description of LLM-assisted work: `dirpluck` prepares an Archive for upload to a non-local conversational LLM or for placement in a local agent workspace. Remove wording that could imply that an LLM is expected to operate `dirpluck` directly, and route trust-model details to `docs/TRUST.md`.
- Remove the README's `reproducibly` wording. The documentation now describes `dirpluck` in terms of collecting the files declared by a TOML selection intent without implying byte-for-byte reproducibility of the ZIP stream.

## 0.6.0

Expand filesystem-location support, simplify the Archive README into a distribution-friendly content index, and allow a Configuration to describe the Archive as a whole.

### Changed

- Write Configuration filesystem locations with `/` separators on every OS. Companion `path`, import `root`, and Root output `path` / `directory` now accept absolute paths recognized by the host OS, while relative paths handle `.` / `..` according to each field's base. dirpluck does not translate absolute-root notation from another OS, expand `~`, or interpolate environment variables. Include patterns and imported `configuration` remain relative-only and reject backslashes.
- Allow a Companion to directly reference any existing source directory, including locations outside its Configuration execution root, through relative `..` or an absolute `path`. The resolved Companion source directory itself remains the selection boundary, so includes and symbolic links cannot escape it. When the Companion lies outside its resolution base, the resolved source directory's final name becomes the Archive root; host absolute paths, drive names, and UNC share names are never embedded in Archive paths.
- Replace the Archive-root `README.md` resolution report with a simple content index. By default it records only `Path`, `Description`, and `Files`, omitting dirpluck-specific details such as Target / Companion roles, Case, Configuration chain, execution roots, and source filesystem paths. CLI `--paths` adds a `Source` column containing each resolved source directory.

### Added

- Add optional `[about].description`. Across a Configuration chain, the first value found from the outermost layer inward becomes the effective description. When present, it is shown directly below the Archive README heading and before the content index; when absent across the whole chain, no overall description is emitted.

## 0.5.2

Reorganize the public documentation by purpose, make the glossary the conceptual foundation of the documentation set, and keep only the minimal runtime references in the wheel.

### Changed

- Organize the public documentation as `README.md`, `GLOSSARY.md`, and `CHANGELOG.md` at the repository root, with `docs/CLI.md`, `docs/CONFIGURATION.md`, and `docs/SPECIFICATION.md` for detailed reference. Remove the former `USAGE.md` and split CLI operation from TOML Configuration authoring. README now focuses on use cases and adoption, the Glossary on concepts, and the `docs/` documents on details read as needed.
- Remove specification details such as cardinality constraints, shadowing rules, path rules, and validation behavior from `GLOSSARY.md`, leaving it as the shared conceptual vocabulary for the documentation set. Exact behavior is concentrated in `docs/SPECIFICATION.md`; the CLI and Configuration guides explain only what is needed for their tasks and point to the specification when more detail is required.
- Replace the wheel's single `dirpluck/docs/USAGE.md` with two compact references: `dirpluck/docs/CLI.md` and `dirpluck/docs/CONFIGURATION.md`. The full Glossary, detailed guides, Specification, canonical documentation sources, and Japanese intermediate documents remain available from the sdist, separating lightweight runtime reference from deeper investigation.

## 0.5.1

Fix Target binding in the 0.5.0 effective-Configuration model so runtime directories always come from CLI input, independent of the layer that defined the Target.

### Fixed

- When the effective Configuration contains a Target, require one or more CLI `DIRECTORY` arguments whether the Target was defined by the Root Configuration or by an imported layer. Remove the 0.5.0 rule that inferred an imported Target's project directory from Configuration placement and rejected CLI `DIRECTORY`. Target Selection still resolves through the Configuration chain, while runtime Target directories always resolve inside the Root Configuration's execution root.

## 0.5.0

Configuration import is generalized into one linear layering model so that Target, Companion, and Shared-pattern definitions can be composed under the same name-resolution rules from imported Configuration to importing Configuration.

### Changed

- Each Configuration may define at most one `[import.<name>]`, while an imported Configuration may itself import one more. Import-chain depth is unlimited; a repeated Configuration file on the active chain is rejected as a cycle.
- The Configuration chain is resolved from the deepest layer outward into one effective Configuration. Target uses the singleton name `target`; Companions and Shared patterns resolve by their own names. An outer same-named definition shadows the inner definition as a whole. Shared-pattern references are resolved against the final effective namespace, and 0.5.0 no longer requires `<import>.<pattern>` qualification as the name-resolution model.
- A Target that survives from an imported Configuration may now be executed. A Root-owned effective Target still receives CLI `DIRECTORY` values. An imported effective Target is bound to the project directory inferred from `<project>/dirpluck.toml` or `<project>/dirpluck/<name>.toml`. An outer Target shadows the inner Target and all of its Cases.
- Case selection is moved from per-import settings to one Case applied to the effective Configuration. `[import.<name>].case` is no longer used. Shadowing a source also replaces its Case definitions.
- Only the Root Configuration's `[output]` is still executed. Recursive-import version-specific wording is removed; cycles are reported with version-independent Configuration errors that identify the import chain.

## 0.4.1

The current package version is centralized in `dirpluck.__version__`, and document generation uses an external JSON context generated from it.

### Changed

- Stop storing the current release number as glossary vocabulary. Generate the external document-context JSON from `dirpluck.__version__`, and use its `version` value in documents that need the current version. CHANGELOG release labels remain literal historical data in the canonical source.

## 0.4.0

Allow the Root Configuration to explicitly reuse Shared include and exclude patterns from imported Configurations under the import namespace.

### Added

- Expose `[shared.include_patterns]` and `[shared.exclude_patterns]` from an imported Configuration to the Root side under qualified names of the form `<import-name>.<pattern-name>`. Root-local Shared patterns keep their existing local names, and include/exclude namespaces remain distinct.
- Allow qualified imported Shared patterns to be referenced from Root-owned Target, Root Companion, and `[import.<name>.companion.<name>]` base/Case selections. Companions declared by the imported Configuration continue to resolve their own Shared patterns locally inside that Configuration; their references are not rebound into the Root namespace.
- Reject an ambiguous Root-visible Shared-pattern name when a Root-local name collides with the qualified name of an imported Shared pattern of the same kind. Shared-pattern tables are still not merged or applied automatically; every Selection must name the Shared pattern it uses explicitly.

## 0.3.0

Allow a Root Configuration to explicitly import Companions declared by another dirpluck Configuration from a different filesystem root while preserving a separate boundary for each Configuration.

### Added

- Add Configuration imports. A Root Configuration may declare `root`, `configuration`, and optional `case` under `[import.<name>]` to combine the extraction results of Companions declared by another dirpluck Configuration into the same Archive plan. A Root Configuration may also consist only of imports with no local Target or Companion.
- Define import `root` as the only path that may explicitly cross the Root Configuration's cwd boundary. The root is restricted to a relative path from the directory containing the Root Configuration file itself; POSIX, Windows, and UNC absolute forms are rejected regardless of the host OS. After the import root is resolved, `configuration`, imported Companions, and selected files are confined inside that root again so every Configuration keeps an independent filesystem boundary.
- Keep runtime binding explicit across Configuration boundaries: Root CLI `DIRECTORY` and `--case` values do not propagate into imports, imported Targets are not used, and import `case` applies independently only to the imported Companion group. Imported `[output]` definitions are schema-validated but not executed; the Root Configuration's `[output]` remains the only final Output. In 0.3.0, imported Configurations may not recursively import another Configuration.
- Build Archive paths relative to the execution root of the Configuration that selected each file. The same real file selected for the same Archive path is written once; different real files colliding on one Archive path, or one real file resolving to different Archive paths, are rejected as ambiguous. The Archive README records used Configuration imports and their execution roots.
- Allow a Root Configuration to declare `[import.<name>.companion.<companion-name>]` and add sources inside an import root as Companions rather than Targets. Companions under an import use logical names `<import>.<companion>` regardless of whether they come from the imported Configuration or the Root Configuration, and duplicate logical names within one import are rejected. Root-defined import Companions use Root Shared patterns, imported-Configuration Companions keep the imported Shared-pattern namespace, and `path = "."` may select the import root itself.

## 0.2.0

Introduce Shared patterns so extraction conditions can be reused explicitly across Cases and sources.

### Added

- Add Shared patterns. Define named pattern sets as `name = [...]` under `[shared.include_patterns]` and `[shared.exclude_patterns]`, then reference them explicitly from Target or Companion base/Case selections with `include_pattern_refs`, `include_if_exists_pattern_refs`, and `exclude_pattern_refs`. Shared patterns are added only to selections that reference them; they do not inherit from base to Case, merge implicitly, or apply automatically across sources.
- Validate Shared include patterns with the include grammar and Shared exclude patterns with the exclude grammar. A Shared include set may be referenced as required candidates through `include_pattern_refs` or optional candidates through `include_if_exists_pattern_refs`; Shared excludes use `exclude_pattern_refs`. All three forms may be combined with directly written `include`, `include_if_exists`, or `exclude` patterns.
- Expand the sdist as a source distribution suitable for rebuilding and validating a release. In addition to the existing tests and public documents, it now includes the canonical documentation sources and Japanese intermediate documents under `_internal/`, plus the synchronization and distribution-verification tools under `tools/`. `_internal/`, `tools/`, tests, and `.github/` remain excluded from wheels.
- Add a public `USAGE.md` that provides a compact reference for the operational rules needed at use time. Manage it through the existing canonical → Japanese intermediate document → English publication flow, and include it at the repository root, in the sdist, and as `dirpluck/docs/USAGE.md` in the wheel. The wheel now packages `USAGE.md` as its only documentation file; `README.md`, `CONFIGURATION.md`, `GLOSSARY.md`, and `SPECIFICATION.md` remain available from the sdist or repository.

## 0.1.0

First public release.

### Added

- Treat one Configuration file as one extraction intent, producing a ZIP Archive from an optional runtime-bound Target definition and/or one or more fixed Companions, plus one required Output definition. When a Target is defined, one or more CLI directory arguments may instantiate that same Target rule in one run; TOML still defines only one Target rule. A Configuration with no Target runs without positional directories, while supplying any to such a Configuration is an error. Extraction conditions are written directly on each source; there are no named shared extraction rules or bundle references.
- Generalize Case as one flat, Configuration-wide selection variation. When a Target exists it must define the selected Case; Companions with the same Case use it and other Companions fall back to base. Without a Target, a Case is valid when at least one Companion defines it. Case selections are complete alternatives with no inheritance or merge, source membership, Companion paths, and Output policy do not change, and Cases cannot be combined or nested.
- Select fixed-depth relative paths with `include` and `include_if_exists`, allowing at most one `*` per path element. `include` requires at least one match per pattern, while `include_if_exists` permits zero matches. Recursive-anywhere `**` search is not provided.
- Filter selected file or directory names with `exclude` using limited exact, prefix, suffix, and contains matching.
- Default `if_empty` to `error`, while allowing optional-only Target or Companion selections to use `if_empty = "allow"`. Allowed empty selections can be preserved as explicit empty directories in the Archive.
- Preview planned Archive contents with `--dry-run`. Missing required includes are shown as `[missing]`, optional misses as `[optional missing]`, and empty-result policy is reported without creating a ZIP.
- Restrict processing to the current working directory, reject symbolic-link escapes, and allow the Target to be the cwd itself while still preserving the cwd's actual directory name in the Archive.
- Require `description` on every Target or Companion selection, including named Cases, and generate an Archive-root README. When multiple purposes resolve to the same actual directory, files are unioned by real path and the README records each declared purpose.
- Support Python 3.11 and later, distribute dirpluck under the MIT License, and keep runtime third-party dependencies at zero.
- Define PyPI distribution boundaries explicitly: the wheel ships executable code plus the public `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md`, while the sdist additionally includes tests and public source documents. `_internal/` and `.github/` remain repository-only development infrastructure.
- Simplify the normal CLI form to `dirpluck DIRECTORY [DIRECTORY ...]` and remove the `build` subcommand. Discover Configurations only from the cwd and `./dirpluck/`: the default searches for `dirpluck.toml`, while `--config NAME` searches for the same named TOML in both locations. Multiple matches are rejected as ambiguous, and `--configs` lists discoverable candidates and conflicts.
- Rework `README.md` around concrete use cases and the value of repeatable file sets, move TOML authoring guidance into `CONFIGURATION.md`, and keep exact operational semantics in `SPECIFICATION.md`.
- Keep the Archive-root `README.md` as a purpose-neutral index: fixed wording does not identify the generating tool or prescribe downstream use, while Target and Companion `description` values carry concrete purpose.
- Add fixed and generated Output forms. Generated Output uses `directory`, `timestamp = true`, optional `prefix` / `suffix`, and optional CLI `--sequence N` to produce `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip`; existing destinations are rejected during normal execution, with no auto-numbering, auto-renaming, or overwrite mode. Asynchronous and parallel invocations are not coordinated, so callers must avoid concurrent writes to the same output path.
- Clarify in `README.md` and `CONFIGURATION.md` that selecting a directory recursively collects its contents and that dirpluck does not infer or automatically exclude secret-like files such as `.env`, private keys, or `.git`; broad selections require explicit exclusions appropriate to the workspace.
