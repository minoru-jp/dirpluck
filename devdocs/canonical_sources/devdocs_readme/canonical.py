from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge
from shikumi_devdoc.norms.document import title


@canonical_source(
    "dirpluck development documents", filename="README.md", merge_policy="local", heading="title"
)
class SECTION_001:
    r"""
    `devdocs/` は、{{TERM_1}} の公開文書を作成・検証するための repository workspace です。ここにある canonical source と日本語 canonical document は repository 上で公開しますが、{{TERM_1}} の runtime API、Configuration interface、または互換性保証対象の product interface ではありません。

    文書内容を変更するときは公開 Markdown を起点にせず、この workspace の canonical source へ戻ります。
    """

    merge @= TERMS.TERM_1

    class SECTION_002:
        r"""
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
        """

        title @= "構成"

    class SECTION_003:
        r"""
        `canonical_sources/` 自体を Python package とし、文書目的ごとに sub-package を分けます。単一文書は `canonical.py` を正本とし、README は `canonical_sources/readme/canonical.py`、project status は `canonical_sources/status/canonical.py`、最初の実行手順は `canonical_sources/getting_started/canonical.py` に置きます。複数文書の collection は sub-package 直下に独立した canonical module を並べ、CLI guide は `canonical_sources/cli/`、Configuration guide は `canonical_sources/configuration/`、Python API は `canonical_sources/python_api/`、Specification は `canonical_sources/specification/` を使います。

        Vocabulary の正本は `canonical_sources/vocabulary/canonical.py` です。各 canonical source は Vocabulary の canonical term class を直接 import し、`merge` で必要な概念と表記 policy を参照します。生成 proxy module は使用しません。

        公開文書は repository-facing publication を唯一の文書系統とします。Wheel 専用の compact canonical source や package publication channel は持たず、同じ公開英語文書を wheel の package resource として再利用します。

        `canonical_sources/__init__.py` は aggregate API を提供しません。この package は document realization の import namespace であり、{{TERM_1}} 本体の公式 Python API ではありません。

        Repository root を Python import root とし、module 名は `devdocs.canonical_sources.vocabulary.canonical` や `devdocs.canonical_sources.readme.canonical` の形で扱います。
        """

        title @= "Canonical sources"

        merge @= TERMS.TERM_1

    class SECTION_004:
        r"""
        `config/context.json` と `config/notice.toml` は、Dirpluck repository が shikumi-devdoc の既存 interface へ入力を渡すための configuration です。

        - `context.json` は render 時の `--context` に渡す JSON object の snapshot です。現在の version は `python tools/generate_document_context.py` で `dirpluck.__version__` から更新します。
        - `notice.toml` は `--notice` に渡し、shikumi-devdoc が要求する `[notice].content` を保持します。

        これらの配置や filename は repository convention です。shikumi-devdoc 側の dotted canonical module、`-o`、`--context`、`--notice`、`--translation-source` という interface 自体は、この workspace の都合で再定義しません。
        """

        title @= "Configuration"

    class SECTION_005:
        r"""
        `canonical_documents/` は canonical source から shikumi-devdoc で実現した日本語 Markdown を格納します。canonical source と canonical document の言語は日本語で固定しているため、言語名の sub-directory は設けません。

        Repository に公開する文書は publication path を mirror します。

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

        Wheel 用に別の canonical artifact は生成しません。Repository へ公開する英語 Markdown がそのまま wheel に同梱されるため、canonical document も repository publication path に対応する1系統だけを保持します。
        """

        title @= "Canonical documents"

    class SECTION_006:
        r"""
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

        意味、構造、情報量を変更する場合は canonical source を編集し、canonical document を再生成してから、その canonical document を翻訳元として同じ relative path の公開英語文書へ反映します。canonical document や公開英語文書を変更の正本として直接編集しません。

        Dirpluck repository 全体の generation orchestration は repository 固有の `tools/render_canonical_docs.py` に置きます。対象 canonical source、publication target、index title、context などは Dirpluck 固有情報なので shikumi-devdoc の汎用 API へ持ち込みません。

        ```console
        python tools/render_canonical_docs.py
        python tools/render_canonical_docs.py --check
        python tools/check_published_docs.py --update
        python tools/check_published_docs.py
        ```

        `render_canonical_docs.py --check` は commit 済み canonical document を一時生成結果と比較し、正本との drift を検出します。公開英語文書へ翻訳・配備した後は `check_published_docs.py --update` で canonical document と公開文書の hash pair を `devdocs/config/publication_manifest.json` に記録します。通常の `check_published_docs.py` は canonical document または公開文書がその reviewed snapshot から変化していないこと、root README / CHANGELOG が現在の release version を公開していることを検証します。Manifest の更新は翻訳・review の代替ではなく、その工程が完了した snapshot を release gate へ渡すための記録です。
        """

        title @= "生成と翻訳"

    class SECTION_007:
        r"""
        Canonical sources、日本語 canonical documents、公開英語文書、および `devdocs/config/publication_manifest.json` はいずれも version control へ commit し、正本から公開物までの差分と、review 済み publication snapshot を確認できる状態にします。

        `devdocs/` は source distribution に含め、release の文書生成・検証に利用できるようにします。一方、wheel には canonical source / canonical document は含めません。Wheel には repository の公開 `README.md`、`GLOSSARY.md`、トップレベルの `CHANGELOG.md`、`STATUS.md`、CHANGELOG archive を含む `docs/` 全体を `dirpluck/_docs/` 以下へ同梱します。

        Source distribution は release の再構築・検証に必要な source 全体を含め、repository operation 専用の `.github/` は除外します。Build backend は Hatchling を使用し、通常の cache、virtual environment、build artifact などは VCS ignore rules に従って配布対象から除外します。

        `devdocs/` の directory layout や canonical implementation は repository development surface であり、{{TERM_1}} の product compatibility contract ではありません。

        GitHub Actions の共通品質 gate は reusable `.github/workflows/checks.yml` に集約します。Ruff formatter は `src/`、`tests/`、`tools/` を対象に `ruff format --check` で検証し、canonical source を含む repository 全体には `ruff check .` を適用します。Canonical source は Python syntax を使う文書 DSL で raw document content の indentation も意味を持つため formatter 対象には含めません。あわせて basedpyright、canonical document drift check、Python 3.11 から 3.14 の `unittest` matrix を実行し、Python 3.13 では従来の `python -m unittest discover -s tests` 形式も互換確認します。

        通常 CI は `main` への push と `main` を対象とする pull request で共通 checks を呼び出し、canonical document drift に加えて reviewed published-document snapshot も検証します。別の build job で wheel / sdist を構築して distribution metadata と contents を検証します。

        GitHub Release の `published` event では release tag 自体を checkout し、tag と dynamic package version の一致を先に確認します。その後、同じ reusable checks を release tag に対して実行し、成功した場合だけ release distribution を build・検証します。Built wheel の isolated install smoke test を通した同一 artifact を PyPI Trusted Publishing で公開します。

        Release 前には canonical source の変更を `python tools/render_canonical_docs.py` で実現し、その日本語 canonical document を翻訳元として対応する公開英語文書へ配備し、`python tools/check_published_docs.py --update` で reviewed snapshot を更新します。Local では `python tools/check_release.py` により、Ruff format / lint、basedpyright、両方の `unittest` discovery 形式、canonical document drift、published-document snapshot、wheel / sdist build、metadata / distribution contents、installed wheel の CLI smoke testをまとめて再現できます。Canonical source だけを更新して公開英語文書が旧 release のまま残る状態は release gate を通しません。
        """

        title @= "Version control と distribution"

        merge @= TERMS.TERM_1
