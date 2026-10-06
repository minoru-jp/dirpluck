from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.filesystem import SPECIFICATION_PART as FILESYSTEM_SPEC
from devdocs.canonical_sources.specification.namespace import SPECIFICATION_PART as NAMESPACE_SPEC
from devdocs.canonical_sources.specification.runtime_targets import (
    SPECIFICATION_PART as RUNTIME_TARGETS_SPEC,
)
from devdocs.canonical_sources.specification.selection import SPECIFICATION_PART as SELECTION_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary("final archive root、entry collision、generated README の planning 規則。")
@canonical_source(
    "Archive planning", filename="archive.md", order=90, merge_policy="local", heading="identity"
)
class SPECIFICATION_PART:
    class SPEC_095:
        r"""Scope から解決した Target の source root は Target entry name 1 segment とする。Directory Target では directory name、file Target では file name を使用する。Logical Scope name は archive path へ暗黙には含めない。"""

        level @= MUST
        related @= (RUNTIME_TARGETS_SPEC.SECTION_502.SPEC_050,)

    class SPEC_096:
        r"""Always source と有効化された Extra source の final archive root は filesystem source location から導出せず、それぞれ `[always.<name>]` / `[extra.<name>]` の `<name>` とする。`path` の basename、Configuration directory からの lexical relative path、host の absolute path、drive、UNC share 名は Archive identity に使用しない。"""

        level @= MUST

    class SPEC_097:
        r"""Source に effective Layout がある場合、final archive root は宣言済み Layout name を最上位 component とし、その下へ Target source root または effective Always / Extra name を置く。Layout がない Target は従来どおり optional Scope Namespace prefix を Target source root へ適用し、Layout がない Always / activated Extra source は effective source name 自体を final archive root とする。同一 source で effective Layout と Namespace は併用しない。Directory source は final archive root の下へ source directory からの relative selected file path を配置する。File Target は final archive root 自体を1個の file entry として配置する。Layout definition を宣言しただけでは Archive directory entry を生成しない。"""

        merge @= TERMS.TERM_18
        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_063,)

    class SPEC_098:
        r"""最終的に解決されたすべての source の final archive root は source role に関係なく、大文字小文字を区別しない比較で一意でなければならない。Target と Always / activated Extra が完全に同じ spelling の root へ解決する場合も destination region を共有せず error とする。`App` と `app` のように spelling は異なるが casefold 後に一致する root も曖昧なので error とする。Layout は final archive root の最上位 component に含まれるため、Layout 適用後の完全な final root に対して同じ一意性規則を適用する。Archive に記録する実際の spelling は保持する。"""

        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_168,)

    class SPEC_099:
        r"""同じ archive path に異なる physical file が衝突する場合は ambiguity error とする。同じ archive path に同じ physical file が再度現れる場合は1回だけ書き込む。同じ physical file が異なる resolved source から異なる archive path へ解決されることは許可し、それぞれの archive path に書き込む。File Target は final archive root 自体が file entry になるため、その path が別の archive file path の ancestor / descendant になる file-directory conflict も error とする。"""

        level @= MUST

    class SPEC_100:
        r"""Directory Target の Pluck Selection と Always / activated Extra source の Selection は source ごとに独立した意味を持つ。File Target は Selection を持たず atomic file 自体を source とする。ある physical file が directory Target の source tree に含まれていても、Target 側の `ignore`、未選択、missing result は Always / activated Extra source の Selection を変更しない。複数 source が同じ physical file を選ぶこと自体は source ごとの Selection result を変更せず、Archive path collision と generated README の overlap semantics だけに従う。"""

        level @= MUST
        related @= (SELECTION_SPEC.SPEC_065,)

    class SPEC_101:
        r"""Archive root の root-level `README.md` は dirpluck が生成する index 用の予約 path とする。Resolved source の final archive root の先頭 component が case-insensitive に `README.md` と一致する場合は error とし、その下へ source tree を配置しない。この規則は Layout / Namespace / source root のどれが先頭 component を与える場合にも同じように適用する。"""

        level @= MUST

    class SPEC_102:
        r"""Archive root には{{TERM_10}}を `README.md` として生成する。これは archive contents の index であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は resolved source の構成に関係なく Archive 全体の説明として含める。さらに、resolved source が Always role だけなら `description_no_targets`、Target だけなら `description_no_always`、Always role / Target とも0件なら `description_empty` を、その field が存在する場合に1個だけ追加する。Always と Target の両方が存在する場合は条件付き description を追加しない。ここで有効化された Extra source は Always source と同じ fixed / Always role として数える。Source の存在は selected file 数ではなく resolved source role で判定するため、`allow_empty = true` により selected file が0件の source も存在する source として扱う。Markdown の heading level、punctuation、空行などの細かな presentation は互換性契約に含めない。"""

        merge @= TERMS.TERM_10
        level @= MUST

    class SPEC_103:
        r"""Generated README は実際に使用された Layout のうち `description` を持つものについて、Layout directory name と description を識別できる情報を1回ずつ含める。Description を持たない Layout は placement として有効だが Layout 説明を必要としない。Source listing は Always source と有効化された Extra source を Target より先に表し、各 source / group の description を file-count、source-path、overlap などの補助 metadata より先に読める形で配置する。Target は Scope ごとにまとめ、Scope identity と `scope.description` を group context として示す。Directory Target はその Scope の Pluck group 配下に final archive root と selected file 数を示し、同一 Scope 内では Scope / Pluck selection `description` を Target ごとに繰り返さない。File Target は Pluck を使わないため Scope group 直下で atomic source として示す。Always source と有効化された Extra source は final archive root と自身の selection `description` を示す。Description の複数行内容は保持する。Heading level、inline-code 表記、label、空行などの細かな presentation は互換性契約に含めない。"""

        level @= MUST

    class SPEC_104:
        r"""Always source または有効化された Extra source が実際に選択した physical file と Target が実際に選択した physical file に重複がある場合、生成 README は重複 file 数と対応する Target の final archive root を識別できる情報を含める。同じ physical file が Target 側で `ignore` されるなどして実際には選択されていない場合は overlap に数えない。この情報は physical overlap の説明であり、Selection や Archive placement を変更しない。Label や表示形式は互換性契約に含めない。"""

        level @= MUST
        condition @= "Always source または有効化された Extra source と Target が同じ physical file を選択した場合"

    class SPEC_106:
        r"""Target grouping のため Scope identity と directory Target の Pluck context は README に記録できる。Scope identity は Target の選択範囲だけを表し、優先度・重要度・Target 間の階層関係を意味しないことを README 自身で説明する。Scope に追加の意味がある場合は `scope.description` がその意味を与える。選択した Pluck Case 名、Configuration path / table、base chain など実行 provenance は既定では記録しない。Physical overlap の識別には Target reference ではなく final archive root を使用する。Source filesystem path は既定では記録せず、CLI `--paths` が指定された場合だけ、各 source に対応する解決済み source filesystem path を `/` separator で README に含める。Directory source では directory path、file Target では file path を対象とする。`--paths` は archive path や selection を変更しない。表示 label や配置は互換性契約に含めない。"""

        level @= MUST
        condition @= "CLI `--paths` が指定された場合"
        related @= (FILESYSTEM_SPEC.SPEC_093,)
