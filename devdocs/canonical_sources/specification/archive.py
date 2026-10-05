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
        r"""Always source の final archive root は filesystem source location から導出せず、`[always.<name>]` の `<name>` とする。`path` の basename、Configuration directory からの lexical relative path、host の absolute path、drive、UNC share 名は Archive identity に使用しない。"""

        level @= MUST

    class SPEC_097:
        r"""Directory Target の final archive root は Target source root に optional Scope Namespace prefix を適用して決める。Always source は `[always.<name>]` の `<name>` 自体を final archive root とする。Directory source は final archive root の下へ source directory からの relative selected file path を配置する。File Target は final archive root 自体を1個の file entry として配置する。"""

        merge @= TERMS.TERM_18
        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_063,)

    class SPEC_098:
        r"""最終的に解決された Target 同士の final archive root は大文字小文字を区別しない比較で一意でなければならず、Always source 同士の final archive root も同じ一意性を満たす。Target と Always の間では、final archive root の spelling が完全一致する場合だけ同じ destination region への composition として共有を許可する。`App` と `app` のように spelling は異なるが casefold 後に一致する Target / Always root は曖昧なので error とする。Archive に記録する実際の spelling は保持し、共有 region の各 selected entry は通常の Archive entry collision rule で検証する。"""

        level @= MUST
        related @= (NAMESPACE_SPEC.SPEC_168,)

    class SPEC_099:
        r"""同じ archive path に異なる physical file が衝突する場合は ambiguity error とする。同じ archive path に同じ physical file が再度現れる場合は1回だけ書き込む。同じ physical file が異なる resolved source から異なる archive path へ解決されることは許可し、それぞれの archive path に書き込む。File Target は final archive root 自体が file entry になるため、その path が別の archive file path の ancestor / descendant になる file-directory conflict も error とする。"""

        level @= MUST

    class SPEC_100:
        r"""Directory Target の Pluck Selection と Always source の Selection は source ごとに独立した意味を持つ。File Target は Selection を持たず atomic file 自体を source とする。ある physical file が directory Target の source tree に含まれていても、Target 側の `ignore`、未選択、missing result は Always source の Selection を変更しない。複数 source が同じ physical file を選ぶこと自体は source ごとの Selection result を変更せず、Archive path collision と generated README の overlap semantics だけに従う。"""

        level @= MUST
        related @= (SELECTION_SPEC.SPEC_065,)

    class SPEC_101:
        r"""Archive root の root-level `README.md` は dirpluck が生成する index 用の予約 path とする。Resolved source の final archive root の先頭 component が case-insensitive に `README.md` と一致する場合は error とし、その下へ source tree を配置しない。この規則は Namespace 名だけでなく、Namespace を使わない source root にも同じように適用する。"""

        level @= MUST

    class SPEC_102:
        r"""Archive root には{{TERM_10}}を `README.md` として生成する。これは archive contents の index であり、dirpluck の resolution report ではない。Effective `[about].description` が存在する場合は Archive 全体の説明として含め、存在しない場合は全体説明を省略できる。Markdown の heading level、punctuation、空行などの細かな presentation は互換性契約に含めない。"""

        merge @= TERMS.TERM_10
        level @= MUST

    class SPEC_103:
        r"""Generated README は Always source を Target より先に表し、各 source / group の description を file-count、source-path、overlap などの補助 metadata より先に読める形で配置する。Target は Scope ごとにまとめ、Scope identity と `scope.description` を group context として示す。Directory Target はその Scope の Pluck group 配下に final archive root と selected file 数を示し、同一 Scope 内では Scope / Pluck selection `description` を Target ごとに繰り返さない。File Target は Pluck を使わないため Scope group 直下で atomic source として示す。Always source は final archive root と自身の selection `description` を示す。Description の複数行内容は保持する。Heading level、inline-code 表記、label、空行などの細かな presentation は互換性契約に含めない。"""

        level @= MUST

    class SPEC_104:
        r"""Always source が実際に選択した physical file と Target が実際に選択した physical file に重複がある場合、生成 README は重複 file 数と対応する Target の final archive root を識別できる情報を含める。同じ physical file が Target 側で `ignore` されるなどして実際には選択されていない場合は overlap に数えない。この情報は physical overlap の説明であり、Selection や Archive placement を変更しない。Label や表示形式は互換性契約に含めない。"""

        level @= MUST
        condition @= "Always source と Target が同じ physical file を選択した場合"

    class SPEC_106:
        r"""Target grouping のため Scope identity と directory Target の Pluck context は README に記録できる。Scope identity は Target の選択範囲だけを表し、優先度・重要度・Target 間の階層関係を意味しないことを README 自身で説明する。Scope に追加の意味がある場合は `scope.description` がその意味を与える。選択した Pluck Case 名、Configuration path / table、base chain など実行 provenance は既定では記録しない。Physical overlap の識別には Target reference ではなく final archive root を使用する。Source filesystem path は既定では記録せず、CLI `--paths` が指定された場合だけ、各 source に対応する解決済み source filesystem path を `/` separator で README に含める。Directory source では directory path、file Target では file path を対象とする。`--paths` は archive path や selection を変更しない。表示 label や配置は互換性契約に含めない。"""

        level @= MUST
        condition @= "CLI `--paths` が指定された場合"
        related @= (FILESYSTEM_SPEC.SPEC_093,)
