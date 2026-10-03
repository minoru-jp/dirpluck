# dirpluck development documents

`devdocs/` is the repository workspace for authoring and validating dirpluck's published documentation. The canonical sources and the realized Japanese canonical documents are public repository artifacts, but they are not part of dirpluck's runtime API, Configuration interface, or product compatibility contract.

When documentation content changes, edit the canonical source in this workspace rather than starting from the published Markdown.

## Layout

`devdocs/` has three main areas:

```text
devdocs/
├── README.md
├── canonical_sources/
├── config/
└── canonical_documents/
```

- `canonical_sources/`: Python packages containing the documentation sources of truth.
- `config/`: repository-local inputs passed to shikumi-devdoc.
- `canonical_documents/`: Japanese Markdown realized from the canonical sources.

`devdocs/README.md` is managed by the same pipeline. Its canonical source is `canonical_sources/devdocs_readme/canonical.py`.

## Canonical sources

`canonical_sources/` is a Python package organized by documentation purpose. Single documents use a `canonical.py` source, such as `canonical_sources/readme/canonical.py` for the repository README, `canonical_sources/status/canonical.py` for project status, and `canonical_sources/getting_started/canonical.py` for the first-run walkthrough. Multi-document collections place independent canonical modules directly in their subpackages: the CLI guide uses `canonical_sources/cli/`, the Configuration guide uses `canonical_sources/configuration/`, the Python API uses `canonical_sources/python_api/`, and the Specification uses `canonical_sources/specification/`.

The canonical Vocabulary is `canonical_sources/vocabulary/canonical.py`. Other canonical sources import canonical term classes from that module directly and use `merge` to bring the required concepts and spelling policy into local scope. There is no generated term-proxy module.

The repository-facing publication is the only published-document channel. There are no wheel-specific compact canonical sources or package publication channel; the same published English documents are reused as package resources in the wheel.

`canonical_sources/__init__.py` deliberately provides no aggregate API. This package is an import namespace for document realization, not an official dirpluck Python API. With the repository root on `sys.path`, canonical modules use dotted paths such as `devdocs.canonical_sources.vocabulary.canonical` and `devdocs.canonical_sources.readme.canonical`.

## Configuration

`config/context.json` and `config/notice.toml` provide repository-local input through shikumi-devdoc's existing interfaces.

- `context.json` is the JSON object passed through `--context`. The current version snapshot is refreshed from `dirpluck.__version__` with `python tools/generate_document_context.py`.
- `notice.toml` is passed through `--notice` and supplies the required `[notice].content`.

These paths and filenames are repository conventions. They do not redefine shikumi-devdoc's dotted-module, `-o`, `--context`, `--notice`, or `--translation-source` interfaces.

## Canonical documents

`canonical_documents/` contains Japanese Markdown realized from the canonical sources. Canonical sources and canonical documents are intentionally fixed to Japanese, so no language-name subdirectory is used.

Repository-facing artifacts mirror their publication paths:

```text
canonical_documents/README.md
canonical_documents/GLOSSARY.md
canonical_documents/CHANGELOG.md
canonical_documents/STATUS.md
canonical_documents/docs/GETTING_STARTED.md
canonical_documents/docs/changelog/INDEX.md
canonical_documents/docs/changelog/*.md
canonical_documents/docs/cli/INDEX.md
canonical_documents/docs/cli/*.md
canonical_documents/docs/configuration/INDEX.md
canonical_documents/docs/configuration/*.md
canonical_documents/docs/TRUST.md
canonical_documents/docs/python_api/INDEX.md
canonical_documents/docs/python_api/*.md
canonical_documents/docs/specification/INDEX.md
canonical_documents/docs/specification/*.md
canonical_documents/devdocs/README.md
```

No separate canonical artifacts are generated for the wheel. The published English Markdown used by the repository is bundled directly into the wheel, so canonical documents are kept only for the single repository publication path.

## Generation and translation

The documentation pipeline is:

```text
canonical_sources/
        ↓ shikumi-devdoc render document / glossary
canonical_documents/
        + render index for document collections
        ↓ translation / publication
public English Markdown
```

Translation metadata in the canonical documents carries policies that must survive Markdown realization, such as Vocabulary terms marked `preserve_spelling`. Published English documents omit the generation notice and translation-metadata comment.

A collection `INDEX.md` is translated from the canonical index realized from `order` and `summary`; the published index does not carry extra prose of its own. Explanatory navigation and reading guidance belong in the collection's canonical `overview.md`.

For changes to meaning, structure, or information content, edit the canonical source, regenerate the canonical document, then reflect the same content in the published English document. Do not treat a canonical document as an independently editable source.

Repository-wide generation orchestration stays in the repository-specific `tools/render_canonical_docs.py`. The set of canonical sources, publication targets, index titles, and project context are dirpluck-specific information and are not pushed into shikumi-devdoc's generic API.

```console
python tools/render_canonical_docs.py
python tools/render_canonical_docs.py --check
```

`--check` compares committed canonical documents with a temporary realization and detects drift from their sources of truth.

## Version control and distribution

Canonical sources, Japanese canonical documents, and published English documents are all committed so changes can be reviewed across the full source-to-publication path.

`devdocs/` is included in the source distribution so the documentation generation and validation inputs remain available with a release. Canonical sources and canonical documents are not included in the wheel. Instead, the wheel bundles the repository's published `README.md`, `GLOSSARY.md`, top-level `CHANGELOG.md`, `STATUS.md`, and complete `docs/` tree, including the changelog archive, under `dirpluck/_docs/`.

The source distribution contains the complete source needed to rebuild and validate the release, while repository-operation-only `.github/` content is excluded. Hatchling is the build backend, and ordinary caches, virtual environments, and build artifacts are left out according to VCS ignore rules.

The `devdocs/` directory layout and canonical implementation are repository-development surfaces, not part of dirpluck's product compatibility contract.

GitHub Actions centralizes the shared quality gate in reusable `.github/workflows/checks.yml`. Ruff formatting is enforced for `src/`, `tests/`, and `tools/` with `ruff format --check`, while `ruff check .` continues to lint the whole repository including canonical sources. Canonical sources are intentionally outside the formatter scope because they use Python syntax as a documentation DSL and raw document indentation can be meaningful. The same shared checks also run basedpyright, canonical-document drift validation, and the Python 3.11 through 3.14 `unittest` matrix; Python 3.13 additionally verifies compatibility with the legacy `python -m unittest discover -s tests` form.

Normal CI runs on pushes to `main` and pull requests targeting `main`, calls the shared checks, and uses a separate build job to build the wheel and sdist and verify distribution metadata and contents.

When a GitHub Release is published, the release workflow checks out the release tag itself and verifies that the tag matches the dynamic package version before running the same reusable checks against that tag. Only after those checks pass does it build and verify the release distributions, smoke-test the built wheel in an isolated environment, and publish that same artifact set to PyPI through Trusted Publishing.

Locally, `python tools/check_release.py` reproduces the combined quality and release checks: Ruff formatting and lint, basedpyright, both `unittest` discovery forms, canonical-document validation, wheel / sdist build, metadata and distribution-content checks, and an installed-wheel CLI smoke test.
