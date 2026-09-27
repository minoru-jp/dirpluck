from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.filesystem import SPECIFICATION_PART as FILESYSTEM_SPEC
from devdocs.canonical_sources.specification.namespace import SPECIFICATION_PART as NAMESPACE_SPEC
from devdocs.canonical_sources.specification.runtime_targets import SPECIFICATION_PART as RUNTIME_TARGETS_SPEC
from devdocs.canonical_sources.specification.selection import SPECIFICATION_PART as SELECTION_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary('final archive root、entry collision、generated README の planning 規則。')


@canonical_source('Archive planning', filename='archive.md', order=90, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_095:
        r"""Scope から解決した Target の source root は Target entry name 1 segment とする。Directory Target では directory name、file Target では file name を使用する。Logical Scope name は archive path へ暗黙には含めない。"""
        level @= MUST
        related @= (RUNTIME_TARGETS_SPEC.SECTION_502.SPEC_050,)

    class SPEC_096:
        r"""Always source の source root は、実体 directory ではなく Configuration に明示された source location から決める。Source location が、その definition を記述した Configuration file directory の配下にある場合は、その Configuration directory から見た lexical relative path とする。Absolute path または `..` により source location がその base 外にある場合は、明示 location の最終 directory name を source root とする。最終 component が symbolic link / Windows directory junction で実体 directory name と異なる場合も、Archive では明示 location 側の name を保持する。Filesystem root 自体を Always source として受理しないのは、この portable source root を持たないためである。Host の absolute path、drive、UNC share 名そのものは archive path へ埋め込まない。"""
        level @= MUST

    class SPEC_097:
        r"""{{TERM_18}}を参照しない source の final archive root は source root と同じである。Namespace を参照する source は `NAMESPACE/SOURCE_ROOT` を final archive root とする。Directory source はその下へ source directory からの relative selected file path を配置する。File Target は final archive root 自体を1個の file entry として配置する。Namespace は collision が実際に起きた場合だけ追加するのではなく、その source へ常に適用する。"""
        merge @= TERMS.TERM_18
        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_063,)

    class SPEC_098:
        r"""1回の実行で異なる resolved source が同じ final archive root に解決された場合は、file selection の内容が重ならなくても ambiguity error とする。dirpluck は source を同じ directory へ黙って merge せず、自動 suffix や Scope / Always 名による自動 qualification も行わない。必要な場合は Configuration で Namespace を明示して final archive root を区別する。"""
        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_064,)

    class SPEC_099:
        r"""Final archive root が一意であることを確認した後、同じ archive path に異なる physical file が衝突する場合は ambiguity error とする。同じ archive path に同じ physical file が再度現れる場合は1回だけ書き込む。同じ physical file が異なる resolved source から異なる archive path へ解決されることは許可し、それぞれの archive path に書き込む。File Target は final archive root 自体が file entry になるため、その path が別の archive file path の ancestor / descendant になる file-directory conflict も error とする。"""
        level @= MUST

    class SPEC_100:
        r"""Directory Target の Pluck Selection と Always source の Selection は source ごとに独立して評価する。File Target は Selection を持たず atomic file 自体を source とする。ある physical file が directory Target の source tree に含まれていても、Target 側の `ignore`、未選択、missing result は Always source の Selection を変更しない。Physical overlap は各 source の最終 selected file 集合が確定した後に判定し、source ごとの result 自体を merge、suppress、error にしない。"""
        level @= MUST
        related @= (SELECTION_SPEC.SPEC_065,)

    class SPEC_101:
        r"""Archive root の root-level `README.md` は dirpluck が生成する index 用の予約 path とする。Resolved source の final archive root の先頭 component が case-insensitive に `README.md` と一致する場合は error とし、その下へ source tree を配置しない。この規則は Namespace 名だけでなく、Namespace を使わない source root にも同じように適用する。"""
        level @= MUST

    class SPEC_102:
        r"""Archive root には{{TERM_10}}を `README.md` として生成する。これは archive contents の index であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は `# Archive contents` の直後にその本文を表示する。存在しない場合はこの全体説明を省略する。"""
        merge @= TERMS.TERM_10
        level @= MUST

    class SPEC_103:
        r"""各 resolved source は、その final archive root を inline code とした level-2 heading で1 sectionずつ表現する。Directory source の heading / Source root 表示は末尾 `/` を付け、file Target は file path として末尾 `/` を付けない。Section には selected file 数を `Files: N` として記録する。Target の `scope.description` が存在する場合は最初に本文として表示し、directory Target では続けて Pluck selection `description` を表示する。File Target は Pluck を使わないため `scope.description` だけを表示する。Always source は従来どおり selection `description` を表示する。各 description は metadata の後へ本文としてそのまま置き、複数行も section body として保持する。"""
        level @= MUST

    class SPEC_104:
        r"""Always source が実際に選択した physical file と Target が実際に選択した physical file に重複がある場合、その Always source section に Target ごとの `Target overlap` metadata を表示する。Metadata は重複 file 数と Target の final archive root を記録する。同じ physical file が Target 側で `ignore` されるなどして実際には選択されていない場合は overlap に数えない。この metadata は physical overlap の説明であり、Selection や Archive placement を変更しない。"""
        level @= MUST
        condition @= "Always source と Target が同じ physical file を選択した場合"

    class SPEC_105:
        r"""少なくとも1個の source に Namespace が適用される場合、README は source section の前に Namespace が Archive 専用の outer directory であり元 source path の一部ではないこと、source root がその直下にあることを説明する。Namespace を使う各 source section には `Namespace` と `Source root` も表示する。Namespace を使わない source にはこの metadata を追加しない。"""
        level @= MUST
        condition @= "少なくとも1個の source に Namespace が適用される場合"

    class SPEC_106:
        r"""既定では source filesystem path、Configuration path / table、base chain、Scope / Pluck / Always 名、選択 Case などの dirpluck 固有情報を記録しない。Target overlap metadata は Target 名ではなく final archive root を使用する。CLI `--paths` が指定された場合だけ各 source section に `Source` として解決済み source filesystem path を `/` separator で記録する。Directory source では directory path、file Target では file path を表示する。`--paths` は archive path や selection を変更しない。"""
        level @= MUST
        condition @= "CLI `--paths` が指定された場合"
        related @= (FILESYSTEM_SPEC.SPEC_093,)
