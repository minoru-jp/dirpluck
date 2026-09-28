# Filesystem boundaries and non-regular entries

## SPEC_088

A Configuration file's directory is the resolution anchor for relative Configuration paths; it is not a shared boundary that confines all sources beneath it.

level: MUST

## SPEC_089

A runtime Target is resolved as a direct child of its corresponding Scope root. `target_kind` is the type filter for direct-child Target candidates: `"directory"` permits directories, `"file"` permits regular files, and `"both"` permits both. After resolution, a directory Target uses that directory itself as the Selection boundary, while a file Target treats the regular file itself as an atomic source and performs no Selection traversal inside it. The Scope root is the base for finding Target candidates.

level: MUST

## SPEC_090

Explicit named-Scope and Always source-root locations may resolve an existing directory through a relative or absolute `path` using the host OS's normal filesystem semantics, including locations that contain symbolic links or Windows directory junctions. For an Always source, the resolved source directory itself becomes the Selection boundary. Output locations do not participate in source boundaries.

level: MUST

## SPEC_091

Include resolution and selected files for each directory source are confined to that source directory, while a file Target is confined to the selected regular file itself. Only regular files are included in the Archive; regular directories are used only for traversal. An entry recognized as a symbolic link during Target discovery or Selection traversal is not selectable: `dirpluck` does not resolve or traverse its target and does not include the link in the Archive. On Windows, directory junctions are treated as the same kind of link-like entry. File symlinks, directory symlinks, broken symlinks, and recognized Windows directory junctions are all non-traversable. Other non-regular entries such as FIFOs, sockets, and devices are likewise not archived and are not traversed as directories.

level: MUST

related: [SPEC_050](runtime-targets.md#spec_050), [SPEC_052](runtime-targets.md#spec_052), [SPEC_077](selection.md#spec_077)

## SPEC_092

To recognize Windows directory junctions while retaining Python 3.11 support, `dirpluck` uses the reparse tag returned by `lstat` on Windows. The decision is centralized in one internal helper used by Target discovery, Selection traversal, and other runtime filesystem checks that reject link-like entries. Control-document path resolution does not use this link-like test. If a supported Windows runtime cannot provide the reparse-tag constant or stat metadata required to distinguish junctions safely, `dirpluck` fails instead of treating the entry as an ordinary directory and continuing traversal. This is a safety boundary for known symbolic links and directory junctions; it does not guarantee complete detection of every possible reparse point or unknown redirection mechanism available on a platform.

level: MUST

condition: when detecting directory junctions on Windows

## SPEC_093

Recognized **non-ignored** link-like entries excluded during Selection traversal are counted once per path even if the same path is observed through multiple patterns. `--preview` reports the total after the contents tree, and a normal build reports it after the output path. Individual link paths are not displayed, and the runtime note is not written to the Archive `README.md`. Link-like entries that match `ignore`, and entries inside a subtree pruned by directory `ignore`, are not included in the skipped-link count.

level: MUST

condition: when Selection traversal excludes a non-ignored link-like entry

## SPEC_094

This rule applies to entries encountered while automatically traversing a source tree from its root. Explicit filesystem paths such as `about.base`, named Scope `path`, Always `path`, and Output `path` follow the Filesystem path notation rules and the rules specific to each field. In particular, an alias may be used for a named Scope or Always root location without implying that Target discovery or Selection traversal may follow another link-like entry below that root. Interpretation of entries or filesystem objects when the generated ZIP is extracted depends on the extractor and platform; `dirpluck` does not guarantee the behavior of third-party extraction software.

level: MUST

related: [SPEC_023](paths.md#spec_023), [SPEC_024](paths.md#spec_024)
