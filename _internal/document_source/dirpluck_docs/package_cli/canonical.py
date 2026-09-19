from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} CLI Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 CLI reference です。

```text
{{TERM_1}} [TARGET ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
{{TERM_1}} --configs
{{TERM_1}} --version
```

- Effective Configuration に Target がある場合は1個以上の positional `TARGET` を指定します。Target がない場合は指定しません。
- `project` は `cwd/project`、`work/project` は `work` location が定義されていればその location から解決します。`./work/project` は cwd 相対を明示します。
- `work/` は named location `work` 直下の directory をすべて Target として展開します。未定義 location では cwd へ fallback せず error です。
- `--config NAME` は cwd と `./dirpluck/` から Configuration filename を選びます。`.toml` は省略できます。
- `--case NAME` は named Case を1個選びます。
- `--dry-run` は archive を書き込まず ZIP contents の plan を表示します。
- `--paths` は生成される Archive README に解決済み source filesystem path を追加します。既定では path を記録しません。
- `--sequence N` は generated output name の明示的な正整数 sequence です。自動採番ではありません。
- `--configs` は cwd から検出できる Configuration を一覧表示して終了します。

```console
{{TERM_1}} projects/example --dry-run
{{TERM_1}} work/example --case audit
{{TERM_1}} work/
{{TERM_1}} --config snapshot
```

TOML の最小 reference は同梱の `CONFIGURATION.md`、trust model は同梱の `TRUST.md` を参照してください。より詳しい CLI semantics、Configuration guide、Glossary、Specification は同じ release の source distribution にある `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, `docs/SPECIFICATION.md` を参照してください。
'''
    vocabulary_refs @= (terms.TERM_1,)
