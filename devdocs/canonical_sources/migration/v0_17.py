from shikumi_devdoc.norms.common import canonical_source
from shikumi_devdoc.norms.document import title


@canonical_source("Migrating to 0.17", filename="0.17.md", merge_policy="local", heading="title")
class MIGRATION_0_17:
    r"""
    0.17.0 は Archive 内の配置を明示する Layout を追加し、同時に final Archive root の一意性を source role 全体へ統一する breaking release です。0.16.x では Target と Always が完全に同じ spelling の root を共有して同じ destination region へ composition できましたが、0.17.0 では Target / Always を問わず同じ final Archive root へ解決する source を error にします。
    """

    class SECTION_001:
        r"""
        0.16.x では、たとえば runtime Target `./app/` と `[always.app]` を同時に選ぶと、両方を `app/` の下へ配置できました。

        ```toml
        [always.app]
        path = "support/app"
        must = ["notes.md"]

        [pluck]
        must = ["src/"]
        ```

        この Configuration で `./app/` を選ぶと、0.16.x では Target と Always が同じ destination region を共有し、entry 同士が直接衝突しない限り次のような Archive を作れました。

        ```text
        app/
        ├── notes.md
        └── src/
            └── main.py
        ```

        0.17.0 ではこの共有を許可しません。Archive placement は source ごとに一意な final root を持つ必要があり、Target と Always が同じ `app` に解決した時点で Configuration / resolution error になります。大文字小文字だけが異なる root も従来どおり同一視して error です。
        """

        title @= "Target と Always の同一 root composition を廃止"

    class SECTION_002:
        r"""
        推奨する移行方法は Layout で source role ごとの最上位 directory を分けることです。Layout は必ず `[layout.<name>]` で宣言し、`description` は任意です。

        ```toml
        [about]
        always_layout = "dependencies"
        targets_layout = "development-targets"

        [layout.dependencies]
        description = "開発に必要な固定資料。"

        [layout.development-targets]
        description = "今回選択した開発対象。"

        [always.app]
        path = "support/app"
        must = ["notes.md"]

        [pluck]
        must = ["src/"]
        ```

        同じ `./app/` Target を選んでも final Archive root は `dependencies/app/` と `development-targets/app/` に分かれ、衝突しません。

        ```text
        dependencies/
        └── app/
            └── notes.md
        development-targets/
        └── app/
            └── src/
                └── main.py
        ```

        `[about].always_layout` / `[about].targets_layout` は総則です。個別 source では `[always.<name>].layout`、`[scope].layout`、`[scope.<name>].layout` で上書きできます。個別指定も総則も無い source は従来どおり Archive root 直下へ配置します。
        """

        title @= "Layout で destination region を分ける"

    class SECTION_003:
        r"""
        Layout を使わず、Always name 自体を変更して root を分ける移行も可能です。

        ```toml
        [always.support-app]
        path = "support/app"
        must = ["notes.md"]
        ```

        この場合は `support-app/` と Target の `app/` が別 root になります。Layout は source filesystem directory を指定する機能ではなく、Archive destination の最上位 directory を宣言する機能です。配置先として参照する名前は `[layout.<name>]` に存在しなければならず、未定義 Layout reference は error です。空の `[layout.<name>]` は有効で、`description` を省略しても配置できます。
        """

        title @= "Always name を変更する移行も可能"

    class SECTION_004:
        r"""
        0.17.0 の Layout は Namespace と合成しません。同じ Scope で effective Layout と `namespace` が同時に有効になる場合、または compatibility Always `namespace` と effective Layout が同時に有効になる場合は error です。Namespace は 1.0.0 に向けて削除方針が強まっている compatibility surface なので、新しい配置設計では Layout を使用してください。

        0.14.x 由来の Always layout migration warning は、0.17.0 の explicit Layout が有効な Always では報告しません。Explicit Layout が最終 Archive destination を意図的に決めている状態で、0.16.x の中間 placement を migration warning として表示すると現在の出力と食い違うためです。Layout を使用しない旧 Configuration では従来の 0.14.x → 0.16.x migration warning を維持します。
        """

        title @= "Namespace と legacy migration warning"
