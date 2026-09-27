# dirpluck Trust Model

This document explains the trust boundary for `dirpluck` Configurations, Invocation Templates, and filesystem operations. It does not define an automatic safety judgment; it describes what the user is responsible for reviewing.

The Specification defines the compatibility contract. See [Filesystem path notation](specification/paths.md) for path resolution, [Selection and Shared patterns](specification/selection.md) and [Filesystem boundaries and entry types](specification/filesystem.md) for Selection and filesystem entries, [Output](specification/output.md) for write behavior, and [Archive planning](specification/archive.md) for Archive construction.

## A Configuration is an execution instruction

A Configuration declares what to select from which filesystem locations and where to write the Archive. `dirpluck` does not infer whether that declaration is appropriate for the user's intent, whether a referenced location is sensitive, or whether a `description` accurately represents its contents.

If a Configuration comes from a third party or has not been reviewed, inspect its `about.base`, Scopes, Always sources, selections, and Output before running it. Treat a Configuration as an execution instruction given to `dirpluck`, not as a sandbox policy or capability manifest.

## An Invocation Template is also an execution instruction

An Invocation Template stores the Configuration document, CLI Target references, and an optional default Case as default or named Invocations. If a `.dirpluck-inv` document comes from a third party, inspect the root `[invocation]` and any `[invocation.<name>]` entry you intend to use, including its `config`, `targets`, and `case`. `-e` / `--entry` selects a named Invocation within the file, and CLI `--case` may override the selected Invocation's `case`.

A named Invocation is independent rather than a difference from the root Invocation, so review the selected entry itself. A relative `config` path is resolved from the Invocation Template file itself, not from the runtime cwd, and the `.dirpluck` suffix may be omitted. When `config` is omitted, `default.dirpluck` in the runtime cwd is used. The CLI `-i PATH` itself is resolved from the runtime cwd when the path is relative. Paths that select or reference Configuration / Invocation Template documents follow the host OS's normal filesystem semantics, so documents reached through symbolic links or Windows directory junctions may be used. Relative references are anchored to the directory of the selected document path, so review both the path and the referenced content before execution. An Invocation Template does not expand the filesystem-access capabilities of a Configuration, but it selects which Configuration and Targets are executed, so an untrusted Template should not be run without review.

## Filesystem permissions are the actual authority boundary

`dirpluck` cannot read or write beyond the permissions of the user running it. Conversely, locations that the user can access and that the Configuration path rules can reference may be used as sources or Output locations. Relative `..` paths and absolute paths are explicit ways to name such filesystem locations.

Relative filesystem paths are resolved from the directory containing the Configuration file in which the field is written, not from the runtime cwd. Each Configuration in a base chain has its own anchor.

`dirpluck` still performs structural validation such as source-boundary enforcement, archive-path collision checks, Configuration-schema validation, and Output write-boundary overlap checks. Configuration / Invocation Template document references and named Scope / Always source-root locations explicitly written in a Configuration follow the host OS's normal filesystem semantics and may use aliases. Separately, during automatic Target discovery and Selection traversal below an explicit root, recognized symbolic links or Windows directory junctions are not followed and are not included in the Archive. Explicit-location resolution and source-tree traversal are separate filesystem boundaries. Special filesystem entries that are neither regular files nor regular directories, such as FIFOs, sockets, and devices, are also excluded from the Archive. These behaviors are not a guard that decides whether a declared filesystem operation is appropriate or safe for a particular purpose.

## The user decides what belongs in a Selection

When a directory is selected with `must` or `may`, regular files and directories below it become candidates for collection. `ignore` may use either name patterns or concrete `./...` path references from the Selection root. It is an explicit instruction that an entry is outside the Selection and takes precedence over diagnostics based on whether the entry is link-like or otherwise special. A subtree matching a directory name ignore or directory path reference is pruned before traversal, and an ignored entry is not used for the skipped-link count or for a special-entry diagnostic. Recognized non-ignored symbolic links or Windows directory junctions are neither selected nor traversed and are not included in the Archive. Other non-regular entries such as FIFOs, sockets, and devices are also not archived. A `must` pattern matching only such special entries fails with an explanatory error, while `may` treats them as optional missing. `dirpluck` does not infer from filenames or contents that hidden files, repository metadata, environment files, key material, or similar files should be ignored automatically.

When Selection traversal recognizes and excludes non-ignored link-like entries, `--preview` and a normal build report the number skipped. Individual paths are not listed, and ignored entries or entries inside a subtree pruned by `ignore` are not counted.

When creating an Archive that will be shared outside the local environment, review the Configuration's `must`, `may`, and `ignore` rules and the resulting contents for that purpose. `--preview` can be used to inspect the archive-relative contents plan.

## Limits of link-like entry detection

`dirpluck` explicitly treats entries that platform APIs identify as symbolic links or Windows directory junctions as non-traversable. Separately, filesystem entries that cannot be treated as regular files or regular directories, such as FIFOs, sockets, and devices, are excluded from the Archive. Filesystems and operating systems may provide other kinds of reparse points, redirection mechanisms, or special filesystem objects, so `dirpluck` does not guarantee that every possible link-like mechanism or filesystem-object meaning can be enumerated or interpreted on every platform, nor that an Archive is absolutely free of every unknown platform-specific mechanism.

The detection boundary is based on the filesystem semantics available during automatic traversal below a source root. When a Configuration explicitly names a named Scope or Always root location, `dirpluck` does not reject that root merely because the location is an alias; it resolves the root using the host OS's normal filesystem semantics. If a supported Windows runtime cannot provide the reparse-tag API or metadata required to classify a directory junction encountered during traversal safely, `dirpluck` reports an error instead of treating the entry as an ordinary directory. Future mechanisms can be added to the recognized set, but unknown platform-specific behavior is not guaranteed in advance.

When the generated ZIP is extracted, interpretation or creation of filesystem objects and entry metadata depends on the extractor and platform. `dirpluck` does not control or guarantee the extraction behavior of third-party unzip or archive software.

## Output follows the declared policy

The filename extension of a fixed Output is not used to determine the ZIP format. `dirpluck` writes a ZIP Archive according to the configured output location and `overwrite` policy. Setting `overwrite = true` explicitly declares that an existing file at the fixed output path may be replaced. The default is `false`.

A timestamp Output creates a `dirpluck`-generated filename only directly under the output directory declared by the Configuration. Within a base chain, `dirpluck` verifies that static Output write boundaries do not overlap, but it does not discover or arbitrate filesystem ownership with unrelated Configuration chains.

`dirpluck` does not lock or arbitrate among multiple processes using the same output path. The existing-destination checks used by `overwrite = false` and timestamp Output are not atomic no-clobber guarantees against another process. If runs may overlap, the caller must assign different output destinations.

Output-file permissions follow the host OS's normal new-file creation semantics rather than a fixed mode inherited from the temporary-file implementation. On POSIX, the process `umask` is applied to the regular-file creation mode. When `overwrite = true` replaces an existing file, `dirpluck` does not preserve or inherit the destination's prior mode; the replacement uses the mode of the newly created Archive for that run. If a particular permission policy is required, such as group-readable output, manage it through the execution environment's `umask` or OS-level permission changes after generation.

Review the output path and existing-file policy in the Configuration before running it when those locations matter.

## When an Archive leaves the local environment

The generated Archive README omits source filesystem paths by default. Only `--paths` adds each resolved source directory to the index. Because those values may expose local-environment information such as absolute paths, review the Archive when using `--paths` for material that will be shared externally.

The files included in the Archive are still selected according to the Configuration. Hiding source paths from the README is not inspection or sanitization of the Archive contents.

## Position in LLM-assisted work

For LLM-assisted work, `dirpluck` can prepare the required local material as a focused Archive. That Archive can be uploaded to a non-local conversational LLM or placed into a workspace used by a local agent.

`dirpluck` does not itself grant an LLM access to the local filesystem, and it does not assume that an LLM operates `dirpluck` directly. The same trust boundary applies regardless of who authored the Configuration.
