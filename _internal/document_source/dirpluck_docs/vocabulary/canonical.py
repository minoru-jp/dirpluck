from shikumi_devdoc.norms.vocabulary import canonical, glossary, preserve_spelling, term, title


@canonical
@title("dirpluck 用語集")
class VOCABULARY:
    r'''dirpluck の設計・実装・利用において共通の意味で用いる用語。'''

    @term("dirpluck")
    class TERM_1:
        r'''本ライブラリの名称。ルート設定ファイルから必要に応じて1本の設定インポート chain を解決し、各層の定義を内側から外側へ名前解決して得た実効設定に従って、対象またはコンパニオンからファイルを選択し ZIP アーカイブを作成する。'''
        glossary @= True
        preserve_spelling @= True

    @term("設定ファイル")
    class TERM_2:
        r'''dirpluck の抽出意図を記述する TOML ファイル。各ファイルは0個または1個の対象、0個以上のコンパニオン、0個以上の名前付き共有パターン、0個または1個の設定インポート、および出力定義を持てる。設定インポートがある場合は import 先を先に解決し、外側の同名定義で内側を shadow して実効設定を構成する。各設定ファイルで対象定義は最大1個のままで、設定インポートの深さに上限は設けず、循環参照だけを拒否する。'''
        glossary @= True

    @term("対象")
    class TERM_3:
        r'''設定ファイルごとに最大1個だけ定義できる主 source。`[target]` に base 選択、必要に応じて `[target.case.<name>]` に独立した Case 選択を記述する。設定 chain では外側の Target 定義が内側の Target 定義全体を shadow し、最終的に1個以下の Target が実効設定へ残る。ルート設定ファイル自身の Target が残る場合は CLI の `DIRECTORY` を束縛し、import 由来 Target が残る場合はその Target を所有する Configuration の project directory を対象ディレクトリとして解決する。'''
        glossary @= True

    @term("ケース")
    class TERM_4:
        r'''実効設定全体で0個または1個だけ選択する平坦な名前付き抽出 variation。Case 定義は base との差分や継承ではなく完全な選択定義である。設定 chain の名前解決では Target や Companion が外側で shadow された場合、その source に属する Case 定義もまとめて置き換わる。最終的な実効設定に対して CLI の `--case` を1個だけ適用し、対象が同名 Case を持つ場合はそれを必須とし、各コンパニオンは同名 Case があれば使い、なければ base へフォールバックする。'''
        glossary @= True

    @term("コンパニオン")
    class TERM_5:
        r'''設定ファイルの抽出意図に付随する固定 source。通常は `[companion.<name>]` に、その定義を所有する設定層の execution root 相対 `path`、説明、base 選択を記述する。設定 chain では同名 Companion を外側で定義すると内側の Companion 定義全体を shadow し、異なる名前は共存する。`[import.<name>.companion.<name>]` は直下の import root を基準にする Companion overlay で、同じ名前解決規則へ参加する。'''
        glossary @= True

    @term("対象ディレクトリ")
    class TERM_6:
        r'''抽出を行う実際のディレクトリ。実効 Target がルート設定ファイル自身に由来する場合は CLI から1個以上与えられる。実効 Target が import chain の内側に由来する場合は、その Target を定義した Configuration の project directory から1個の対象ディレクトリを決定する。コンパニオンは定義を所有する設定層または import root overlay の固定 `path` から決定する。いずれも対応する filesystem boundary 内へ解決されなければならない。'''
        glossary @= True

    @term("抽出")
    class TERM_7:
        r'''実効設定の対象またはコンパニオンからアーカイブへ含めるファイルを確定する処理。`include` は存在必須の候補、`include_if_exists` は任意候補、`exclude` は選択済み範囲への限定的な名前フィルタである。共有パターン参照は実効設定の include / exclude 名前空間から解決し、設定 chain の外側に同名共有パターンがあれば内側の定義を shadow する。最終的に参照名が解決できない場合は設定エラーとする。'''
        glossary @= True

    @term("アーカイブ")
    class TERM_8:
        r'''dirpluck が生成する ZIP 成果物。選択されたファイルは、その source 定義に対応する execution root から見た実際の相対 path を保持し、ルートには dirpluck が生成する `README.md` を置く。同じ archive path に同じ実ファイルが重なる場合は1回だけ書き込み、異なる実ファイルの path 衝突や、同じ実ファイルが異なる archive path へ解決される曖昧さは拒否する。'''
        glossary @= True

    @term("出力定義")
    class TERM_9:
        r'''`[output]` に記述する設定。1回の実行で使用するのは最外側のルート設定ファイルの出力定義だけで、import chain 内側の出力定義は実行しない。固定出力では cwd 相対 `path` と `if_exists = "error" | "overwrite"`、動的命名出力では `directory`、`timestamp = true`、任意の `prefix` / `suffix` を記述する。'''
        glossary @= True

    @term("アーカイブREADME")
    class TERM_10:
        r'''アーカイブのルート `README.md` として生成する用途中立の索引文書。解決した Configuration chain、各 execution root、実効 Target / Companion、選択された Case、description、選択件数など、解決済み計画の事実を記録する。具体的な用途は設定された description に委ねる。'''
        glossary @= True

    @term("共有パターン")
    class TERM_12:
        r'''設定ファイル内で名前を付けて定義し、選択定義から明示的に参照する再利用可能なパターン集合。include 用は `[shared.include_patterns]`、exclude 用は `[shared.exclude_patterns]` に `name = [...]` として定義する。設定 chain では include / exclude を別々の名前空間として内側から外側へ解決し、外側の同名定義が内側を shadow する。Selection の参照名は最終的な実効名前空間で解決し、参照していない共有パターンは適用しない。'''
        glossary @= True

    @term("設定インポート")
    class TERM_13:
        r'''別の dirpluck 設定ファイルを1段内側の設定層として読み込む仕組み。各設定ファイルは `[import.<name>]` を0個または1個だけ持てる。`root` はその設定ファイル自身の所在ディレクトリからの相対 path、`configuration` は解決した import root 内の相対 TOML path とする。import 先もさらに1個だけ import でき、chain の長さに上限は設けない。解決済み Configuration file が現在の chain に再登場した場合は循環参照として拒否する。import 名は link の識別と診断に使い、複数 import を同じ層で構成する namespace graph は作らない。'''
        glossary @= True

    @term("ルート設定ファイル")
    class TERM_14:
        r'''1回の dirpluck 実行を開始する最外側の設定ファイル。CLI の通常探索または `--config NAME` で選択され、process cwd を自身の execution root とする。0個または1個の設定インポートを持ち、import chain を解決して実効設定を作る。最終 `[output]` を所有し、実効 Target が自身の定義である場合だけ CLI の `DIRECTORY` を束縛する。'''
        glossary @= True

    @term("実効設定")
    class TERM_15:
        r'''設定インポート chain を最深部から最外側へ順に重ね、同名定義を外側で shadow して得る1回の実行用 Configuration。Target は最終的に最大1個、Companion は名前ごとに最大1個、共有 include / exclude パターンは各名前空間で名前ごとに最大1個へ解決される。Source 定義は shadow された場合に base と Case を含む定義全体が置き換わり、共有パターン参照はこの実効名前空間で最終解決する。出力だけは layering の対象にせず、ルート設定ファイルの定義を使用する。'''
        glossary @= True
