# dirpluck

`dirpluck` is a CLI tool for selecting the files you need from multiple locations and collecting them into a single ZIP Archive.

A TOML Configuration records what to include, what to exclude, which fixed material should always be attached, and which additional material should be activated only for selected Cases. For example, when handing a repository to an LLM for development work, you can package the current development target, working instructions, and local wheels needed only in some environments into a reproducible Archive built from the same rules.

## Installation

The current version is **0.18.0**.

Python 3.11 or later is required.

```console
pip install dirpluck
dirpluck --version
```

`dirpluck` has no third-party runtime dependencies.

If you are upgrading from 0.16.x, see [Migrating to 0.17](https://github.com/minoru-jp/dirpluck/blob/main/docs/migration/0.17.md) for the final Archive-root uniqueness change and the move to Layout. If you are upgrading from 0.14.x or earlier, also review [Migrating to 0.16](https://github.com/minoru-jp/dirpluck/blob/main/docs/migration/0.16.md) for the earlier Always Archive-identity change.

## Example: hand an LLM a development handoff Archive

As a representative example, build a handoff Archive for LLM-assisted development. The complete version lives in the [LLM development environment Recipe](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/llm-development-environment.md); this README keeps only the main structure.

Suppose you have this workspace:

```text
workspace/
├── default.dirpluck
├── handoff/
│   └── DEVELOPMENT.md
├── offline_wheels/
│   └── ...
└── projects/
    ├── service-api/
    └── worker-jobs/
```

Create `default.dirpluck` at the workspace root:

```toml
[about]
description = "A handoff Archive for LLM-assisted development."
description_no_targets = "No development Target was selected."
description_no_always = "No support source is active."
description_empty = "No source was selected; this Archive contains only the generated README."
always_layout = "support"
targets_layout = "development-targets"

[layout.support]
description = "Working instructions used during development."

[layout.dependencies]
description = "Development dependencies used in offline environments."

[layout.development-targets]
description = "Repositories selected as development targets for this task."

[always.handoff]
description = "Development instructions attached to every normal handoff."
path = "handoff"
must = ["DEVELOPMENT.md"]

[extra.offline_wheels]
description = "A wheelhouse for environments that cannot reach a package index."
path = "offline_wheels"
must = ["*.whl"]
layout = "dependencies"

[scope.projects]
description = "Repositories that can be selected as development targets."
path = "projects"

[pluck]
description = "Normal project files to hand to the LLM."
may = ["*", "*/"]
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pyc",
]

[case.always.offline]
description = "The destination cannot reach a package index."
include = ["handoff", "offline_wheels"]

[output]
path = "develop-target.zip"
overwrite = true
```

In this example, working instructions that are always needed are defined with `always`, while the wheelhouse needed only for offline environments is defined with `extra`. An Extra source is inactive merely by being declared and becomes active only for runs where an Always Case such as `.offline` adds it.

Layouts separate support material, dependencies, and development Targets inside the Archive. Conditional descriptions such as `description_no_targets` add context to the generated README according to which sources are present, while the ordinary `description` is always shown.

### Preview and build

Preview a normal handoff without activating the Extra source:

```console
dirpluck projects/service-api/ --preview
```

For a destination that cannot reach a package index, select the `.offline` Always Case:

```console
dirpluck projects/service-api/ --case .offline --preview
```

Conceptually, the resulting Archive looks like this:

```text
develop-target.zip
├── README.md
├── support/
│   └── handoff/
│       └── DEVELOPMENT.md
├── dependencies/
│   └── offline_wheels/
│       └── ...
└── development-targets/
    └── service-api/
        └── ...
```

If the preview looks correct, remove `--preview` to build the ZIP. See the [Recipe](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/llm-development-environment.md) for the complete example, including combined Pluck / Always Cases and a README-only Archive.

### Filesystem note

Symbolic links and recognized Windows directory junctions encountered during automatic Target discovery or Selection traversal are not followed or included in the Archive. See [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) for the exact filesystem boundary.

## Before sharing an Archive

`dirpluck` does not infer from filenames or contents that something is sensitive and should not be shared.

The example ignore list for `.git/`, `.venv/`, `.env*`, `*.pem`, `*.key`, and similar entries is useful, but it is **not a security boundary**. Project-specific credentials, private keys, personal information, customer data, local settings, test fixtures, or other sensitive material may exist under completely different names or locations.

Before sending an Archive to another party or to a non-local LLM, inspect the selection with `--preview`.

A Configuration is also an instruction for filesystem operations. Named Scopes and Always / Extra sources can reference local filesystem locations, and Output declares where the Archive is written. Do not run a Configuration received from someone else, or one you have not reviewed, without checking its referenced sources, Base Configuration, Selection, and Output.

The generated Archive README does not include source filesystem paths by default. If `--paths` is used, resolved source paths are added and may reveal local-environment information such as absolute paths.

See [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) for the detailed trust boundary and guidance for Archives that will leave the local environment.

## Why dirpluck?

For a one-off ZIP, doing the work by hand may be simpler.

`dirpluck` is useful when the decision about what to hand off needs to be reused later. Recording the rules in a Configuration lets you reconstruct an Archive from the same intent without relying on shell history, past conversations, or human memory.

You can change the Target, select multiple Targets together, attach fixed material with `always`, activate additional material only for selected runs with `extra` and an Always Case, and use Layouts to separate roles inside the Archive.

## Documentation

This README introduces the basic workflow through one concrete example.

- [Getting Started](https://github.com/minoru-jp/dirpluck/blob/main/docs/GETTING_STARTED.md): a short walkthrough from a minimal Configuration to preview and build.
- [Recipes](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/INDEX.md): use-case guides that start from a real workspace and goal, then show the matching TOML and CLI patterns.
- [Glossary](https://github.com/minoru-jp/dirpluck/blob/main/GLOSSARY.md): meanings of the concepts used throughout the documentation.
- [Configuration Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/configuration/INDEX.md): Configuration authoring, including Scope, Always, Extra, Layout, Shared, Case, and Base Configuration.
- [CLI Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/cli/INDEX.md): Target references, CLI options, and Invocation Templates.
- [Python API](https://github.com/minoru-jp/dirpluck/blob/main/docs/python_api/INDEX.md): the small official Python API for the same execution model as the CLI.
- [Specification](https://github.com/minoru-jp/dirpluck/blob/main/docs/specification/INDEX.md): exact rules for Configuration composition, resolution, matching, filesystem traversal, Archives, Output, and validation.
- [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md): the trust boundary for Configurations, filesystem access, and external sharing.
- [Changelog](https://github.com/minoru-jp/dirpluck/blob/main/CHANGELOG.md): release history.
- [Status](https://github.com/minoru-jp/dirpluck/blob/main/STATUS.md): current development stage, compatibility policy, and publication status.

## License

`dirpluck` is released under the MIT License.

See [LICENSE](https://github.com/minoru-jp/dirpluck/blob/main/LICENSE) for details.
