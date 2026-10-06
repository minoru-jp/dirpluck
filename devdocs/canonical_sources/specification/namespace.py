from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.specification import MAY, MUST, level
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary("Archive placement に使用する Namespace の canonical semantics。")
@canonical_source(
    "Namespace", filename="namespace.md", order=60, merge_policy="local", heading="identity"
)
class SPECIFICATION_PART:
    class SPEC_061:
        r"""{{TERM_18}}は `[namespace.<name>]` という名前付き table で定義する。現行 schema では table 本体は空でなければならず、属性を受理しない。親 `[namespace]` だけを空で定義することは Namespace definition にならないため error とする。"""

        merge @= TERMS.TERM_18
        level @= MUST

    class SPEC_062:
        r"""Namespace name は TOML key として解釈された後、1個の Archive directory component として検証する。空名、`.`、`..`、path separator の `/` と `\`、ASCII control character U+0000..U+001F と U+007F を拒否する。これらは host OS の filename rule ではなく、Archive entry name を安全な1 componentとして保持するための構造上の制約である。dirpluck は host OS ごとの予約名、末尾 dot、その他の filesystem 固有 naming rule を独自に判定しない。Namespace は filesystem path ではなく、source の logical Archive identity を補助する名前付き Configuration concept である。"""

        level @= MUST

    class SPEC_063:
        r"""Scope の `namespace` field は effective Namespace name を参照し、Layout を使用しない Target の final archive root に `NAMESPACE/` prefix を追加する。Scope root、Target discovery、Target entry name は変更しない。Unknown Namespace reference は Configuration error とする。同じ Scope に個別または `[about].targets_layout` 由来の effective Layout が存在する場合は Namespace と Layout を合成せず Configuration error とする。0.x compatibility として Always `namespace` を使用する source でも、個別または `[about].always_layout` 由来の effective Layout が同時に存在する場合は Namespace と Layout を合成せず Configuration error とする。Namespace だけを使用する Always の compatibility semantics は Compatibility specification に従う。"""

        level @= MUST

    class SPEC_168:
        r"""複数 Scope が同じ Namespace definition を参照すること自体は有効である。Namespace definition name は大文字小文字を区別しない比較で一意とする。Scope Namespace 適用後の final archive root は通常の Archive identity / collision rule に従う。実際に Archive へ書き込む spelling は Configuration / Target name の表記を保持する。"""

        level @= MAY

    class SPEC_169:
        r"""dirpluck は Archive directory identity について host OS / filesystem 固有の予約名、末尾 dot、Unicode normalization などを再現して cross-platform extraction compatibility を保証しない。別の OS / filesystem へ Archive を移動して展開する場合、その環境で有効かつ意図どおり区別される名前を選ぶ責任は Configuration author にある。大文字小文字を区別しない一意性検証は dirpluck 自身の Archive identity rule として適用する。"""

        level @= MUST
