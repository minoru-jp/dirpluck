# Filesystem path notation

## SPEC_017

Filesystem locations in Configuration / Invocation Template TOML fields, CLI `--config PATH` / `-i PATH` / `--output PATH`, and Python runtime `output` use `/` as the path separator regardless of the host OS. Backslash is not accepted as a separator; `/` is used on Windows as well.

level: MUST

## SPEC_018

A relative filesystem path written in a Configuration is resolved from the **directory containing the Configuration file in which that field is written**. This rule applies at least to:

```text
about.base
scope.<name>.path
always.<name>.path
output.path
output.timestamp.path
```

level: MUST

## SPEC_019

A relative path written in an inner Configuration of a base chain is resolved from the inner Configuration's own directory and is not rebased to an outer Configuration's directory.

level: MUST

## SPEC_020

An absolute path uses `/` separators in a root form recognized by the host OS as a complete absolute path and refers directly to that location. Examples include `/opt/data` on a POSIX host and `C:/data` or `//server/share/data` on a Windows host. `dirpluck` does not automatically convert a root form from another OS. A Windows drive-relative form such as `C:foo` is not treated as an absolute path.

level: MUST

## SPEC_021

Filesystem-location notation does not perform `~` expansion or environment-variable interpolation and does not accept globs. `.` and `..` are resolved as ordinary path components when they satisfy the field- or option-specific file or directory requirements. A Configuration or CLI document selection that uses an absolute path depends on the referenced filesystem and is not guaranteed to be portable across operating systems.

level: MUST

## SPEC_022

CLI `--config PATH`, `-i PATH`, and `--output PATH`, plus Python runtime `output`, use the runtime cwd as the resolution base for relative paths. A `config` path inside either the default or a named Invocation is resolved from the Template document's own directory. Runtime cwd is not used to resolve relative filesystem paths written inside a Configuration after it has been loaded.

level: MUST

## SPEC_023

Paths that **select or reference Configuration / Invocation Template documents themselves** follow the host OS's normal filesystem semantics; symbolic links and Windows directory junctions are not rejected merely for appearing in the path. For the runtime-cwd `default.dirpluck`, `--config PATH`, `-i PATH`, `about.base`, and an Invocation's `config`, dirpluck keeps the selected or referenced path as a lexical absolute document location rather than replacing it with the physical path of a link target. Relative document references and relative filesystem locations written in that document are anchored to the directory of this document location. Only internal checks that need path identity, such as base-chain cycle detection, resolve aliases to a physical path so equivalent document-path aliases are recognized.

level: MUST

## SPEC_024

This control-document rule is separate from source-root resolution and source-tree link handling. Explicit source-root locations written by a Configuration, such as `[scope.<name>].path` and `[always.<name>].path`, follow the host OS's normal filesystem semantics and are not rejected merely because an intermediate or final path component is a symbolic link or Windows directory junction. After an explicit location resolves to an existing directory, that directory becomes the source root or Selection boundary. During the automatic Target discovery or Selection traversal that begins from that root, recognized link-like entries are not selected or traversed under the link-like-entry rule in Filesystem boundary and entry types. Values that are not filesystem locations, including include patterns, ignore patterns, archive paths, and CLI Target references, follow their own rules.

level: MUST
