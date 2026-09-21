from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} development documents")
class TITLE_1:
    r'''`devdocs/` は、{{TERM_1}} の公開文書を作成・検証するための repository workspace です。ここにある正本と日本語中間文書は repository 上で公開しますが、{{TERM_1}} の runtime API、Configuration interface、または互換性保証対象の product interface ではありません。

文書内容を変更するときは公開 Markdown を起点にせず、この workspace の canonical source へ戻ります。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("構成")
    class TITLE_2:
        r'''`devdocs/` は次の3領域を持ちます。

```text
devdocs/
├── README.md
├── canonical_documents/
├── config/
└── intermediate_documents/
```

- `canonical_documents/`: 文書正本を格納する Python package。
- `config/`: shikumi-devdoc へ渡す repository-local input。
- `intermediate_documents/`: 正本から実現した日本語 Markdown。

`devdocs/README.md` 自身も例外ではなく、`canonical_documents/devdocs_readme/canonical.py` を正本として同じ pipeline で管理します。'''

    @title("Canonical documents")
    class TITLE_3:
        r'''`canonical_documents/` 自体を Python package とし、文書目的ごとの sub-package に `canonical.py` を置きます。たとえば README の正本は `canonical_documents/readme/canonical.py`、Configuration guide の正本は `canonical_documents/configuration/canonical.py` です。

Vocabulary の正本は `canonical_documents/vocabulary/canonical.py` です。shikumi-devdoc の `terms` realization で生成する `canonical_documents/terms.py` を各 canonical document から共有し、Vocabulary で定義した概念と表記 policy を参照します。

`canonical_documents/__init__.py` は aggregate API を提供しません。この package は document realization の import namespace であり、{{TERM_1}} 本体の公式 Python API ではありません。

shikumi-devdoc から canonical module を import するときは `devdocs/` を Python import root に置きます。したがって module 名は `canonical_documents.vocabulary.canonical` や `canonical_documents.readme.canonical` の形になります。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Configuration")
    class TITLE_4:
        r'''`config/context.json` と `config/notice.toml` は、Dirpluck repository が shikumi-devdoc の既存 interface へ入力を渡すための configuration です。

- `context.json` は render 時の `--context` に渡す JSON object の snapshot です。現在の version は `python tools/generate_document_context.py` で `dirpluck.__version__` から更新します。
- `notice.toml` は `--notice` に渡し、shikumi-devdoc が要求する `[notice].content` を保持します。

これらの配置や filename は repository convention です。shikumi-devdoc 側の dotted canonical module、`-o`、`--context`、`--notice`、`--translation-source` という interface 自体は、この workspace の都合で再定義しません。'''

    @title("Intermediate documents")
    class TITLE_5:
        r'''`intermediate_documents/` は canonical source から shikumi-devdoc で実現した日本語 Markdown を格納します。正本と中間文書の言語は日本語で固定しているため、言語名の sub-directory は設けません。

Repository に公開する文書は publication path を mirror します。

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

Python distribution に同梱する文書は物理的な `src/dirpluck/docs/` path を mirror せず、publication channel を表す `package/` の下へ置きます。

```text
intermediate_documents/package/CLI.md
intermediate_documents/package/CONFIGURATION.md
intermediate_documents/package/PYTHON_API.md
```

同じ canonical source から repository-facing と package-facing の両方へ出力する場合も、各 publication target に対応する intermediate artifact を独立して生成します。'''

    @title("生成と翻訳")
    class TITLE_6:
        r'''文書 pipeline は次の順序です。

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

中間文書の translation metadata は、Vocabulary の `preserve_spelling` など Markdown realization 後にも維持すべき policy を翻訳境界へ渡します。公開英語文書にはこの metadata comment と生成 notice を含めません。

意味、構造、情報量を変更する場合は canonical source を編集し、中間文書を再生成してから公開英語文書へ反映します。中間文書を正本として直接編集しません。'''

    @title("Version control と distribution")
    class TITLE_7:
        r'''Canonical documents、日本語 intermediate documents、公開英語文書はいずれも version control へ commit し、正本から公開物までの差分を review できる状態にします。

`devdocs/` は source distribution に含め、release の文書生成・検証に利用できるようにします。一方、wheel には含めません。Wheel 利用時に必要な reference は `dirpluck/docs/` に同梱する公開英語文書です。

`devdocs/` の directory layout や canonical implementation は repository development surface であり、{{TERM_1}} の product compatibility contract ではありません。'''
        vocabulary_refs @= (terms.TERM_1,)
