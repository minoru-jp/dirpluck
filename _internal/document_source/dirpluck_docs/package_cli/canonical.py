from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} CLI Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 CLI reference です。

```text
{{TERM_1}} [DIRECTORY ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run]
{{TERM_1}} --configs
{{TERM_1}} --version
```

- Effective Configuration に Target がある場合は1個以上の `DIRECTORY` を指定します。Target がない場合は指定しません。
- `--config NAME` は cwd と `./dirpluck/` から Configuration filename を選びます。`.toml` は省略できます。
- `--case NAME` は named Case を1個選びます。
- `--dry-run` は archive を書き込まず ZIP contents の plan を表示します。
- `--sequence N` は generated output name の明示的な正整数 sequence です。自動採番ではありません。
- `--configs` は cwd から検出できる Configuration を一覧表示して終了します。

```console
{{TERM_1}} projects/example --dry-run
{{TERM_1}} projects/example --case audit
{{TERM_1}} --config snapshot
```

TOML の最小 reference は同梱の `CONFIGURATION.md` を参照してください。より詳しい CLI semantics、Configuration guide、Glossary、Specification は同じ release の source distribution にある `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, `docs/SPECIFICATION.md` を参照してください。
'''
    vocabulary_refs @= (terms.TERM_1,)
