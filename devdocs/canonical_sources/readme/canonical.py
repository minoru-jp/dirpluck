from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge
from shikumi_devdoc.norms.document import title


@canonical_source('dirpluck', filename='README.md', merge_policy="all", heading="title")
class SECTION_001:
    r"""
    {{TERM_1}} は、「どの file を一緒に扱うか」という判断を TOML に残し、その宣言から ZIP Archive を組み立てる tool です。CLI を主な入口とし、同じ invocation model を最小の Python API からも利用できます。

    Backup のように周辺をすべて複製するのではなく、review、引き渡し、調査、定例作業、LLM と扱う作業 context など、ある目的に必要な file だけを繰り返し集めることを目的としています。
    """

    merge @= TERMS.TERM_1

    class SECTION_002:
        """"""
        title @= '何に使うか'

        class SECTION_003:
            r"""
            複数の directory に分かれた資料でも、同じ目的で使うものならひとつの Archive にまとめられます。

            たとえば review 用に、

            - 対象 project の source
            - review guideline
            - reference material

            を一緒に集める、といった用途です。

            固定資料だけを集めることも、実行時に選んだ {{TERM_3}} へ固定資料を添えることもできます。
            """
            title @= '必要な資料をひとつにまとめる'

            merge @= TERMS.TERM_3

        class SECTION_004:
            r"""
            「README と `src/` と `tests/` を集める」「秘密情報や生成物は除外する」といった判断を {{TERM_2}} に残しておけば、対象となる project を変えながら同じルールを使えます。

            {{TERM_3}} をどこから選ぶかは {{TERM_16}} として分けられるため、Configuration の置き場所と実際の project tree を同じ場所に揃える必要はありません。

            File / directory の両方になり得る **include / Target reference** は、記法だけで型を明示します。末尾 `/` なしは file、末尾 `/` ありは directory で、filesystem の現在状態から型を推測しません。たとえば Selection の `"pyproject.toml"` は file、`"src/"` は directory を表します。Target reference も同じ原則を使い、default Scope の directory Target は `./project/`、named Scope では `work/project/` のように書きます。`may` が期待型では一致せず反対型の entry が存在する場合も optional semantics は変えず、source label 付きの diagnostic で末尾 `/` の見直しを案内します。CLI は通常 build / `--preview` の両方で warning を表示し、Python API は `RunResult.warnings` に返します。`must` は通常 build の既存 error に同じ型 marker hint を含め、preview では missing のまま同じ hint を warning として確認できます。Literal Target の error も型 marker hint を含めます。

            `ignore` は除外側の規則として意図的に広く扱います。通常の ignore string / concrete path は末尾 `/` がなければ matching file と directory の両方を除外し、末尾 `/` がある場合だけ directory に限定します。File だけを精密に除外したい場合は structured `{ match = "..." }` を使えます。

            Directory Target の通常の `must` / `may` / `ignore` string は、directory tree を予測可能に扱うための制限された Selection pattern を使います。より表現力が必要な Selection では `{ match = "..." }` で root-relative path 全体へ Python-compatible regular expression を使えます。Scope の `<...>` Target selector も regular expression を使いますが、こちらは eligible direct-child Target の normalized name の絞り込みだけを行います。この使い分けは意図したものです。詳細は `docs/configuration/selection.md` と `docs/cli/targets.md` を参照してください。
            """
            title @= '同じ抽出方法を、別の Target に使う'

            merge @= TERMS.TERM_2
            merge @= TERMS.TERM_3
            merge @= TERMS.TERM_16

    class SECTION_005:
        r"""
        一度だけなら、手作業で ZIP を作る方が簡単です。

        {{TERM_1}} が役立つのは、同じ種類の判断を後でもう一度行うときです。

        Configuration に残しておけば、

        - 何を必ず含めるか
        - 何を存在するときだけ含めるか
        - 何を除外するか
        - どの固定資料を一緒に集めるか

        を、shell history、会話履歴、人間の記憶へ依存せず確認できます。

        `--preview` を使えば、Archive を書き込む前に、現在の filesystem に対して何が選ばれるかを確認できます。

        Configuration を複数の用途で共有したい場合は、別の Configuration を基礎として再利用することもできます。Configuration の構成方法については `docs/configuration/INDEX.md`、厳密な合成・解決規則については `docs/specification/INDEX.md` を参照してください。
        """
        title @= 'なぜ宣言として残すのか'

        merge @= TERMS.TERM_1

    class SECTION_006:
        r"""
        {{TERM_1}} は、どの file が機密情報かを推論しません。

        外部へ渡す Archive を作る場合は、`--preview` で内容を確認し、含めるべきでないものを Configuration で明示的に除外してください。

        たとえば `.env`、秘密鍵、credential、project 固有の機密 file などは、名前や配置が project ごとに異なります。

        Configuration と filesystem 操作の trust boundary、absolute path、overwrite、外部へ渡す Archive を扱う際の考え方は `docs/TRUST.md` にまとめています。
        """
        title @= '外へ渡す前に'

        merge @= TERMS.TERM_1

    class SECTION_011:
        r"""
        最初の Configuration を作り、`--preview` で確認してから Archive を生成する流れは `docs/GETTING_STARTED.md` にまとめています。

        Configuration field の詳細は `docs/configuration/INDEX.md`、CLI option と Invocation Template は `docs/cli/INDEX.md` を参照してください。
        """
        title @= 'まず試す'


    class SECTION_008:
        r"""
        現在の version は **{{version}}** です。

        Python 3.11 以降を使用します。

        ```console
        pip install {{TERM_1}}
        {{TERM_1}} --version
        ```

        {{TERM_1}} には runtime third-party dependency はありません。
        """
        title @= 'インストール'

        merge @= TERMS.TERM_1

    class SECTION_009:
        r"""
        文書は目的ごとに分けています。

        - `docs/GETTING_STARTED.md`: 最初の Configuration から preview / build までを通して試す guide。
        - `GLOSSARY.md`: 文書全体で使う概念の意味。
        - `docs/configuration/INDEX.md`: `.dirpluck` Configuration を書くための guide。
        - `docs/cli/INDEX.md`: CLI の使い方と `.dirpluck-inv` Invocation Template の guide。
        - `docs/python_api/INDEX.md`: CLI と同じ実行 model を Python から使う最小の公式 API。
        - `docs/specification/INDEX.md`: Configuration composition、resolution、matching、filesystem traversal、Archive、Output、validation の厳密な規則。
        - `docs/TRUST.md`: Configuration と filesystem 操作の trust boundary、および利用者が確認すべき範囲。
        - `CHANGELOG.md`: release history。
        - `STATUS.md`: 現在の開発段階、互換性方針、公開形態。
        """
        title @= '文書'


    class SECTION_010:
        r"""
        {{TERM_1}} は MIT License のもとで公開されています。

        詳細は `LICENSE` を参照してください。
        """
        title @= 'ライセンス'

        merge @= TERMS.TERM_1
