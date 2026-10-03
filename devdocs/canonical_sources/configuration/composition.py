from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_019 = test_target_field("example 019")


@summary('Base Configuration による再利用と composition。')
@canonical_source('Configuration composition', filename='composition.md', order=30, merge_policy="local", heading="title")
class CONFIGURATION_PART:
    r"""
    この文書は、`[about].base` を使った Base Configuration の再利用と filesystem anchor の考え方を説明します。

    この guide は Base Configuration の authoring を説明し、base chain、shadowing、cycle detection の厳密な契約は `../specification/composition.md`、relative path anchor は `../specification/paths.md` が定義します。CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` にあります。
    """

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2

    class SECTION_013:
        r"""
        既存の Configuration を基礎として再利用するときは、`[about]` の `base` で{{TERM_13}}を参照します。

        ```toml
        {{example_019}}
        ```

        `base` は1個の Configuration file を参照します。参照先がさらに `base` を持つ場合は linear base chain になります。Base chain の深さに固定上限はありません。

        各 Configuration に書かれた relative filesystem path は、常にその Configuration file 自身の directory を基準に解決します。Base Configuration から継承した named Scope や Always source の path を、外側 Configuration の位置へ rebase しません。Default Scope も同じ Configuration-directory model に従い、Root Configuration file の directory をそのまま root とします。

        Pluck、Always、Scope、Shared pattern の composition、description resolution、cycle detection、Output の扱いは `../specification/INDEX.md` に定義します。Base Configuration は Output を省略できます。Output を持たない root Configuration も `--preview` に使用でき、通常 build でも CLI `--here` / `--output` または Python API `output=` で runtime Output を与えれば実行できます。Runtime Output を使わない build では root 自身の fixed または timestamp Output を直接宣言します。
        """
        title @= 'Base Configuration'

        example_019 @= """
        [about]
        base = "../common/common.dirpluck"
        """

        merge @= TERMS.TERM_13
