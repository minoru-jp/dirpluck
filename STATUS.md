# dirpluck Project Status

This document describes dirpluck's current development stage, compatibility policy, and the criteria for moving toward 1.0.

The `0.13.x` line is **Beta**. Version 0.9.0 made the major reorganization of the Configuration language and filesystem model, and 0.10.0 aligns runtime Output and the published documentation structure with the current design. From this point, the project will validate that public surface in real use while actively preserving compatibility.

## Current status

The current public version line is `0.13.x`, and the development stage is **Beta**.

Beta is not a period for freely redesigning public interfaces. The goal is to verify in real use that the current Configuration, CLI, official Python API, and Archive semantics can be used continuously, while making necessary improvements additively wherever possible.

## Stability policy

From 0.10.0 onward, breaking changes to the published Configuration language, CLI, official Python API, and Archive semantics will be avoided except for compelling reasons.

Compelling reasons include defects where preserving the existing behavior would damage correctness, safety, or core design consistency. Ordinary feature additions and improvements should be additive. If an existing interface must be replaced, the project will provide deprecation and a migration period where practical.

`0.13.0` is an explicit exception: it corrects an early design in which inclusion Selection and Target references inferred file-versus-directory meaning from the current filesystem, and replaces that inference with trailing-`/` type notation. `ignore` remains intentionally broad on the exclusion side: no trailing `/` applies to files and directories, while a trailing `/` narrows the exclusion to directories only. Migration is documented in the CHANGELOG. This exception does not relax the compatibility policy for later releases.

Human-facing generated output, such as the generated Archive README and diagnostic messages, is different: its exact wording and formatting are not treated as a stable machine-readable interface. Those details may change in later releases to improve readability or clarity. Programmatic integrations should depend on the explicitly documented public contracts such as Configuration, CLI, the official Python API, and Archive semantics rather than parsing the exact presentation of human-facing output.

Internal modules, repository-local development tools, and the documentation-generation workspace are outside this compatibility policy.

## Beta goals

During Beta, the project will especially verify that:

- the current Configuration model remains practical for real project trees and shareable Archive creation;
- the CLI and official Python API continue to provide the same invocation semantics reliably;
- the major contracts around Scope, Selection, Base, Namespace, Output, and Archive planning do not require fundamental redesign;
- new functionality can be added without breaking existing semantic boundaries; and
- documentation, diagnostics, platform compatibility, and other usability improvements can continue without destabilizing the public contract.

## Path to 1.0

After sufficient real-world use, when there is no identified need for a major redesign or other breaking architectural change, dirpluck will move to `1.0.0` using the current design as its foundation.

The criterion for 1.0 is not an unlimited accumulation of features. The important point is confidence that the current public interfaces and filesystem / Archive model form a stable contract that can be used continuously.

## Documentation tooling

The canonical-source / canonical-document pipeline for published documentation uses `shikumi-devdoc>=0.3.0`. This is a repository-development dependency and is not a dirpluck runtime dependency.

When this source repository is published on the web, the required Shikumi 0.2.0 and shikumi-devdoc 0.3.0 releases are assumed to have already been published. Repository-specific orchestration, including which documents are generated, where they are written, and which project context is supplied, remains in `tools/render_canonical_docs.py` rather than being pushed into shikumi-devdoc's generic API.

## Distribution note

At this stage, dirpluck is published **only through PyPI**, with no public web page for browsing the source repository yet.

As a result, some repository-relative links in the README and other published documents do not resolve on PyPI. This is a known limitation of the current distribution arrangement.

When the source repository is later published on a service such as GitHub, documentation links will be reviewed against the public repository URL and adjusted so they resolve from the public environment.

Because there is not yet a public repository, there is also no hosted CI. Pre-release tests, canonical-document regeneration checks, distribution verification, and PyPI uploads are performed locally. CI and release workflows will be configured for the public environment when the repository is published on GitHub.
