from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.specification import MUST, condition, level
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary("Configuration document の top-level schema と table 構造。")
@canonical_source(
    "Configuration schema",
    filename="configuration-schema.md",
    order=20,
    merge_policy="local",
    heading="identity",
)
class SPECIFICATION_PART:
    class SPEC_011:
        r"""
        受理する top-level 構造は次とする。

        ```text
        [about]
        [shared.must]
        [shared.may]
        [shared.ignore]
        [pluck]
        [case.pluck.<name>]
        [case.always.<name>]
        [scope]
        [scope.<name>]
        [layout.<name>]
        [namespace.<name>]
        [always.<name>]
        [output]
        [output.timestamp]
        ```
        """

        level @= MUST

    class SPEC_012:
        r"""未知の key は error とする。"""

        level @= MUST

    class SPEC_013:
        r"""`[about]` は任意で、`description` / `description_no_targets` / `description_no_always` / `description_empty` / `always_layout` / `targets_layout` / `base` を持てる。各 field は任意だが、`[about]` を定義する場合は少なくとも1 field を必要とする。4つの description field は空でない string とする。`always_layout` / `targets_layout` は1個の Archive directory component として有効な Layout name reference、`base` は1個の Configuration file path とする。"""

        level @= MUST
        condition @= "`[about]` を定義する場合"

    class SPEC_014:
        r"""Base chain を構成する各 Configuration は Pluck を0個または1個、名前付き Scope、Layout、Always source、Shared pattern、{{TERM_18}}を0個以上持てる。`[scope]` は root Configuration で常設される default Scope の optional `description` / `target_kind` / `ignore` / `layout` / `namespace` 設定であり、Scope の存在宣言ではない。Named Scope は required `path` と同じ optional field を持つ。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` とする。`[layout.<name>]` は Archive 内の最上位 directory を宣言する名前付き definition で、optional `description` だけを持てる。`description` を省略した空 table も valid とし、親 `[layout]` だけを定義して名前付き Layout を1個も持たない Configuration は error とする。Layout name は TOML key として解釈した後に1個の Archive directory component として検証し、同一 Configuration 内で大文字小文字を区別しない比較で一意でなければならない。Canonical `[always.<name>]` は required `path`、Selection field、optional `layout` を持ち、`namespace` は 1.0 schema に含めない。Case definition は top-level `[case]` namespace の下に置き、`[case.pluck.<name>]` は Pluck の完全な Selection、`[case.always.<name>]` は effective Always source 集合の membership filter とする。これにより `case` は Always source 名として予約せず、`[always.case]` は通常の Always source definition として使用できる。"""

        merge @= TERMS.TERM_18
        level @= MUST

    class SPEC_015:
        r"""各 Configuration は Output を0個または1個宣言できる。Output を宣言する場合、fixed output と timestamp output は排他的である。Configuration file 単体の schema validity と Archive planning / `--preview` には Output を要求しない。Archive file を書き込む build では、{{TERM_14}}自身の Output declaration または runtime Output のどちらかを必要とする。Base Configuration の Output は Root Configuration へ継承しない。"""

        merge @= TERMS.TERM_14
        level @= MUST
        condition @= "Output を宣言する場合"
        condition @= "Archive file を書き込む build"

    class SPEC_016:
        r"""各 Configuration と Base composition 後の{{TERM_15}}は source definition を1個も持たなくてもよい。Pluck、Always source、named Scope はすべて optional であり、常設の default Scope だけを持つ Effective Configuration も valid とする。Runtime request の結果として resolved source が0個でも build / preview は正常に成立し、Archive は generated `README.md` だけを含められる。"""

        merge @= TERMS.TERM_15
        level @= MUST
        condition @= "Base composition 後"
