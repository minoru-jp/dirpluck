from shikumi_devdoc.norms.vocabulary import canonical, glossary, preserve_spelling, term, title


@canonical
@title("dirpluck 用語集")
class VOCABULARY:
    r'''dirpluck の文書と実装で共通して使う概念を定義する。ここでは語の意味だけを定め、個数制約、解決順序、エラー条件などの仕様は定義しない。'''

    @term("dirpluck")
    class TERM_1:
        r'''宣言された抽出意図に従って source からファイルを選び、ZIP アーカイブを作成する CLI ツール。'''
        glossary @= True
        preserve_spelling @= True

    @term("設定ファイル")
    class TERM_2:
        r'''dirpluck の抽出意図を TOML で記述した文書。'''
        glossary @= True

    @term("対象")
    class TERM_3:
        r'''実行時に選ぶ source directory へ共通の選択規則を適用するための source 定義。'''
        glossary @= True

    @term("ターゲットロケーション")
    class TERM_16:
        r'''直下のディレクトリを実行時の対象として選ぶため、基準として名前を付けたディレクトリ。'''
        glossary @= True

    @term("ケース")
    class TERM_4:
        r'''base とは別の抽出 variation として名前を付けた選択定義。'''
        glossary @= True

    @term("コンパニオン")
    class TERM_5:
        r'''設定ファイルに source directory を固定し、同じ抽出意図へ付随させる source 定義。'''
        glossary @= True

    @term("対象ディレクトリ")
    class TERM_6:
        r'''対象またはコンパニオンに対応し、実際にファイルを抽出するディレクトリ。'''
        glossary @= True

    @term("抽出")
    class TERM_7:
        r'''source directory からアーカイブへ含めるファイルを選択規則に従って確定する処理。'''
        glossary @= True

    @term("アーカイブ")
    class TERM_8:
        r'''dirpluck が抽出結果から生成する ZIP 成果物。'''
        glossary @= True

    @term("出力定義")
    class TERM_9:
        r'''生成するアーカイブの出力先と命名方針を記述する設定。'''
        glossary @= True

    @term("アーカイブREADME")
    class TERM_10:
        r'''アーカイブのルートに生成され、含まれる内容を示す索引文書。'''
        glossary @= True

    @term("共有パターン")
    class TERM_12:
        r'''選択定義から参照して再利用する、名前付きの include または exclude パターン集合。'''
        glossary @= True

    @term("設定インポート")
    class TERM_13:
        r'''別の設定ファイルを内側の layer として取り込み、定義を組み合わせる仕組み。'''
        glossary @= True

    @term("ルート設定ファイル")
    class TERM_14:
        r'''1回の dirpluck 実行を開始する最外側の設定ファイル。'''
        glossary @= True

    @term("実効設定")
    class TERM_15:
        r'''ルート設定ファイルと設定インポートを解決し、1回の実行に使用する形へ構成した設定。'''
        glossary @= True
