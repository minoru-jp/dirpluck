from shikumi_devdoc.norms.common import canonical_source
from shikumi_devdoc.norms.vocabulary import preserve_spelling, vocabulary


@vocabulary
@canonical_source("dirpluck 用語集", filename="GLOSSARY.md", placeholders=False, heading="identity")
class TERMS:
    r'''dirpluck の文書と実装で共通して使う概念を定義する。ここでは語の意味だけを定め、個数制約、解決順序、path の基準、CLI 文法、validation、error 条件などの仕様は定義しない。'''

    class TERM_1:
        r"""
            {{dirpluck}}

            宣言された抽出意図に従って source から file を選び、ZIP Archive を作成する tool。CLI と最小の Python API を利用入口として持つ。
        """
        preserve_spelling @= True

    class TERM_2:
        r"""
            {{設定ファイル}}

            dirpluck の抽出意図と、その意図に必要な source、selection、output などを TOML syntax で記述し、`.dirpluck` 拡張子で識別する文書。
        """
    class TERM_3:
        r"""
            {{対象}}

            実行時にスコープから選ばれ、pluck の selection が適用される source directory。
        """
    class TERM_4:
        r"""
            {{ケース}}

            同じ source に対して base selection とは別の抽出 variation を表す、名前付きの selection。
        """
    class TERM_5:
        r"""
            {{常時ソース}}

            Configuration に source directory を固定し、実行のたびに同じ抽出意図へ参加させる source definition。
        """
    class TERM_6:
        r"""
            {{ソース}}

            1回の実行で file selection の対象となる filesystem directory。対象と常時ソースは、source が実行へ参加する方法の違いを表す。
        """
    class TERM_7:
        r"""
            {{選択}}

            source から Archive に含める file を、宣言された pattern と policy に従って決めること、またはそのための定義。
        """
    class TERM_8:
        r"""
            {{アーカイブ}}

            dirpluck が selection result から生成する ZIP artifact。
        """
    class TERM_9:
        r"""
            {{出力定義}}

            生成する Archive の書き込み先と命名方法を宣言する Configuration definition。
        """
    class TERM_10:
        r"""
            {{アーカイブREADME}}

            Archive の root に生成され、含まれる source と内容を示す index document。
        """
    class TERM_11:
        r"""
            {{pluck}}

            今回の実行で選ばれた対象から何を取り出すかを表す selection definition。
        """
        preserve_spelling @= True

    class TERM_12:
        r"""
            {{共有パターン}}

            複数の selection から名前で参照して再利用する pattern set。
        """
    class TERM_13:
        r"""
            {{基底設定ファイル}}

            別の Configuration が自身の基礎として参照し、その definition を引き継いで構成する Configuration file。
        """
    class TERM_14:
        r"""
            {{ルート設定ファイル}}

            1回の dirpluck 実行で CLI から選ばれる最外側の Configuration file。
        """
    class TERM_15:
        r"""
            {{実効設定}}

            ルート設定ファイルとその base chain を解決し、1回の実行に使用する形へ構成した Configuration。
        """
    class TERM_16:
        r"""
            {{スコープ}}

            実行時に対象を探す filesystem 上の範囲。
        """
    class TERM_17:
        r"""
            {{書き込み境界}}

            ひとつの output definition が Archive を書き込める filesystem 上の範囲として、Configuration から静的に定まる境界。
        """
    class TERM_18:
        r"""
            {{ネームスペース}}

            source を Archive 内で区別して配置するために、source root の外側へ追加する Archive 専用の名前空間。
        """
    class TERM_19:
        r"""
            {{Invocation Template}}

            Configuration、CLI Target reference、Case などの実行入力を、再利用可能な呼び出しとして保存する `.dirpluck-inv` document。
        """
        preserve_spelling @= True
