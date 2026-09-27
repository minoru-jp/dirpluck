<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/devdocs_readme/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/canonical_documents/` にある日本語 canonical document はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの canonical document を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や canonical document を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck development documents

`devdocs/` は、dirpluck の公開文書を作成・検証するための repository workspace です。ここにある canonical source と日本語 canonical document は repository 上で公開しますが、dirpluck の runtime API、Configuration interface、または互換性保証対象の product interface ではありません。

文書内容を変更するときは公開 Markdown を起点にせず、この workspace の canonical source へ戻ります。

## 構成

`devdocs/` は次の3領域を持ちます。

```text
devdocs/
├── README.md
├── canonical_sources/
├── config/
└── canonical_documents/
```

- `canonical_sources/`: 文書正本を格納する Python package。
- `config/`: shikumi-devdoc へ渡す repository-local input。
- `canonical_documents/`: 正本から実現した日本語 Markdown。

`devdocs/README.md` 自身も例外ではなく、`canonical_sources/devdocs_readme/canonical.py` を正本として同じ pipeline で管理します。

## Canonical sources

`canonical_sources/` 自体を Python package とし、文書目的ごとに sub-package を分けます。単一文書は `canonical.py` を正本とし、README は `canonical_sources/readme/canonical.py`、project status は `canonical_sources/status/canonical.py`、最初の実行手順は `canonical_sources/getting_started/canonical.py` に置きます。複数文書の collection は sub-package 直下に独立した canonical module を並べ、CLI guide は `canonical_sources/cli/`、Configuration guide は `canonical_sources/configuration/`、Python API は `canonical_sources/python_api/`、Specification は `canonical_sources/specification/` を使います。

Vocabulary の正本は `canonical_sources/vocabulary/canonical.py` です。各 canonical source は Vocabulary の canonical term class を直接 import し、`merge` で必要な概念と表記 policy を参照します。生成 proxy module は使用しません。

公開文書は repository-facing publication を唯一の文書系統とします。Wheel 専用の compact canonical source や package publication channel は持たず、同じ公開英語文書を wheel の package resource として再利用します。

`canonical_sources/__init__.py` は aggregate API を提供しません。この package は document realization の import namespace であり、dirpluck 本体の公式 Python API ではありません。

Repository root を Python import root とし、module 名は `devdocs.canonical_sources.vocabulary.canonical` や `devdocs.canonical_sources.readme.canonical` の形で扱います。

## Configuration

`config/context.json` と `config/notice.toml` は、Dirpluck repository が shikumi-devdoc の既存 interface へ入力を渡すための configuration です。

- `context.json` は render 時の `--context` に渡す JSON object の snapshot です。現在の version は `python tools/generate_document_context.py` で `dirpluck.__version__` から更新します。
- `notice.toml` は `--notice` に渡し、shikumi-devdoc が要求する `[notice].content` を保持します。

これらの配置や filename は repository convention です。shikumi-devdoc 側の dotted canonical module、`-o`、`--context`、`--notice`、`--translation-source` という interface 自体は、この workspace の都合で再定義しません。

## Canonical documents

`canonical_documents/` は canonical source から shikumi-devdoc で実現した日本語 Markdown を格納します。canonical source と canonical document の言語は日本語で固定しているため、言語名の sub-directory は設けません。

Repository に公開する文書は publication path を mirror します。

```text
canonical_documents/README.md
canonical_documents/GLOSSARY.md
canonical_documents/CHANGELOG.md
canonical_documents/STATUS.md
canonical_documents/docs/GETTING_STARTED.md
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

Wheel 用に別の canonical artifact は生成しません。Repository へ公開する英語 Markdown がそのまま wheel に同梱されるため、canonical document も repository publication path に対応する1系統だけを保持します。

## 生成と翻訳

文書 pipeline は次の順序です。

```text
canonical_sources/
        ↓ shikumi-devdoc render document / glossary
canonical_documents/
        + render index for document collections
        ↓ translation / publication
public English Markdown
```

canonical document の translation metadata は、Vocabulary の `preserve_spelling` など Markdown realization 後にも維持すべき policy を翻訳境界へ渡します。公開英語文書にはこの metadata comment と生成 notice を含めません。

Collection の `INDEX.md` は `order` / `summary` から実現した canonical index 自体を翻訳し、公開版だけに追加 prose を持たせません。説明的な導線や読み分けは各 collection の `overview.md` canonical source に置きます。

意味、構造、情報量を変更する場合は canonical source を編集し、canonical document を再生成してから公開英語文書へ反映します。canonical document を正本として直接編集しません。

Dirpluck repository 全体の generation orchestration は repository 固有の `tools/render_canonical_docs.py` に置きます。対象 canonical source、publication target、index title、context などは Dirpluck 固有情報なので shikumi-devdoc の汎用 API へ持ち込みません。

```console
python tools/render_canonical_docs.py
python tools/render_canonical_docs.py --check
```

`--check` は commit 済み canonical document を一時生成結果と比較し、正本との drift を検出します。

## Version control と distribution

Canonical sources、日本語 canonical documents、公開英語文書はいずれも version control へ commit し、正本から公開物までの差分を review できる状態にします。

`devdocs/` は source distribution に含め、release の文書生成・検証に利用できるようにします。一方、wheel には canonical source / canonical document は含めません。Wheel には repository の公開 `README.md`、`GLOSSARY.md`、`CHANGELOG.md`、`STATUS.md`、`docs/` 全体を `dirpluck/_docs/` 以下へ同梱します。

Source distribution は release の再構築・検証に必要な source 全体を含め、repository operation 専用の `.github/` は除外します。Build backend は Hatchling を使用し、通常の cache、virtual environment、build artifact などは VCS ignore rules に従って配布対象から除外します。

`devdocs/` の directory layout や canonical implementation は repository development surface であり、dirpluck の product compatibility contract ではありません。

GitHub 公開前は hosted CI / release workflow を置かず、release 前の test、canonical document check、wheel / sdist build、metadata / distribution contents、installed wheel の CLI smoke test は `python tools/check_release.py` で local に確認します。GitHub 公開後は公開環境に合わせて CI / release workflow を新たに構成します。
