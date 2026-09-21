# dirpluck development documents

`devdocs/` is the repository workspace used to create and verify dirpluck's public documentation. The canonical sources and Japanese intermediate documents stored here are public repository content, but they are not part of dirpluck's runtime API, Configuration interface, or product compatibility contract.

When documentation content changes, start from the canonical source in this workspace rather than editing published Markdown as the source of truth.

## Structure

`devdocs/` has three main areas.

```text
devdocs/
├── README.md
├── canonical_documents/
├── config/
└── intermediate_documents/
```

- `canonical_documents/`: the Python package containing canonical document sources.
- `config/`: repository-local inputs passed to shikumi-devdoc.
- `intermediate_documents/`: Japanese Markdown realized from the canonical sources.

`devdocs/README.md` is not an exception. Its canonical source is `canonical_documents/devdocs_readme/canonical.py`, and it follows the same pipeline as the other documents.

## Canonical documents

`canonical_documents/` is itself a Python package. Each document purpose has a subpackage containing `canonical.py`. For example, the canonical README source is `canonical_documents/readme/canonical.py`, and the canonical Configuration guide is `canonical_documents/configuration/canonical.py`.

The canonical Vocabulary is `canonical_documents/vocabulary/canonical.py`. The `canonical_documents/terms.py` module is generated from it by the shikumi-devdoc `terms` realization and is shared by the other canonical documents so they can reference the concepts and spelling policy defined by the Vocabulary.

`canonical_documents/__init__.py` does not provide an aggregate API. This package is an import namespace for document realization, not part of dirpluck's official Python API.

When shikumi-devdoc imports canonical modules, `devdocs/` is placed on the Python import path. Canonical module names therefore take forms such as `canonical_documents.vocabulary.canonical` and `canonical_documents.readme.canonical`.

## Configuration

`config/context.json` and `config/notice.toml` are repository-side inputs used with the existing shikumi-devdoc interface.

- `context.json` is the JSON object snapshot passed through `--context` during rendering. Refresh the current version from `dirpluck.__version__` with `python tools/generate_document_context.py`.
- `notice.toml` is passed through `--notice` and contains the `[notice].content` required by shikumi-devdoc.

Their locations and filenames are repository conventions. This workspace does not redefine shikumi-devdoc's interface for dotted canonical modules, `-o`, `--context`, `--notice`, or `--translation-source`.

## Intermediate documents

`intermediate_documents/` contains Japanese Markdown realized from the canonical sources with shikumi-devdoc. The canonical sources and intermediate documents are fixed to Japanese, so there is no language-name subdirectory.

Repository-facing documents mirror their publication paths.

```text
intermediate_documents/README.md
intermediate_documents/GLOSSARY.md
intermediate_documents/CHANGELOG.md
intermediate_documents/docs/CLI.md
intermediate_documents/docs/CONFIGURATION.md
intermediate_documents/docs/PYTHON_API.md
intermediate_documents/docs/SPECIFICATION.md
intermediate_documents/docs/TRUST.md
intermediate_documents/devdocs/README.md
```

Documents bundled in the Python distribution do not mirror the physical `src/dirpluck/docs/` path. They live under `package/`, which represents the publication channel.

```text
intermediate_documents/package/CLI.md
intermediate_documents/package/CONFIGURATION.md
intermediate_documents/package/PYTHON_API.md
```

When one canonical source produces both a repository-facing and package-facing document, each publication target still has its own intermediate artifact.

## Generation and translation

The documentation pipeline is:

```text
canonical_documents/vocabulary/canonical.py
        ↓ shikumi-devdoc terms
canonical_documents/terms.py
        ↓
canonical_documents/*/canonical.py
        ↓ shikumi-devdoc render --translation-source
intermediate Japanese Markdown under intermediate_documents/
        ↓ translation
public English Markdown
```

Translation metadata in the intermediate documents carries policies that must survive Markdown realization, such as Vocabulary `preserve_spelling` rules, across the translation boundary. Published English documents omit both that metadata comment and the generated notice.

To change meaning, structure, or information content, edit the canonical source, regenerate the intermediate document, and then update the published English document. Do not treat the intermediate document itself as the source of truth.

## Version control and distribution

Canonical documents, Japanese intermediate documents, and published English documents are all committed to version control so changes can be reviewed from source of truth through publication.

`devdocs/` is included in the source distribution so a release can be used to regenerate and verify its documentation. It is excluded from wheels. Runtime references needed by wheel users are the published English documents bundled under `dirpluck/docs/`.

The `devdocs/` directory layout and canonical implementation are a repository development surface, not part of dirpluck's product compatibility contract.
