from shikumi_devdoc.norms.common import canonical_source
from shikumi_devdoc.norms.document import title


@canonical_source("Migrating to 0.16", filename="0.16.md", merge_policy="local", heading="title")
class MIGRATION_0_16:
    r"""
    0.16.0 は Always source の Archive identity を修正する breaking release です。0.14.x 以前では Always の `path` から Archive root を導出し、必要に応じて `namespace` をその外側へ追加していました。0.16.0 以降は `[always.<name>]` の `<name>` が Archive directory を決め、`path` は filesystem 上の source directory だけを指定します。
    """

    class SECTION_001:
        r"""
        0.14.x 以前では次の Configuration は source location から `documentation/` を導出しました。

        ```toml
        [always.docs]
        path = "../external/documentation"
        must = ["guide.md"]
        ```

        0.16.0 では同じ Configuration は `docs/guide.md` を生成します。`documentation` は filesystem 上の source directory name にすぎず、Archive identity には使いません。

        ```text
        docs/
        └── guide.md
        ```

        `<name>` と `path` は別の責務を持ちます。`<name>` は Archive directory identity、`path` は Selection root です。`path` は実在 directory に解決しなければならず、選択された file はその directory からの relative path を `<name>/` の下へ維持して配置します。
        """

        title @= "Always name が Archive directory を決める"

    class SECTION_002:
        r"""
        0.14.x の Always Namespace は filesystem 由来の source root の外側へ prefix を追加していました。

        ```toml
        [namespace.reference]

        [always.docs]
        path = "../external/documentation"
        namespace = "reference"
        must = ["guide.md"]
        ```

        0.16.x 以降の 0.x series では `namespace = "reference"` を pre-1.0 compatibility の name override として扱います。上の Configuration は、名前解決後に `[always.reference]` と同じ effective Always name を持つものとして新しい配置規則へ進み、`reference/guide.md` を生成します。旧 `reference/documentation/guide.md` placement は維持しません。この `namespace` field は 1.0.0 で削除するため、移行先では `[always.reference]` のように目的の Archive directory name を Always identifier へ直接記述してください。

        Always namespace を読み込むと公開 `AlwaysMigrationWarning` を必ず報告します。この warning は `namespace` field が 1.0.0 で削除されることと、Always identifier へ Archive directory name を直接記述する移行先を知らせます。0.16.0 から 1.0.0 未満まで報告し、1.0.0 では field の受理と warning をともに取り外します。
        """

        title @= "Always Namespace は 1.0 で削除"

    class SECTION_003:
        r"""
        Namespace を使わない新しい Configuration では、目的の Archive directory name を直接 Always name に書いてください。

        ```toml
        [always.reference]
        path = "../external/documentation"
        must = ["guide.md"]
        ```

        Always の effective name と Runtime Target の final archive root は、Archive destination region として比較します。Namespace override を使う Always は override 後の名前で評価します。Target と Always が `app` のように完全に同じ spelling を持つ場合は、同じ destination region への意図的な composition として共有できます。一方 Target `App` と Always `app` のように casefold 後だけ一致する別 spelling は曖昧なので error です。Target 同士、Always 同士の root identity は引き続き大文字小文字を区別しない比較で一意でなければなりません。共有 region 内の実 entry collision は Archive planner が通常どおり検出します。

        dirpluck は Always / Namespace の名前について、Windows の予約名や末尾 dot など host OS 固有の filename rule を独自に再実装しません。一方、`/` と `\` は path separator として解釈され得て1個の Archive componentという境界を壊すため拒否し、ASCII control character U+0000..U+001F と U+007F も Archive entry name の切り詰めや表示崩れを避けるため拒否します。Archive を別の OS / filesystem へ移動して展開する場合、その他の名前がその展開先で有効か、また同一視されないかは利用者が確認してください。一般的な展開時衝突を避けるため、dirpluck 自身の Archive identity 一意性では大文字小文字を区別しません。
        """

        title @= "移行時の確認事項"

    class SECTION_004:
        r"""
        0.16.0 から 1.0.0 直前まで、dirpluck は 0.14.x で有効だった Always Archive identity と 0.16.x の effective Always name を比較します。両者が異なる場合だけ `AlwaysMigrationWarning` を報告し、warning message に旧 root と新 root を含めます。

        たとえば `[always.docs] path = "docs"` は旧・新とも `docs/` なので layout migration warning は出ません。一方 `[always.docs] path = "documentation"` は旧 `documentation/` から新 `docs/` へ変わるため warning を報告します。Python API では標準 warnings framework、CLI では同じ診断を stderr から確認できます。

        `namespace` の pre-1.0 compatibility warning はこの比較とは独立しています。Namespace を使用した場合は、Archive layout の比較結果にかかわらず 1.0.0 での削除と移行先を通知します。
        """

        title @= "移行 warning は実際の layout 差分を検出する"

    class SECTION_005:
        r"""
        Pluck Case の canonical syntax は `[pluck.case.<name>]` から `[case.pluck.<name>]` へ移動します。Always Case は新しく `[case.always.<name>]` として追加し、effective Always source 集合から参加 source を `include` または `exclude` で選びます。`include = []` は Always を0件にする明示的な選択です。

        ```toml
        [case.pluck.audit]
        must = ["documents/", "records/"]

        [case.always.release]
        include = ["docs", "license"]
        ```

        0.16.0 から 1.0.0 未満では legacy `[pluck.case.<name>]` も互換入力として受理し、`ConfigurationDeprecationWarning` で `[case.pluck.<name>]` への移行を案内します。同じ Configuration document で同名 Case を新旧両方に定義した場合は曖昧さを避けるため error です。1.0.0 では legacy `[pluck.case.<name>]` を削除します。

        Runtime Case selector も2軸になり、`--case audit` は Pluck Case だけ、`--case .release` は Always Case だけ、`--case audit.release` は両方を選びます。この分離により、Always source の存在によって Pluck Case の可視性が変わることはありません。
        """

        title @= "Case syntax を top-level namespace へ移す"
