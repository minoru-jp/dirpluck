# dirpluck Project Status

This document describes dirpluck's current development stage, compatibility policy, and the criteria for moving toward 1.0.

The `0.16.x` line is **Beta**. Version 0.9.0 made the major reorganization of the Configuration language and filesystem model, and from 0.10.0 onward the project strongly favored preserving the published surface. Real-world use since then has shown that design issues still remain that should be corrected before 1.0, so 0.16.0 revises the compatibility policy for the remainder of the 0.x series.

## Current status

The current public version line is `0.16.x`, and the development stage is **Beta**.

The remaining 0.x series is a design-convergence period for defining the 1.0.0 public contract. The project will reduce migration burden where practical, but it will not freeze a design that is unsuitable for 1.0 solely for compatibility.

0.15.0 was not published; the contract changes planned for it are folded into 0.16.0. The 0.16.0 implementation also reorganizes the internal execution model into three stages: input parsing / normalization, extraction from the filesystem, and Archive / message output. This direction is the internal foundation for 1.0: later stages should not reinterpret public grammar, and each layer should avoid depending unnecessarily on the input language of the previous layer or the presentation format of the next one.

## Stability policy

From 0.10.0 onward, dirpluck followed a policy of generally avoiding breaking changes to the published Configuration language, CLI, official Python API, and Archive semantics. Real-world use, including the 0.13.0 entry-type redesign and the 0.16.0 Always Archive-identity redesign, showed that further corrections to core design are still needed before 1.0. That pre-1.0 policy is withdrawn as of 0.16.0.

From 0.16.0 through the release immediately before 1.0.0, 0.x releases may make breaking changes when they are needed for correctness, safety, predictability, design consistency, or the long-term 1.0 public contract. Avoiding a breaking change is no longer the overriding priority.

Breaking changes will not be introduced silently. Where technically useful, the project will provide deprecation periods, migration warnings, Migration Guides, and explicit before/after examples. Old usages or output changes that can be detected automatically should be surfaced through both the CLI and the official Python API. Legacy design will not be retained indefinitely as a compatibility mode solely to avoid migration.

Human-facing generated output, such as the generated Archive README and diagnostic messages, is different: its exact wording and formatting are not treated as a stable machine-readable interface. Those details may change in later releases to improve readability or clarity. Programmatic integrations should depend on the explicitly documented public contracts such as Configuration, CLI, the official Python API, and Archive semantics rather than parsing the exact presentation of human-facing output.

Internal modules, repository-local development tools, and the documentation-generation workspace are outside this compatibility policy.

## Beta goals

During Beta, the project will especially verify that:

- the Configuration model has clear responsibility boundaries and remains practical for real project trees and shareable Archive creation;
- the CLI and official Python API provide the same invocation semantics and migration diagnostics;
- the major contracts around Scope, Selection, Base, Namespace, Always, Output, and Archive planning converge on their 1.0 forms;
- the `parse / normalize → extract → output` responsibility boundary remains intact, without input-language concepts or presentation concerns flowing into layers that do not need them;
- awkward semantic boundaries discovered through real use are corrected before 1.0, including with breaking changes when necessary;
- deprecations, warnings, and Migration Guides are available when appropriate for those changes; and
- documentation, diagnostics, platform compatibility, and other usability improvements continue throughout the convergence period.

## Path to 1.0

Dirpluck will move to `1.0.0` after the required 0.x design corrections and migrations are complete and the Configuration, CLI, official Python API, and filesystem / Archive model can be fixed as a stable public contract.

The criterion for 1.0 is not an unlimited accumulation of features. The priority is to avoid carrying known core design problems into 1.0, retire migration warnings and pre-1.0 compatibility semantics that are no longer needed, and reach a state where compatibility can be maintained strongly after the 1.0 boundary.

## Documentation tooling

The canonical-source / canonical-document pipeline for published documentation uses `shikumi-devdoc>=0.3.2`. This is a repository-development dependency and is not a dirpluck runtime dependency.

Regenerating canonical documents in the public source repository assumes that the required Shikumi 0.2.0 and shikumi-devdoc 0.3.2 releases are already available. Repository-specific orchestration, including which documents are generated, where they are written, and which project context is supplied, remains in `tools/render_canonical_docs.py` rather than being pushed into shikumi-devdoc's generic API.

## Distribution note

Dirpluck is published as a package on PyPI, and its source repository is public at [https://github.com/minoru-jp/dirpluck](https://github.com/minoru-jp/dirpluck).

To keep documentation navigation working from the PyPI project description as well as from GitHub, the root README uses absolute URLs for published documents on the repository's `main` branch. Package metadata uses the same public repository as the basis for Homepage, Documentation, Repository, Issues, and Changelog project URLs.

The wheel continues to bundle the README, Glossary, CLI / Configuration / Python API guides, Trust model, Specification, CHANGELOG, and STATUS for the same release under `dirpluck/_docs/`. Reading the documentation bundled in an installed wheel does not require network access.
