from shikumi_devdoc.norms.changelog import FIXED, change, changelog_part, release


@changelog_part(order=10)
class CHANGELOG_PART:
    @release("0.9.1")
    class RELEASE_15:
        r'''Target と Always source が同じ physical material を独立した役割で含められるようにし、Archive planning と生成 README の重複表現を修正する。'''

        @change(FIXED)
        class CHANGE_1:
            r'''Target と Always source が同じ physical file を選択して異なる Archive path へ配置する場合に ambiguity error として拒否していた制約を解除する。Target の Pluck と Always source の Selection は physical overlap の有無にかかわらず独立して評価し、Target 側の `ignore` や未選択結果によって Always source を抑止しない。同じ archive path に異なる physical file が衝突する場合は引き続き error とし、同じ archive path に同じ physical file が重なる場合は1回だけ書き込む。Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合は、生成 Archive README の Always source section に Target 側の final Archive root と重複 file 数を表示する。'''
