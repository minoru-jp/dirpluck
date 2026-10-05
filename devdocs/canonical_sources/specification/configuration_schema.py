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
        r"""`[about]` は任意で、`description` と `base` だけを持つ。両 field はそれぞれ任意だが、`[about]` を定義する場合は少なくとも一方を必要とする。`description` は空でない string、`base` は1個の Configuration file path とする。"""

        level @= MUST
        condition @= "`[about]` を定義する場合"

    class SPEC_014:
        r"""Base chain を構成する各 Configuration は Pluck を0個または1個、名前付き Scope、Always source、Shared pattern、{{TERM_18}}を0個以上持てる。`[scope]` は root Configuration で常設される default Scope の optional `description` / `target_kind` / `ignore` / `namespace` 設定であり、Scope の存在宣言ではない。Named Scope は required `path` と同じ optional field を持つ。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` とする。Canonical `[always.<name>]` は required `path` と Selection field だけを持ち、`namespace` は 1.0 schema に含めない。Case definition は top-level `[case]` namespace の下に置き、`[case.pluck.<name>]` は Pluck の完全な Selection、`[case.always.<name>]` は effective Always source 集合の membership filter とする。これにより `case` は Always source 名として予約せず、`[always.case]` は通常の Always source definition として使用できる。"""

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
