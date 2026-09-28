from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_009 = test_target_field("example 009")
example_010 = test_target_field("example 010")
example_011 = test_target_field("example 011")
example_012 = test_target_field("example 012")
example_013 = test_target_field("example 013")
example_014 = test_target_field("example 014")
example_015 = test_target_field("example 015")
example_016 = test_target_field("example 016")
example_017 = test_target_field("example 017")
example_018 = test_target_field("example 018")
example_019 = test_target_field("example 019")
example_020 = test_target_field("example 020")


@summary('Selection、Shared patterns、Case の記述方法。')


@canonical_source('Configuration selection', filename='selection.md', order=20, placeholders=False, heading="title")
class CONFIGURATION_PART:
    r"""
    この文書は、各 source から何を収集するかを定義する Selection、再利用可能な Shared patterns、Case variation を説明します。

    この guide は Selection authoring を説明し、pattern grammar と validation の厳密な契約は `../specification/selection.md`、filesystem entry の boundary は `../specification/filesystem.md` が定義します。CLI からの Target / Case 操作は `../cli/targets.md`、trust boundary は `../TRUST.md` を参照してください。
    """

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2

    class SECTION_005:
        r"""
        Directory Target の Pluck、Always source、Case はそれぞれ独立した{{TERM_7}}を持ちます。Selection では `must` / `may` / `ignore`、必要に応じて `allow_empty` を記述し、人間向けの説明を添えたい場合だけ `description` を使います。File Target は atomic source なので Selection を持ちません。

        Selection の通常の string pattern と Scope の regular-expression Target selector は、意図的に同じ pattern language にはしていません。通常の `must` / `may` string pattern は directory tree を予測可能に辿るための制限された path pattern、通常の `ignore` string は name pattern です。一方、より表現力が必要な Selection では `{ match = "..." }` inline table を使い、Selection root 配下の root-relative path 全体へ Python-compatible regular expression を適用できます。Scope の `<...>` Target selector も Python-compatible regular expression を使いますが、こちらは eligible direct-child Target の normalized name だけを絞り込む別の機能です。これらの差は意図したものです。Target selector は `../cli/targets.md` を参照してください。

        File と directory の両方になり得る include entry reference では、型を filesystem から推測しません。通常の `must` / `may` string は最終 component の末尾 `/` なしを file、末尾 `/` ありを directory とします。Intermediate component は次の階層へ進むため directory であることが構造上決まります。Structured `match` も normalized path 上で file は末尾 `/` なし、directory は末尾 `/` ありとして厳密に区別します。

        `ignore` は除外側なので意図的に広く扱います。通常の ignore string と concrete path reference は末尾 `/` がなければ matching file / directory の両方を除外し、末尾 `/` がある場合は directory だけに限定します。File だけに限定した除外が必要なら structured `match` を使います。
        """
        title @= 'Selection'

        merge @= TERMS.TERM_7

        class SECTION_006:
            r"""
            その source が抽出意図の中で果たす役割を書きます。生成される{{TERM_10}}では、この description が archive path の意味を説明するために使われます。

            ```toml
            {{example_009}}
            ```

            `description` は任意です。省略しても selection の抽出意味論は変わりません。記述する場合は空でない string とし、生成される Archive README ではその source の見出しと file 数に続く本文として使われます。複数行の説明も table cell へ圧縮せず、そのまま section body として表示します。
            """
            title @= '`description`'

            example_009 @= "description = \"Reference material used to evaluate the submission.\""

            merge @= TERMS.TERM_10

        class SECTION_007:
            r"""
            存在を要求し、存在するものを selection に含める candidate です。

            ```toml
            {{example_010}}
            ```

            Pattern が1件も一致しなければ selection は成立しません。最終 component は末尾 `/` なしなら file、末尾 `/` ありなら directory を要求します。Directory を選ぶ例は `src/` のように明示します。
            """
            title @= '`must`'

            example_010 @= "must = [\"report.pdf\", \"data/*.csv\"]"

        class SECTION_008:
            r"""
            存在する場合だけ selection に含め、不在を error にしない candidate です。

            ```toml
            {{example_011}}
            ```

            `must` と `may` は同じ selection で併用できます。最終 component の型表記は `must` と同じです。`may` が期待した型では一致せず、同じ pattern に一致する反対型の entry が存在する場合も optional missing の意味は変えません。この type mismatch は non-fatal diagnostic として source label とともに記録し、CLI は通常 build / `--preview` の両方で warning を stderr へ表示し、Python API は `RunResult.warnings` に返します。その diagnostic 自体は `may` を error に格上げしません。`must` の同じ mismatch は通常 build では従来どおり unsatisfied error ですが、`--preview` では missing 表示に加えて同じ型 marker hint を warning として確認できます。
            """
            title @= '`may`'

            example_011 @= "may = [\"generated/*.pdf\", \"coverage.xml\"]"

        class SECTION_008_1:
            r"""
            通常の string pattern より高い表現力が必要な場合は、`must` / `may` / `ignore` の entry として `{ match = "..." }` inline table を使えます。`match` の値は Python-compatible regular expression で、Selection root 配下の root-relative path **全体**へ full-match semantics で適用します。

            ```toml
            {{example_019}}
            ```

            Path separator は OS にかかわらず `/` です。Regular file は `src/main.py`、regular directory は `src/package/` のように directory だけ末尾 `/` を付けた path として照合します。そのため file / directory の違いを regular expression 側で区別でき、末尾 `/?` のような通常の regex syntax を使えば両方へ明示的に match できます。Selection root 自身は `match` 候補に含めません。

            `must` の `match` は1件以上の non-ignored selectable entry に一致する必要があり、`may` は0件一致を許容します。複数 entry に一致した場合はすべてを選びます。Directory に一致した場合は通常の directory selection と同じく、その subtree を `ignore` に従って収集します。通常 pattern と `match` が最終的に同じ file を選んでも Archive へ重複して収録しません。

            `ignore` でも同じ form を使えます。Directory path に一致した `ignore` match はその subtree を prune します。

            ```toml
            {{example_020}}
            ```

            `match` は Selection root 配下を広く走査して候補 path を照合する場合があります。通常の guided Selection pattern のように regular expression から効率的な探索経路を推論することは仕様に含めません。単純な path selection には通常の string pattern を使い、必要な場合だけ `match` を使うのが分かりやすい使い分けです。Pattern は non-empty、512 character 以下で、invalid regular expression は Configuration error です。
            """
            title @= '`{ match = "..." }`'

            example_019 @= r"""
            must = [
                "src/",
                { match = 'packages/(core|ui)/dist/.*\.whl' },
            ]
            """

            example_020 @= r"""
            ignore = [
                { match = 'build/' },
                { match = 'src/.*\.tmp' },
            ]
            """

        class SECTION_009:
            r"""
            既に `must` / `may` から選択候補になった範囲で、pluck しない entry を指定します。通常の string は従来どおり file / directory **name** を照合します。Root-relative path 全体を regular expression で除外したい場合は前節の `{ match = "..." }` form を使います。

            ```toml
            {{example_012}}
            ```

            特定の場所だけを除外したい場合は、1要素 nested array の中を `./` で始めて Selection root からの concrete relative path を指定できます。

            ```toml
            {{example_013}}
            ```

            Pluck では `./` は現在の Target root、Always source ではその Always source root を表します。Concrete path reference は末尾 `/` がなければその path にある file / directory のどちらも除外対象とし、実体が directory なら subtree も除外します。末尾 `/` がある場合は directory だけに限定します。Path reference は Selection root の内側に限定し、`..`、absolute path、glob、backslash を受理しません。

            通常の name pattern も同じ考え方で、末尾 `/` なしは matching file / directory の両方、末尾 `/` ありは directory だけを除外します。Name pattern、Shared ignore reference、path reference、structured `match` はすべて除外条件の和として扱います。同じ entry に複数の条件が一致しても error にはなりません。Directory に一致する name ignore / path reference / structured `match` は、その directory をその時点で除外し、内部を走査しません。評価順序は意味論に含めません。

            `ignore` は entry の種類による診断より優先し、一致した entry は selection 対象から外した時点で処理済みとします。そのため ignored entry は symbolic link / Windows directory junction や特殊 filesystem entry であっても、その種類を理由とする runtime diagnostic の根拠にしません。`must` が ignored entry にしか一致しない場合は通常の unsatisfied `must` として扱います。

            認識した非 ignored symbolic link / Windows directory junction は `must` / `may` の選択対象にも再帰走査の対象にもならず、Archive へも含めません。FIFO、socket、device など regular file / regular directory ではない非 ignored filesystem entry も Archive 対象にしません。`must` がそのような特殊 entry だけに一致した場合は selectable でない理由を示す error とし、`may` では optional missing として扱います。Selection には内容や名前に基づく暗黙の ignore を加えません。Configuration を実行するときの trust boundary と広い selection の扱いは `../TRUST.md` を参照してください。
            """
            title @= '`ignore`'

            example_012 @= """
            ignore = [
                ".git/",
                ".venv/",
                "__pycache__/",
                ".env*",
                "*.pem",
                "*.key",
                "*.pyc",
            ]
            """

            example_013 @= """
            ignore = [
                ["./tests/fixtures/big.bin"],
                ["./src/generated/"],
            ]
            """

        class SECTION_010:
            r"""
            `may` だけの selection で、最終的に0 file でも正常としたい場合に使います。

            ```toml
            {{example_014}}
            ```

            既定は `false` です。`allow_empty = true` と `must` は同時に使えません。
            """
            title @= '`allow_empty`'

            example_014 @= """
            may = ["generated/*.pdf"]
            allow_empty = true
            """

    class SECTION_011:
        r"""
        同じ pattern set を複数 selection で使う場合は{{TERM_12}}として名前を付けます。Selection と同じ `must` / `may` / `ignore` の3 namespace を使います。

        ```toml
        {{example_015}}
        ```

        Selection array の通常の string は direct pattern、`{ match = "..." }` は direct structured match です。`must` / `may` の1要素 nested array は Shared reference、`ignore` の1要素 nested arrayは plain name なら Shared reference、`./` で始まる string なら Selection-relative path reference として解釈します。Shared pattern set 自身にも direct string と `{ match = "..." }` を記述できますが、Shared reference や path reference を入れ子にはできません。

        ```toml
        {{example_016}}
        ```

        参照先 namespace は、その reference を書いた field から決まります。`must = [["project"]]` は `shared.must.project`、`may` は `shared.may`、`ignore = [["python-noise"]]` は `shared.ignore.python-noise` を参照します。`ignore = [["./tests/fixtures/"]]` のように `./` で始めた場合だけ Shared namespace ではなく Selection-relative path を表します。

        `[]`、`["a", "b"]`、`[123]` のような nested array は reference として無効です。`must` / `may` では nested array は Shared reference 専用です。`ignore` では `./` を path reference marker に予約しますが、通常の direct string pattern と structured `match` の表現は変えません。

        Base chain での name resolution と duplicate validation は `../specification/INDEX.md` を参照してください。
        """
        title @= 'Shared patterns'

        example_015 @= """
        [shared.must]
        project = ["src/", "pyproject.toml"]

        [shared.may]
        docs = ["README.md", "docs/"]

        [shared.ignore]
        python-noise = ["__pycache__/", "*.pyc"]
        """

        example_016 @= """
        [pluck]
        description = "The current project."
        must = [
            "LICENSE",
            ["project"],
        ]
        may = [
            ["docs"],
        ]
        ignore = [
            ".git/",
            ["python-noise"],
        ]
        """

        merge @= TERMS.TERM_12

    class SECTION_012:
        r"""
        {{TERM_4}}は、同じ source に別の完全な selection を用意するときに使います。

        ```toml
        {{example_017}}
        ```

        ```console
        {{example_018}}
        ```

        Case は base selection への差分ではありません。必要な `must` / `may` / `ignore` / Shared reference / `allow_empty` は Case 自身へ書きます。

        Pluck と Always source が同じ Case 名を持てば、同じ CLI `--case` で対応する variation を選べます。Always source に同名 Case がない場合の fallback など、正確な Case semantics は `../specification/INDEX.md` を参照してください。
        """
        title @= 'Cases'

        example_017 @= """
        [pluck]
        description = "Normal review."
        must = ["documents/", "metadata.json"]

        [pluck.case.audit]
        description = "Audit review."
        must = ["documents/", "metadata.json", "records/"]
        """

        example_018 @= "dirpluck ./acme/ --case audit"

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_4
