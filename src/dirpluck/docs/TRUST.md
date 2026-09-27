# dirpluck Trust Quick Reference

This is the compact trust reference bundled with the installed package. For the complete trust model, see `docs/TRUST.md` in the source distribution for the same release. For the exact compatibility contract, see `docs/specification/INDEX.md` there.

## Configuration and Invocation Templates

Configurations and Invocation Templates are both execution instructions. Before running a document received from a third party, review the Configuration, Targets, Case, Scope / Always sources, Selection, and Output it will use. `dirpluck` does not infer whether a referenced location is sensitive, whether a `description` matches reality, or whether a declared operation is safe for the user's purpose.

## Filesystem boundary

`dirpluck` cannot read or write beyond the OS permissions of the user running it. Conversely, relative `..` paths and absolute paths that the user can access and the Configuration path rules allow may be used as sources or Output locations.

Configuration / Invocation Template documents and explicitly declared Scope / Always root locations follow the host OS's normal filesystem semantics. During automatic traversal below an explicit root, recognized symbolic links and Windows directory junctions are not followed or archived. Entries that are not regular files or regular directories, such as FIFOs, sockets, and devices, are also excluded. This does not guarantee classification of every unknown platform-specific mechanism.

## Selection and preview

`dirpluck` does not infer from filenames or contents that hidden files, repository metadata, environment files, key material, or similar files should be ignored automatically. Before sharing an Archive, review the `must`, `may`, and `ignore` rules and the actual generated contents for that purpose.

`--preview` shows the archive-relative contents plan without writing the Archive. It also reports the count of recognized non-ignored link-like entries excluded during traversal.

## Output and sharing

Output follows the destination and overwrite policy declared by the Configuration or runtime options. `dirpluck` does not provide process locking or collision arbitration for concurrent runs targeting the same output path.

The generated Archive README omits source filesystem paths by default, but `--paths` may record local-environment information such as absolute paths. Omitting paths from the README is not inspection or sanitization of the Archive contents.
