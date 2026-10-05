# Specification overview

This specification defines the compatibility-relevant semantics of the `dirpluck` CLI, `.dirpluck` Configuration documents, and `.dirpluck-inv` Invocation Template documents. Both document formats use TOML syntax. The official package-root Python API surface and the calling contract of `run()` are defined in `../python_api/INDEX.md`; Configuration, Target, Case, Invocation, and Archive semantics executed by `run()` are shared with this specification. See `../../README.md` for purpose, `../../GLOSSARY.md` for terminology, `../configuration/INDEX.md` for Configuration authoring, `../cli/INDEX.md` for CLI operation, and `../TRUST.md` for the trust boundary around Configuration / Invocation Template inputs and filesystem operations.

Pre-1.0 compatibility inputs and behaviors that are explicitly scheduled for removal in 1.0.0 are isolated in [Pre-1.0 compatibility](compatibility.md). The ordinary Specification documents contain only canonical semantics that are candidates for the 1.0 contract. Except for items explicitly marked for removal in `compatibility.md`, the current canonical CLI / Configuration / Invocation Template notation and grammar are retained as 1.0 contract candidates.

## SECTION_001

title: Public surface

### SPEC_001

The compatibility-supported public surface is the `dirpluck` CLI, the `.dirpluck` Configuration and `.dirpluck-inv` Invocation Template document formats defined by this document, and the package-root Python API explicitly defined in [Python API](../python_api/INDEX.md). Both document types use TOML syntax. Python modules and names that are not explicitly exported from the package root are internal implementation.

level: MUST
