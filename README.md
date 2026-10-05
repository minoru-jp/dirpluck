# dirpluck

`dirpluck` is a CLI tool for selecting the files you need from multiple locations and collecting them into a single ZIP Archive.

A TOML Configuration records what to include, what to exclude, and which fixed material should always be attached. For example, when handing repositories to an LLM for development work, you can package the current development targets, a shared framework, local wheels needed for the task, and related repositories into a reproducible Archive built from the same rules.

## Installation

The current version is **0.16.0**.

Python 3.11 or later is required.

```console
pip install dirpluck
dirpluck --version
```

`dirpluck` has no third-party runtime dependencies.

If you are upgrading from 0.14.x, see [Migrating to 0.16](https://github.com/minoru-jp/dirpluck/blob/main/docs/migration/0.16.md) for the breaking Always Archive-layout change.

## Example: prepare development context for an LLM

Suppose you have this workspace:

```text
workspace/
├── default.dirpluck
├── framework-core/
│   └── dist/
│       └── framework_core-2.4.0-py3-none-any.whl
├── docs-builder/
│   └── dist/
│       └── docs_builder-1.6.0-py3-none-any.whl
└── repositories/
    ├── service-api/
    │   ├── src/
    │   └── .tmp/
    │       └── proposed-changes.patch
    ├── worker-jobs/
    └── web-console/
```

`repositories/` contains several repositories built on the same foundation. For this task, `service-api` and `web-console` are the development targets to give to the LLM. The `framework-core` and `docs-builder` wheels are needed regardless of which Target is selected, so they should always be included in the Archive. `service-api/.tmp/` contains a downloaded diff to review in a separate workflow.

Create `default.dirpluck` at the workspace root:

```toml
[about]
description = "Repositories and runtime dependencies for LLM-assisted development."

[namespace.repositories]

[always.dependencies]
description = "The foundational framework used by the target repositories."
path = "framework-core/dist"
must = ["*.whl"]

[always.tools]
description = "A tool used to build development documentation."
path = "docs-builder/dist"
must = ["*.whl"]

[scope.projects]
description = "Repositories that can be selected as development targets."
path = "repositories"
namespace = "repositories"
ignore = ["archive/", "scratch/"]

[shared.ignore]
repository-noise = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]

[pluck]
description = "Repositories selected as development targets for this LLM task."
may = ["*", "*/"]
ignore = [
    { shared = "repository-noise" },
    { path = "private/local-notes/" },
    { path = ".tmp/" },
]

[case.pluck.diff]
description = "Development target repository; .tmp/ contains the diff to review."
may = ["*", "*/"]
ignore = [
    { shared = "repository-noise" },
    { path = "private/local-notes/" },
]

[output]
path = "develop-target.zip"
overwrite = true
```

`always` adds fixed material regardless of the selected Target. `scope.projects` defines where selectable repositories live, and `pluck` applies the same Selection to each selected directory Target. Normally `.tmp/` is excluded; the `diff` Case includes it when the downloaded changes should be reviewed. `description` does not change selection semantics, but it is carried into the generated Archive README so a person or LLM can distinguish the development targets, foundation, and supporting tools.

### Preview

Before creating the Archive, inspect what will be collected. In this example, commands are run from the workspace root, so `default.dirpluck` is used automatically.

```console
dirpluck projects/service-api/ projects/web-console/ --preview
```

`--preview` shows what would be selected from the current filesystem without writing the ZIP. Check that nothing unexpected is included and that required files are not missing.

### Add a diff with a Case

The normal Selection excludes `.tmp/`. When `service-api/.tmp/proposed-changes.patch` should be included for review, select the `diff` Case:

```console
dirpluck projects/service-api/ --case diff --preview
```

`--case diff` uses the Selection from `[case.pluck.diff]`, so `.tmp/` is included only for this run. The Case `description` is also carried into the generated Archive README. After inspection, remove `--preview` from the same command to build the Archive.

### Build

If the preview looks right, build the Archive with the same Targets:

```console
dirpluck projects/service-api/ projects/web-console/
```

Conceptually, the resulting Archive looks like this:

```text
develop-target.zip
├── README.md
├── dependencies/
│   └── framework_core-2.4.0-py3-none-any.whl
├── repositories/
│   ├── service-api/
│   │   └── ...
│   └── web-console/
│       └── ...
└── tools/
    └── docs_builder-1.6.0-py3-none-any.whl
```

For another task, change only the Target:

```console
dirpluck projects/worker-jobs/ --preview
```

The collection rules and fixed material recorded in the Configuration stay the same.

### Filesystem note

Symbolic links and recognized Windows directory junctions encountered during automatic Target discovery or Selection traversal are not followed or included in the Archive. See [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) for the exact filesystem boundary.

## Before sharing an Archive

`dirpluck` does not infer from filenames or contents that something is sensitive and should not be shared.

The example ignore list for `.git/`, `.venv/`, `.env*`, `*.pem`, `*.key`, and similar entries is useful, but it is **not a security boundary**. Project-specific credentials, private keys, personal information, customer data, local settings, test fixtures, or other sensitive material may exist under completely different names or locations.

Before sending an Archive to another party or to a non-local LLM, inspect the selection with `--preview`.

A Configuration is also an instruction for filesystem operations. Named Scopes and Always sources can reference local filesystem locations, and Output declares where the Archive is written. Do not run a Configuration received from someone else, or one you have not reviewed, without checking its referenced sources, Base Configuration, Selection, and Output.

The generated Archive README does not include source filesystem paths by default. If `--paths` is used, resolved source paths are added and may reveal local-environment information such as absolute paths.

See [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md) for the detailed trust boundary and guidance for Archives that will leave the local environment.

## Why dirpluck?

For a one-off ZIP, doing the work by hand may be simpler.

`dirpluck` is useful when the decision about what to hand off needs to be reused later. Recording the rules in a Configuration lets you reconstruct an Archive from the same intent without relying on shell history, past conversations, or human memory.

You can change the Target, select multiple Targets together, and attach fixed material with `always` while keeping the collection rules reusable.

## Documentation

This README introduces the basic workflow through one concrete example.

- [Getting Started](https://github.com/minoru-jp/dirpluck/blob/main/docs/GETTING_STARTED.md): a short walkthrough from a minimal Configuration to preview and build.
- [Recipes](https://github.com/minoru-jp/dirpluck/blob/main/docs/recipes/INDEX.md): use-case guides that start from a real workspace and goal, then show the matching TOML and CLI patterns.
- [Glossary](https://github.com/minoru-jp/dirpluck/blob/main/GLOSSARY.md): meanings of the concepts used throughout the documentation.
- [Configuration Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/configuration/INDEX.md): Configuration authoring, including Scope, Always, Shared, Case, and Base Configuration.
- [CLI Guide](https://github.com/minoru-jp/dirpluck/blob/main/docs/cli/INDEX.md): Target references, CLI options, and Invocation Templates.
- [Python API](https://github.com/minoru-jp/dirpluck/blob/main/docs/python_api/INDEX.md): the small official Python API for the same execution model as the CLI.
- [Specification](https://github.com/minoru-jp/dirpluck/blob/main/docs/specification/INDEX.md): exact rules for Configuration composition, resolution, matching, filesystem traversal, Archives, Output, and validation.
- [Trust Model](https://github.com/minoru-jp/dirpluck/blob/main/docs/TRUST.md): the trust boundary for Configurations, filesystem access, and external sharing.
- [Changelog](https://github.com/minoru-jp/dirpluck/blob/main/CHANGELOG.md): release history.
- [Status](https://github.com/minoru-jp/dirpluck/blob/main/STATUS.md): current development stage, compatibility policy, and publication status.

## License

`dirpluck` is released under the MIT License.

See [LICENSE](https://github.com/minoru-jp/dirpluck/blob/main/LICENSE) for details.
