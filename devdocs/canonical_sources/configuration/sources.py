from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_003 = test_target_field("example 003")
example_004 = test_target_field("example 004")
example_005 = test_target_field("example 005")
example_006 = test_target_field("example 006")
example_007 = test_target_field("example 007")
example_008 = test_target_field("example 008")


@summary("Pluck、Scope、Namespace、Always source の定義と配置。")
@canonical_source(
    "Configuration sources", filename="sources.md", order=10, merge_policy="local", heading="title"
)
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

        title @= "Pluck"

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

        `target_kind = "directory"` の Scope は直下の eligible directory だけ、`target_kind = "file"` は直下の eligible regular file だけ、`target_kind = "both"` はその両方を Target candidate とします。`target_kind` は Scope 直下の entry に対する type filter として働きます。Scope `ignore` は除外側の規則として広く扱い、末尾 `/` なしは matching file / directory Target candidate の両方、末尾 `/` ありは directory candidate だけを除外します。File selection の `pluck.ignore` とは役割が違います。`description` はその Scope から得た Target group の Archive README context として1回表示されます。Generated README の Scope 名は選択範囲を識別するための名前であり、Target 間の優先度・重要度・階層関係を表しません。追加の意味を持たせる場合は `description` に明記します。

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

        title @= "Scope"

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
        {{TERM_18}}は source の logical Archive identity を補助する名前付き concept です。Namespace 自体は名前付きの空 table として定義します。

        ```toml
        {{example_006}}
        ```

        Namespace 名は1個の Archive directory component です。現時点で `[namespace.<name>]` は属性を持ちません。`/` と `\`、ASCII control character は Archive component の構造を壊すため拒否しますが、dirpluck は OS 固有の予約名や filename 規則を独自判定しません。別の OS / filesystem へ展開する Archive を作る場合は、利用者が展開先に適した名前を選んでください。Namespace 名の一意性は大文字小文字を区別せず判定します。

        Scope の `namespace = "<name>"` は Target の final Archive root の prefix として使用します。Namespace は 1.0 では Scope 専用の Archive grouping concept です。

        ```toml
        {{example_007}}
        ```

        0.16.x 以降の 0.x series では `[always.<name>].namespace` も pre-1.0 compatibility として受理しますが、1.0.0 で削除します。Always source の Archive directory name は `[always.<name>]` の `<name>` に直接記述してください。互換期間の挙動と warning は `../specification/compatibility.md` と `../migration/0.16.md` を参照してください。

        生成される{{TERM_10}}では、各 source の final Archive root 自体を見出しとして表示し、Namespace と source root を分離した補助 metadata は追加しません。
        """

        title @= "Namespace"

        example_006 @= """
        [namespace.work]

        [namespace.external]
        """

        example_007 @= """
        [namespace.work]

        [scope.work]
        path = "/srv/work"
        namespace = "work"
        """

        merge @= TERMS.TERM_10
        merge @= TERMS.TERM_18

    class SECTION_004:
        r"""
        `[always.<name>]` は Configuration 側で source directory を固定し、実行のたびに参加させる{{TERM_5}}です。0.16.0 以降、`<name>` は Always source の Archive directory identity そのものです。`path` は filesystem 上の取得元 directory / Selection root だけを指定し、path の basename や Configuration directory からの relative path は Archive root に使いません。

        ```toml
        {{example_008}}
        ```

        たとえば `[always.guidelines] path = "review-guidelines"` は selected file を `guidelines/` の下へ配置します。`review-guidelines` という source directory name は Archive path に現れません。`[always.company_reference] path = "/srv/company/reference"` も `company_reference/` の下へ配置します。

        Relative `path` は、その definition が記述されている Configuration file の directory を基準に解決します。`..` を使って外側の directory を参照でき、absolute `path` は host filesystem 上の directory を直接参照します。`path` は必ず実在 directory に解決し、その directory 自体を Selection boundary とします。Filesystem root も明示的な Always source directory として使用できます。明示 location は symbolic link / Windows directory junction を含められますが、その root 内の自動 traversal で link-like entry は選択・走査しません。

        Always source の Archive directory identity は `[always.<name>]` の `<name>` だけで決まります。1.0 では Always source に `namespace` field を持たせません。0.16.x 以降の 0.x series で受理する `namespace` は pre-1.0 compatibility であり、1.0.0 で削除します。

        Always source の Selection は Target の Pluck とは独立して評価します。同じ physical file が Target 配下にも存在していても、Target 側の `ignore` や Selection result は Always source の Selection を変更しません。両方が同じ physical file を選択し、異なる Archive path に配置する場合は両方を収録します。Target と Always の final archive root が完全に同じ spelling なら、同じ destination region への意図的な composition として共有できます。`App` と `app` のように大文字小文字だけが異なる root は曖昧なので error です。共有 region 内で異なる physical file が同じ final Archive entry path に解決された場合は、通常の Archive entry collision として error にします。

        TOML syntax と Configuration schema の検証を先に行い、Always source 名は大文字小文字を区別しない比較で一意にします。Runtime Target 同士の final archive root も同じ kind 内では一意です。Target と Always の間だけは上記の exact-spelling composition を許可し、case-only ambiguity は拒否します。Pluck を持たず Always source だけで完結する Configuration も有効です。
        """

        title @= "Always"

        merge @= TERMS.TERM_5

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
