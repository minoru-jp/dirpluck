from devdocs.canonical_sources.specification.archive import SPECIFICATION_PART as ARCHIVE_SPEC
from devdocs.canonical_sources.specification.output import SPECIFICATION_PART as OUTPUT_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, summary


@summary("preview mode の出力と副作用境界。")
@canonical_source(
    "Preview", filename="preview.md", order=110, merge_policy="local", heading="identity"
)
class SPECIFICATION_PART:
    class SPEC_145:
        r"""`--preview` は、同じ Configuration / Target / Case / Selection 入力から通常 build が作成する Archive plan と同じ source selection と Archive 内配置を表示し、output file / directory を作成・変更しない。Root Configuration に Output declaration がなくても使用できる。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--archive-mtime` は preview でも validation するが、Archive を書かないため preview result には影響しない。"""

        level @= MUST
        condition @= "`--preview` を使用する場合"
        related @= (ARCHIVE_SPEC.SPEC_098, OUTPUT_SPEC.SPEC_107)

    class SPEC_146:
        r"""Preview は不足する required `must` と optional `may` を区別し、path ではない Selection expression を filesystem path と誤解させない形で未一致として表現する。最終 selection が0件の場合は、現在の `allow_empty` policy で成功可能か通常 build なら error になるかを判別できるようにする。型 marker の不一致候補が検出された `must` / `may` は selection result の required / optional missing semantics を変えず、source を識別できる non-fatal diagnostic も生成する。CLI `--preview` はその diagnostic を stderr へ報告し、Python API の `preview=True` は `RunResult.warnings` に返す。Tree node の exact label、記号、整形は互換性契約に含めない。"""

        level @= MUST
        condition @= "`--preview` で selection result を表示する場合"

    class SPEC_147:
        r"""`--preview` でも、有効な Archive plan を構築するために必要な Configuration / Base / Scope / Target / Shared / Namespace / Case / Selection / Archive layout の validation を省略しない。使用した Scope root や source path が解決できない場合は error とする一方、未使用の named Scope root が現在存在しないことだけでは error にしない。Archive を実際に書き込む処理だけに必要な destination existence / replacement validation は preview の契約に含めない。"""

        level @= MUST
        condition @= "`--preview` で Archive plan を構築する場合"
