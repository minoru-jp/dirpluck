# dirpluck

`dirpluck` is a tool that records decisions about which files belong together in TOML and builds a ZIP Archive from that declaration. The CLI is the primary entry point, and the same invocation model is also available through a small Python API.

Rather than copying everything around it like a backup, it is intended to repeatedly gather only the files needed for a particular purpose, such as review, handoff, research, recurring work, or a working context handled with an LLM.

## Where it fits

### Gather the material you need into one Archive

Material spread across multiple directories can be collected into one Archive when it serves the same purpose.

For example, a review package might bring together:

- the source of the project being reviewed
- review guidelines
- reference material

You can gather only fixed material, or attach fixed material to a Target selected at runtime.

### Apply the same extraction to different Targets

If you record decisions such as "collect README, `src/`, and `tests/`" or "exclude secrets and generated files" in a Configuration, you can reuse the same rules while changing the project being handled.

The Scope from which a Target is selected is defined separately, so the Configuration and the actual project tree do not need to live in the same place.

## Why keep it declarative

For a one-off task, creating a ZIP by hand may be simpler.

`dirpluck` is useful when the same kind of decision needs to be made again later.

A Configuration lets you record:

- what must always be included
- what should be included only when present
- what should be excluded
- which fixed material should be collected alongside the Target

without relying on shell history, conversation history, or human memory.

Use `--preview` to inspect what would be selected from the current filesystem before writing an Archive.

When Configurations need to be shared across related uses, one Configuration can also reuse another as its base. See [docs/configuration/INDEX.md](docs/configuration/INDEX.md) for authoring guidance and [docs/specification/INDEX.md](docs/specification/INDEX.md) for exact composition and resolution rules.

## Before sharing an Archive

`dirpluck` does not infer which files contain sensitive information.

Before creating an Archive that will leave the local environment, use `--preview` to review its contents and explicitly exclude anything that should not be included.

For example, `.env` files, private keys, credentials, and project-specific sensitive files may use different names and locations in different projects.

See [docs/TRUST.md](docs/TRUST.md) for the trust boundary around Configurations and filesystem operations, including absolute paths, overwrite behavior, and Archives intended to leave the local environment.

## Getting started

The shortest end-to-end walkthrough is [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md). It creates a `default.dirpluck`, previews the planned Archive contents, and then builds the Archive.

For Configuration fields and composition, see [Configuration guide](docs/configuration/INDEX.md). For CLI options and Invocation Templates, see [CLI guide](docs/cli/INDEX.md).

## Installation

The current version is **0.10.2**.

Python 3.11 or later is required.

```console
pip install dirpluck
dirpluck --version
```

`dirpluck` has no third-party runtime dependencies.

## Documentation

The documentation is separated by purpose:

- [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md): an end-to-end first run from Configuration to preview and build.
- [GLOSSARY.md](GLOSSARY.md): meanings of the concepts used throughout the documentation.
- [docs/configuration/INDEX.md](docs/configuration/INDEX.md): a guide for writing `.dirpluck` Configurations.
- [docs/cli/INDEX.md](docs/cli/INDEX.md): a guide to the CLI and `.dirpluck-inv` Invocation Templates.
- [docs/python_api/INDEX.md](docs/python_api/INDEX.md): the small official Python API for using the same execution model as the CLI.
- [docs/specification/INDEX.md](docs/specification/INDEX.md): exact rules for Configuration composition, resolution, matching, filesystem traversal, Archives, Output, and validation.
- [docs/TRUST.md](docs/TRUST.md): the trust boundary for Configurations and filesystem operations, and what users are responsible for reviewing.
- [CHANGELOG.md](CHANGELOG.md): release history.
- [STATUS.md](STATUS.md): current development stage, compatibility policy, and publication status.

## License

`dirpluck` is released under the MIT License.

See [LICENSE](LICENSE) for details.
