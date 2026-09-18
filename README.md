# dirpluck

`dirpluck` is a CLI tool for recording a recurring decision, "which files belong together?", in TOML and building a ZIP archive from the same declared intent later.

Rather than copying everything around a workspace like a backup, it is intended to package only the material needed for an explicit purpose such as review, handoff, research, recurring work, or a working context shared with an LLM.

## Where it fits

### Gather fixed material from several locations

When files for one purpose live in different directories, they can be fixed in a Configuration as Companions. A Companion source directory does not need to live near the Configuration and may directly reference another filesystem location.

For example, a review package can combine proposal material, research results, and legal references, or a recurring workflow can gather the same kinds of material each time. A Configuration may consist entirely of Companions when nothing needs to vary at runtime.

### Attach stable references to a changing subject

Use a Target when the same selection rules should be applied to different projects, submissions, cases, or similar subjects. The Target selection stays in the Configuration while the concrete source directory is supplied when `dirpluck` runs.

Stable guidelines, templates, and reference material can remain as Companions in the same archive. This keeps the extraction intent fixed while only the subject changes.

### Reuse an extraction intent declared elsewhere

When a related project already has a Configuration, a Configuration import can use it as an inner layer instead of copying the same definitions into the parent Configuration.

Exact import ordering, shadowing, and filesystem-boundary rules live in [docs/SPECIFICATION.md](docs/SPECIFICATION.md). For the authoring forms needed to write a Configuration, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Why keep the intent as a declaration

For a one-off archive, creating a ZIP by hand may be simpler. `dirpluck` is useful when the same kind of judgment needs to be made again.

A Configuration records what is required, what is optional, what should be excluded, and which fixed references belong with the package. That intent does not have to be reconstructed from shell history, conversation history, or memory. `--dry-run` can show how the current filesystem resolves before anything is written.

For LLM-assisted work, `dirpluck` prepares the material on the local filesystem as an Archive. That Archive can be uploaded to a non-local conversational LLM or placed into the workspace used by a local agent. This workflow does not assume that the LLM operates `dirpluck` itself.

## Configuration and filesystem trust

`dirpluck` is not a guard that infers whether a filesystem operation declared in a Configuration is appropriate. It applies the declared selection and output according to its documented rules.

See [docs/TRUST.md](docs/TRUST.md) for how to treat Configurations, broad selections, absolute paths, overwrite behavior, and Archives that will leave the local environment.

## A small example

The following Configuration combines a runtime Target with fixed review guidelines:

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck projects/example --dry-run
dirpluck projects/example
```

For all Configuration fields and a larger example, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md). For CLI options and Configuration discovery, see [docs/CLI.md](docs/CLI.md).

## Installation

Python 3.11 or later is required. The current release is `0.6.1`.

```console
pip install dirpluck
dirpluck --version
```

`dirpluck` has no third-party runtime dependencies.

## Documentation

The documents are separated by reading purpose:

- [GLOSSARY.md](GLOSSARY.md): the concepts used throughout the documentation.
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md): how to write TOML Configurations.
- [docs/CLI.md](docs/CLI.md): how to operate the CLI.
- [docs/SPECIFICATION.md](docs/SPECIFICATION.md): exact rules for resolution, matching, filesystem boundaries, archives, output, and validation.
- [docs/TRUST.md](docs/TRUST.md): the trust boundary for Configurations and filesystem operations.
- [CHANGELOG.md](CHANGELOG.md): release history.

The wheel includes only compact `dirpluck/docs/CONFIGURATION.md` and `dirpluck/docs/CLI.md` references so an installed package contains enough information to write a Configuration and run the CLI. For more detail, use the documentation in the source distribution or repository.

## Public interface

The compatibility-supported public surface is the `dirpluck` CLI and the TOML Configuration format. Python modules inside the package are internal implementation unless explicitly documented as a public API.
