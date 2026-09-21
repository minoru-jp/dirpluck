from shikumi_devdoc.norms.vocabulary import canonical, glossary, preserve_spelling, term, title


@canonical
@title("dirpluck 用語集")
class VOCABULARY:
    r'''dirpluck の文書と実装で共通して使う概念を定義する。ここでは語の意味だけを定め、個数制約、解決順序、path の基準、CLI 文法、validation、error 条件などの仕様は定義しない。'''

    @term("dirpluck")
    class TERM_1:
        r'''宣言された抽出意図に従って source から file を選び、ZIP Archive を作成する tool。CLI と最小の Python API を利用入口として持つ。'''
        glossary @= True
        preserve_spelling @= True

    @term("設定ファイル")
    class TERM_2:
        r'''dirpluck の抽出意図と、その意図に必要な source、selection、output などを TOML syntax で記述し、`.dirpluck` 拡張子で識別する文書。'''
        glossary @= True

    @term("対象")
    class TERM_3:
        r'''実行時にスコープから選ばれ、pluck の selection が適用される source directory。'''
        glossary @= True

    @term("ケース")
    class TERM_4:
        r'''同じ source に対して base selection とは別の抽出 variation を表す、名前付きの selection。'''
        glossary @= True

    @term("常時ソース")
    class TERM_5:
        r'''Configuration に source directory を固定し、実行のたびに同じ抽出意図へ参加させる source definition。'''
        glossary @= True

    @term("ソース")
    class TERM_6:
        r'''1回の実行で file selection の対象となる filesystem directory。対象と常時ソースは、source が実行へ参加する方法の違いを表す。'''
        glossary @= True

    @term("選択")
    class TERM_7:
        r'''source から Archive に含める file を、宣言された pattern と policy に従って決めること、またはそのための定義。'''
        glossary @= True

    @term("アーカイブ")
    class TERM_8:
        r'''dirpluck が selection result から生成する ZIP artifact。'''
        glossary @= True

    @term("出力定義")
    class TERM_9:
        r'''生成する Archive の書き込み先と命名方法を宣言する Configuration definition。'''
        glossary @= True

    @term("アーカイブREADME")
    class TERM_10:
        r'''Archive の root に生成され、含まれる source と内容を示す index document。'''
        glossary @= True

    @term("pluck")
    class TERM_11:
        r'''今回の実行で選ばれた対象から何を取り出すかを表す selection definition。'''
        glossary @= True
        preserve_spelling @= True

    @term("共有パターン")
    class TERM_12:
        r'''複数の selection から名前で参照して再利用する pattern set。'''
        glossary @= True

    @term("基底設定ファイル")
    class TERM_13:
        r'''別の Configuration が自身の基礎として参照し、その definition を引き継いで構成する Configuration file。'''
        glossary @= True

    @term("ルート設定ファイル")
    class TERM_14:
        r'''1回の dirpluck 実行で CLI から選ばれる最外側の Configuration file。'''
        glossary @= True

    @term("実効設定")
    class TERM_15:
        r'''ルート設定ファイルとその base chain を解決し、1回の実行に使用する形へ構成した Configuration。'''
        glossary @= True

    @term("スコープ")
    class TERM_16:
        r'''実行時に対象を探す filesystem 上の範囲。'''
        glossary @= True

    @term("書き込み境界")
    class TERM_17:
        r'''ひとつの output definition が Archive を書き込める filesystem 上の範囲として、Configuration から静的に定まる境界。'''
        glossary @= True

    @term("ネームスペース")
    class TERM_18:
        r'''source を Archive 内で区別して配置するために、source root の外側へ追加する Archive 専用の名前空間。'''
        glossary @= True

    @term("Invocation Template")
    class TERM_19:
        r'''Configuration、CLI Target reference、Case などの実行入力を、再利用可能な呼び出しとして保存する `.dirpluck-inv` document。'''
        glossary @= True
        preserve_spelling @= True
