from shikumi_devdoc.norms.vocabulary import canonical, glossary, preserve_spelling, term, title


@canonical
@title("dirpluck 用語集")
class VOCABULARY:
    r'''dirpluck の設計・実装・利用において共通の意味で用いる用語。'''

    @term("dirpluck")
    class TERM_1:
        r'''本ライブラリの名称。ルート設定ファイルに記述された抽出意図に従い、省略可能な CLI 束縛の対象定義を1個以上の実行時ディレクトリへ適用し、設定に固定されたコンパニオン、明示的にインポートした別の設定ファイルが宣言するコンパニオン、および import root 内でルート設定ファイルが追加定義するコンパニオンからファイルを選択して ZIP アーカイブを作成する。対象を持たずコンパニオンや設定インポートだけで構成することもできる。'''
        glossary @= True
        preserve_spelling @= True

    @term("設定ファイル")
    class TERM_2:
        r'''dirpluck の抽出意図を記述する TOML ファイル。0個または1個の対象定義、0個以上のコンパニオン、0個以上の名前付き共有パターン、0個以上の設定インポート、および出力定義から成る。CLI から直接選択された設定ファイルはルート設定ファイルとなり、process cwd を自身の source 用実行 root として最終出力を所有する。設定インポートの `root` はルート設定ファイル自身の所在ディレクトリからの相対 path として解決する。設定インポートから読み込まれた設定ファイルは解決された import `root` を実行 root とし、その設定が宣言するコンパニオンを再利用できるほか、ルート設定ファイルは `[import.<name>.companion.<name>]` で同じ import root 内に追加コンパニオンを定義できる。import 先の対象と出力定義は使用しない。設定内では1個の平坦なケース名だけを選択でき、ルート設定ファイルでは対象とコンパニオン、import 先ではコンパニオンの抽出選択を切り替えられる。共有パターンは同じ設定ファイル内で明示的に参照して再利用し、ケース継承や暗黙の merge には用いない。ルート設定ファイルの探索は cwd と `./dirpluck/` の直下だけで行い、同じファイル名が複数見つかった場合は曖昧としてエラーにする。'''
        glossary @= True

    @term("対象")
    class TERM_3:
        r'''設定ファイルが必要とするときだけ存在する runtime-bound source 定義。`[target]` に既定の抽出設定を直接記述でき、必要な場合だけ `[target.case.<name>]` に独立した名前付きケースを追加できる。対象には固定 `path` を設定せず、TOML に書く対象定義は最大1個のままにする。ルート設定ファイルとして実行された場合だけ CLI の `DIRECTORY` から1個以上のディレクトリを受け取り、同じ選択済み対象規則をすべてへ適用する。別の設定ファイルからインポートされた場合、その設定の対象定義は使用しない。対象を定義しないルート設定ファイルに対象ディレクトリを束縛することはできない。'''
        glossary @= True

    @term("ケース")
    class TERM_4:
        r'''設定ファイル全体で0個または1個だけ選択する平坦な名前付き抽出 variation。ルート設定ファイルで対象がある場合は `[target.case.<name>]` がそのケースを定義し、各コンパニオンは同名の `[companion.<name>.case.<name>]` があれば使い、なければ base 選択へフォールバックする。対象がないルート設定ファイル、または設定インポートで Case を指定する場合は、少なくとも1個の対象となるコンパニオンがそのケースを定義する必要がある。import 先の Target Case は使用しない。ケース定義は base との差分や継承ではなく完全な選択定義で、source の追加・削除、コンパニオン path、出力定義は変更しない。ケースの組み合わせや多階層化は行わない。'''
        glossary @= True

    @term("コンパニオン")
    class TERM_5:
        r'''設定ファイルの抽出意図に付随する固定 source。対象がある場合は対象に同伴し、対象がない場合はその目的自体に付随する。通常は `[companion.<name>]` に、その設定ファイルへ割り当てられた実行 root 相対の固定 `path`、目的説明、および base の選択定義を直接記述する。ルート設定ファイルは `[import.<import-name>.companion.<name>]` によって import root 内へ追加コンパニオンを定義でき、その場合も source は Target ではなく Companion のままである。必要なら対応する `.case.<case-name>` に完全な代替選択を追加でき、選択されたケースが存在しないコンパニオンは base へフォールバックする。'''
        glossary @= True

    @term("対象ディレクトリ")
    class TERM_6:
        r'''抽出を行う実際のディレクトリ。ルート設定ファイルの対象は存在する場合に CLI から1個以上与えられ、すべて同じ対象定義を使う。コンパニオンはルート設定ファイル、import 先設定、または `[import.<name>.companion.<name>]` の固定 `path` から決定される。使用される source ディレクトリはいずれも、その source を解決する設定ファイルへ割り当てられた実行 root 内に存在しなければならず、シンボリックリンクを利用した外部への逸脱も拒否する。ルート設定ファイルの対象には process cwd 自体を `.` として指定でき、その場合もアーカイブでは cwd の実ディレクトリ名を保持する。'''
        glossary @= True

    @term("抽出")
    class TERM_7:
        r'''対象またはコンパニオンからアーカイブへ含めるファイルを確定し、ルート設定ファイル自身の対象・コンパニオンと、各設定インポート名前空間に属する import 先設定由来またはルート追加のコンパニオン結果をひとつのアーカイブ計画へ統合する処理。`include` は存在を必須とする相対パス、`include_if_exists` は存在する場合だけ追加する任意候補、`exclude` は選択済み範囲に適用する限定的な名前フィルタである。これらは選択定義へ直接記述できるほか、include 用または exclude 用の共有パターンを同じ設定ファイル内から明示的に参照して追加できる。include 用の共有パターンは `include_pattern_refs` または `include_if_exists_pattern_refs`、exclude 用は `exclude_pattern_refs` から参照し、include 用を必須候補または任意候補のどちらとして扱うかは選択側で決める。少なくとも直接記述または共有パターン参照による `include` / `include_if_exists` 相当の候補の一方が必要で、`if_empty = "allow"` は必須候補を持たない場合だけ指定できる。'''
        glossary @= True

    @term("アーカイブ")
    class TERM_8:
        r'''dirpluck が生成する ZIP 成果物。選択されたファイルは、そのファイルを選択した設定ファイルへ割り当てられた実行 root から見た実際の相対パスを保持し、ルートには dirpluck が生成する `README.md` を置く。複数の source または設定インポートが同じアーカイブ path へ同じ実ファイルを選んだ場合は1回だけ書き込み、同じアーカイブ path が異なる実ファイルへ解決される場合や、同じ実ファイルが異なるアーカイブ path へ解決される場合は曖昧として拒否する。'''
        glossary @= True

    @term("出力定義")
    class TERM_9:
        r'''`[output]` に記述する必須設定。ルート設定ファイルの出力定義だけが一回の実行の最終出力として使用され、インポートされた設定ファイル自身の出力定義は使用しない。固定出力ではルート設定ファイルの実行 root である cwd 相対 `path` と `if_exists = "error" | "overwrite"`、動的命名出力では `directory` と `timestamp = true`、任意の `prefix` / `suffix` を記述する。動的命名は実行ごとに時刻を含む ZIP 名を作り、確認時点で同名出力があればエラーとする。必要なら CLI の `--sequence N` で timestamp 直後へ明示的な番号を加えられるが、自動採番、同じ出力 path への並行書き込みの調停、出力形式の一時 override は行わない。'''
        glossary @= True

    @term("アーカイブREADME")
    class TERM_10:
        r'''アーカイブのルート `README.md` として生成する用途中立の索引文書。ルート設定ファイル、設定インポート、選択されたケース、各設定に割り当てられた実行 root、実際に含まれたディレクトリ、対象または論理名で識別したコンパニオンの description、選択された設定位置、ディレクトリ決定方法、選択ファイル数、必要に応じて空結果方針を機械的に記録する。固定文言では生成ツール名や下流用途を示さず、具体的な用途は設定された description に委ねる。同じ実ディレクトリに複数の役割が重なった場合は、そのディレクトリを一度だけ索引し各役割を個別に記録する。'''
        glossary @= True


    @term("0.3.0")
    class TERM_11:
        r'''この文書群が対象とするリリースのバージョン。README ではバージョン番号を直接記述せず、この語彙から差し込む。'''
        preserve_spelling @= True

    @term("共有パターン")
    class TERM_12:
        r'''同じ設定ファイル内の複数の選択定義から明示的に再利用する名前付きパターン集合。include 用は `[shared.include_patterns]`、exclude 用は `[shared.exclude_patterns]` に `name = [...]` の形で定義し、それぞれ対応するパターン文法で検証する。選択定義は `include_pattern_refs`、`include_if_exists_pattern_refs`、`exclude_pattern_refs` から共有パターン名を参照して自身の直接記述へ追加し、参照していない共有パターンは適用されない。共有パターンはケース継承、暗黙の merge、source 間の自動適用を行わない。'''
        glossary @= True

    @term("設定インポート")
    class TERM_13:
        r'''ルート設定ファイルから別の dirpluck 設定ファイルを名前付きで明示的に読み込み、その設定が宣言するコンパニオンと、ルート側が同じ import root 内へ追加定義するコンパニオンの抽出結果を同じアーカイブ計画へ統合する仕組み。`[import.<name>]` に、ルート設定ファイル自身の所在ディレクトリからの相対 path で import 用の実行 `root` を指定し、その root 内の `configuration`、必要に応じて `case`、0個以上の `[import.<name>.companion.<companion-name>]` を記述する。import 名は名前空間となり、その配下のコンパニオンの論理名は `<import>.<companion>` とする。import 先設定由来とルート追加で同じ論理名を定義することはできない。`root` は絶対 path を受け付けず、Configuration 群の相対的な位置関係として保持する。import 先設定由来のコンパニオンは import 先の共有パターン、ルート追加コンパニオンはルート設定ファイルの共有パターンを使い、両者を merge しない。import 先の Target と `[output]` は使用しない。各 import 名前空間には少なくとも1個のコンパニオンが必要である。0.3.0 では設定インポートを記述できるのはルート設定ファイルだけで、インポートされた設定ファイルからさらに設定をインポートする再帰構成は許可しない。'''
        glossary @= True

    @term("ルート設定ファイル")
    class TERM_14:
        r'''一回の dirpluck 実行を開始する設定ファイル。CLI の通常の設定探索または `--config NAME` で選択され、process cwd を自身の source 用実行 root とし、CLI の `DIRECTORY` と `--case` を自身の対象・コンパニオンへ束縛する。設定インポートの `root` は process cwd ではなく、この設定ファイル自身の所在ディレクトリからの相対 path として解決する。0個以上の設定インポートを宣言し、別設定のコンパニオンを再利用したり import root 内へ追加コンパニオンを定義したりでき、一回の実行で有効になる最終 `[output]` を所有する。インポートされた設定ファイルの Target、出力定義、Case を暗黙に継承・伝播しない。'''
        glossary @= True
