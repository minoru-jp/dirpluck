# Specification overview

This document defines the exact compatibility-supported behavior of the `dirpluck` CLI, the `.dirpluck` Configuration document format, and the `.dirpluck-inv` Invocation Template document format. Both document types use TOML syntax. The official package-root Python API surface and the calling contract of `run()` are defined in [Python API](../python_api/INDEX.md); the Configuration, Target, Case, Invocation, and Archive semantics executed by `run()` are the same semantics defined here. For purpose and positioning, see [README](../../README.md). For term meanings, see [Glossary](../../GLOSSARY.md). For TOML authoring, see [Configuration guide](../configuration/INDEX.md). For CLI operation, see [CLI guide](../cli/INDEX.md). For the trust boundary around Configurations, Invocation Templates, and filesystem operations, see [Trust model](../TRUST.md).

## SECTION_001

title: Public surface

### SPEC_001

The compatibility-supported public surface is the `dirpluck` CLI, the `.dirpluck` Configuration and `.dirpluck-inv` Invocation Template document formats defined by this document, and the package-root Python API explicitly defined in [Python API](../python_api/INDEX.md). Both document types use TOML syntax. Python modules and names that are not explicitly exported from the package root are internal implementation.

level: MUST
