from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_003 = test_target_field("example 003")
example_004 = test_target_field("example 004")
example_005 = test_target_field("example 005")
example_006 = test_target_field("example 006")
example_007 = test_target_field("example 007")
example_008 = test_target_field("example 008")


@summary('Pluck、Scope、Namespace、Always source の定義と配置。')


@canonical_source('Configuration sources', filename='sources.md', order=10, merge_policy="local", heading="title")
class CONFIGURATION_PART:
    r"""
    この文書は、Target を選ぶ Pluck / Scope と、固定 source を追加する Always、および Archive 上の Namespace を説明します。

    この guide は source authoring を説明し、互換性上の厳密な契約は Specification が定義します。Target / Scope / Always / Case の解決は `../specification/runtime-targets.md`、Namespace は `../specification/namespace.md`、source traversal boundary は `../specification/filesystem.md` を参照してください。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。
    """

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2

    class SECTION_003:
        r"""
        `[pluck]` は、今回の実行で選ばれた **directory** {{TERM_3}}から何を取り出すかを定義します。Source path 自体は持たず、Target は{{TERM_16}}と CLI Target reference から解決します。`target_kind = "file"` または `"both"` の Scope から得た file Target は atomic source であり、Pluck は適用しません。

        ```toml
        {{example_003}}
        ```

        同じ実行で複数 directory Target を選んだ場合も、各 directory Target へ同じ pluck selection を独立して適用します。File Target と directory Target は同じ実行で併用できます。Pluck がない Configuration でも `target_kind = "file"` または `"both"` の Scope から file Target は positional Target reference で選択できますが、directory Target は選択できません。
        """
        title @= 'Pluck'

        example_003 @= """
        [pluck]
        description = "The submission currently being reviewed."
        must = ["documents/", "metadata.json"]
        may = ["attachments/"]
        ignore = [".git/", "__pycache__/", "*.pyc"]
        """

        merge @= TERMS.TERM_3
        merge @= TERMS.TERM_16

    class SECTION_030:
        r"""
        {{TERM_16}}は Target を探す場所です。常設の default Scope と、必要に応じて追加する名前付き Scope を使えます。

        Default Scope は常に存在し、{{TERM_14}}がある directory を探索 root とします。`[scope]` table は default Scope の optional `description` / `target_kind` / `ignore` / `namespace` を設定するために使い、`path` は書きません。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` です。`[scope]` を省略した場合、または空の `[scope]` を書いた場合は directory Target、description なし、`ignore = []`、Namespace なしという従来動作になります。Base Configuration に書いた `[scope]` は、その Configuration 自身を Root として使う場合だけ有効で、outer Root の default Scope へ継承されません。

        ```toml
        {{example_004}}
        ```

        名前付き Scope は `path` を持ちます。

        ```toml
        {{example_005}}
        ```

        `target_kind = "directory"` の Scope は直下の eligible directory だけ、`target_kind = "file"` は直下の eligible regular file だけ、`target_kind = "both"` はその両方を Target candidate とします。`target_kind` は Scope 直下の entry に対する type filter として働きます。Scope `ignore` は除外側の規則として広く扱い、末尾 `/` なしは matching file / directory Target candidate の両方、末尾 `/` ありは directory candidate だけを除外します。File selection の `pluck.ignore` とは役割が違います。`description` はその Scope から得た Target の Archive README context として使います。

        CLI Target reference は、single Target と全展開に加え、すべての `target_kind` で使える Target selector を持ちます。

        ```text
        NAME                    -> default Scope の file Target
        ./NAME                  -> default Scope の file Target (explicit form)
        ./NAME/                 -> default Scope の directory Target
        SCOPE/NAME              -> named Scope の file Target
        SCOPE/NAME/             -> named Scope の directory Target
        /                       -> default Scope の全 Target
        SCOPE/                  -> named Scope の全 Target
        :[...]                  -> default Scope の typed literal Target list
        SCOPE:[...]             -> named Scope の typed literal Target list
        :<regex>                -> default Scope の regular-expression Target selector
        SCOPE:<regex>           -> named Scope の regular-expression Target selector
        ```

        Literal Target reference は末尾 `/` なしを file、末尾 `/` ありを directory とし、filesystem から型を推測しません。`SCOPE/` は Scope expansion に予約されるため、default Scope の directory Target は `./NAME/` と書きます。全展開は Scope の `target_kind` に対応する direct child だけを対象とし、再帰しません。Directory mode では eligible directory、file mode では eligible regular file、both mode ではその両方を展開します。

        `[...]` の list item も同じ型規則を使います。`/` は item separator でもあるため、途中の directory item は `project//archive.zip` のように directory marker と separator が `//` になります。3連以上の `/` は error です。`<...>` は file candidate を `NAME`、directory candidate を `NAME/` と正規化した文字列全体へ Python-compatible regular expression を full-match します。`/?` などで両型を明示的に選べます。Pattern は空にできず、512 character 超、invalid regex、0件 match を error とします。

        Base chain では名前付き Scope だけを名前ごとに重ね、同名 Scope は `description` / `target_kind` / `path` / `ignore` / `namespace` を含む definition 全体として外側の Configuration が置き換え、異名 Scope は共存します。Default Scope は base から継承せず、常に root Configuration に属します。したがって Base の `[scope]` metadata / policy は outer Root では使用されませんが、その Base Configuration 自身を Root として使う場合には通常どおり有効です。名前付き Scope の root は定義元 Configuration を基準にした場所のままで rebase しません。

        Scope には任意で `namespace = "<name>"` を指定できます。これは Target の探索場所を変えず、その Scope から得た Target の Archive root に、別途定義した{{TERM_18}}を prefix として追加します。Namespace は衝突時だけ自動適用されるものではなく、指定した Scope の Target に常に適用されます。

        名前付き Scope の path が現在の filesystem で利用可能かどうかは、その Scope を Target reference で実際に使うときに確認します。未マウントなどで存在しない named Scope が定義されていても、別の Scope だけを使う実行は妨げません。Named Scope の root location 自体は symbolic link / Windows directory junction を含められますが、解決した Scope root 直下で自動発見した link-like entry は Target として選択・展開しません。厳密な duplicate root、Namespace reference、Target resolution の規則は `../specification/INDEX.md` を参照してください。
        """
        title @= 'Scope'

        example_004 @= """
        [scope]
        ignore = ["archive/", "tmp-*/"]
        """

        example_005 @= """
        [scope.work]
        path = "../work"
        ignore = ["archive/", "tmp-*/"]

        [scope.oss]
        path = "/srv/oss"
        ignore = ["old-*/"]
        """

        merge @= TERMS.TERM_14
        merge @= TERMS.TERM_16
        merge @= TERMS.TERM_18

    class SECTION_031:
        r"""
        {{TERM_18}}は、source root が Archive 上で同じ path に解決される場合などに、source を明示的に区別して配置するための Archive 専用 prefix です。Namespace 自体は名前付きの空 table として定義します。

        ```toml
        {{example_006}}
        ```

        Namespace 名そのものが Archive 上の1 directory 名になります。現時点で `[namespace.<name>]` は属性を持ちません。不要な設定値を持たせず、将来 Namespace 固有の policy が必要になった場合に同じ table を拡張できる構造とします。

        Scope と Always source は Namespace 名を参照できます。

        ```toml
        {{example_007}}
        ```

        たとえば `work/project` の source root が `project/` なら `work/project/`、Always source の通常の source root が `docs/` なら `external/docs/` として Archive に配置します。Namespace を指定しない source は従来どおり source root 自体を Archive root とします。

        異なる resolved source の最終 Archive root が同じになる場合、dirpluck は source を黙って merge せず error にします。Namespace はこの衝突を明示的に避けるために使えますが、自動的に一意性を保証するものではありません。同じ Namespace を共有して最終 Archive root が再び同じになれば error です。

        生成される{{TERM_10}}では、各 source の final Archive root 自体を見出しとして表示します。Namespace を使う場合も、その最終配置 path が見出しへ直接反映され、Namespace と Source root を分離した補助 metadata や Namespace の定型説明文は追加しません。
        """
        title @= 'Namespace'

        example_006 @= """
        [namespace.work]

        [namespace.external]
        """

        example_007 @= """
        [namespace.work]
        [namespace.external]

        [scope.work]
        path = "/srv/work"
        namespace = "work"

        [always.docs]
        path = "../docs"
        namespace = "external"
        description = "External documentation."
        must = ["*.md"]
        """

        merge @= TERMS.TERM_10
        merge @= TERMS.TERM_18

    class SECTION_004:
        r"""
        `[always.<name>]` は Configuration 側で source directory を固定し、実行のたびに参加させる{{TERM_5}}です。`path` は relative path と absolute path のどちらでも指定できます。

        ```toml
        {{example_008}}
        ```

        Relative `path` は、その definition が記述されている Configuration file の directory を基準に解決します。`..` を使って外側の directory を参照することもできます。Absolute `path` は host filesystem 上の場所を直接参照します。明示した Always root location は symbolic link / Windows directory junction を含めることができ、alias の参照先 directory を source root として利用します。Archive 上の source root 名は実体側へ置き換えず、Configuration に書いた location 側の name / relative path を使います。

        解決された source directory 自体が selection boundary です。Root 自体に alias を使えることと、Source 内の自動 traversal で link-like entry をたどることは別です。Source 内で symbolic link または Windows directory junction として認識した entry は選択せず、リンク先もたどりません。

        Always source には任意で `namespace = "<name>"` を指定し、定義済みの{{TERM_18}}を Archive root の外側へ追加できます。Filesystem 上の source path や selection boundary は変わりません。

        Always source の Selection は Target の Pluck とは独立して評価します。同じ physical file が Target 配下にも存在していても、Target 側の `ignore` や Selection result は Always source の Selection を変更しません。両方が同じ physical file を選択し、異なる Archive path に配置する場合は両方を収録します。生成される{{TERM_10}}では、Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合、その Always source section に Target 側の Archive root と重複 file 数を表示します。

        複数の Always source は名前を変えて定義します。Pluck を持たず Always source だけで完結する Configuration も有効です。
        """
        title @= 'Always'

        example_008 @= """
        [always.guidelines]
        path = "review-guidelines"
        description = "Guidelines used for every review."
        must = ["*.md"]

        [always.company_reference]
        path = "/srv/company/reference"
        description = "Reference material maintained outside this project."
        must = ["*.md"]
        """

        merge @= TERMS.TERM_5
        merge @= TERMS.TERM_10
        merge @= TERMS.TERM_18
