from shikumi_devdoc.norms.vocabulary import canonical, glossary, preserve_spelling, term, title


@canonical
@title("dirpluck 用語集")
class VOCABULARY:
    r'''dirpluck の設計・実装・利用において共通の意味で用いる用語。'''

    @term("dirpluck")
    class TERM_1:
        r'''本ライブラリの名称。設定ファイルに記述されたひとつの抽出意図に従い、省略可能な CLI 束縛の対象定義を1個以上の実行時ディレクトリへ適用し、または設定に固定されたコンパニオンからファイルを選択して ZIP アーカイブを作成する。対象を持たずコンパニオンだけで構成することもできる。'''
        glossary @= True
        preserve_spelling @= True

    @term("設定ファイル")
    class TERM_2:
        r'''dirpluck の一回の実行で実現するひとつの抽出意図を記述する TOML ファイル。0個または1個の対象定義、0個以上のコンパニオン、少なくとも1個の source、および出力定義から成る。設定内では1個の平坦なケース名だけを選択でき、対象とコンパニオンの抽出選択を同じケース名で切り替えられる。source の構成、コンパニオンの path、出力方針まで変える場合は別の設定ファイルを用いる。設定探索は cwd と `./dirpluck/` の直下だけで行い、同じファイル名が複数見つかった場合は曖昧としてエラーにする。'''
        glossary @= True

    @term("対象")
    class TERM_3:
        r'''設定ファイルが必要とするときだけ存在する CLI 束縛の source 定義。`[target]` に既定の抽出設定を直接記述でき、必要な場合だけ `[target.case.<name>]` に独立した名前付きケースを追加できる。対象には固定 `path` を設定せず、TOML に書く対象定義は最大1個のままにする。対象を定義する設定では CLI の `DIRECTORY` が1個以上必須で、同じ選択済み対象規則をすべてへ適用する。対象を定義しない設定では `DIRECTORY` の指定を拒否する。'''
        glossary @= True

    @term("ケース")
    class TERM_4:
        r'''設定ファイル全体で0個または1個だけ選択する平坦な名前付き抽出 variation。対象がある場合は `[target.case.<name>]` がそのケースを定義し、各コンパニオンは同名の `[companion.<name>.case.<name>]` があれば使い、なければ base 選択へフォールバックする。対象がない場合は少なくとも1個のコンパニオンがそのケースを定義する必要がある。ケース定義は base との差分や継承ではなく完全な選択定義で、source の追加・削除、コンパニオン path、出力定義は変更しない。ケースの組み合わせや多階層化は行わない。'''
        glossary @= True

    @term("コンパニオン")
    class TERM_5:
        r'''設定ファイルの抽出意図に付随する固定 source。対象がある場合は対象に同伴し、対象がない場合はその目的自体に付随する。`[companion.<name>]` に cwd 相対の固定 `path`、目的説明、および base の選択定義を直接記述する。必要なら `[companion.<name>.case.<case-name>]` に同名ケース用の完全な代替選択を追加でき、選択されたケースが存在しないコンパニオンは base へフォールバックする。'''
        glossary @= True

    @term("対象ディレクトリ")
    class TERM_6:
        r'''抽出を行う実際のディレクトリ。対象は存在する場合に CLI から1個以上与えられ、すべて同じ対象定義を使う。コンパニオンは設定ファイルの固定 `path` から決定される。使用される source ディレクトリはいずれも存在し、実行時のカレントディレクトリ内に解決されなければならず、シンボリックリンクを利用した外部への逸脱も拒否する。対象には cwd 自体を指定でき、その場合もアーカイブでは cwd の実ディレクトリ名を保持する。'''
        glossary @= True

    @term("抽出")
    class TERM_7:
        r'''対象またはコンパニオンからアーカイブへ含めるファイルを確定する処理。`include` は存在を必須とする相対パス、`include_if_exists` は存在する場合だけ追加する任意候補、`exclude` は選択済み範囲に適用する限定的な名前フィルタである。少なくとも `include` または `include_if_exists` の一方が必要で、`if_empty = "allow"` は必須 `include` を持たない場合だけ指定できる。'''
        glossary @= True

    @term("アーカイブ")
    class TERM_8:
        r'''dirpluck が生成する ZIP 成果物。選択されたファイルは実行時のカレントディレクトリから見た実際の相対パスを保持し、ルートには dirpluck が生成する `README.md` を置く。複数の source が同じ実ディレクトリへ解決された場合は実パスでファイルを合成し、同じファイルを重複して書き込まない。'''
        glossary @= True

    @term("出力定義")
    class TERM_9:
        r'''`[output]` に記述する必須設定。固定出力では cwd 相対 `path` と `if_exists = "error" | "overwrite"`、動的命名出力では `directory` と `timestamp = true`、任意の `prefix` / `suffix` を記述する。動的命名は実行ごとに時刻を含む ZIP 名を作り、確認時点で同名出力があればエラーとする。必要なら CLI の `--sequence N` で timestamp 直後へ明示的な番号を加えられるが、自動採番、同じ出力 path への並行書き込みの調停、出力形式の一時 override は行わない。'''
        glossary @= True

    @term("アーカイブREADME")
    class TERM_10:
        r'''アーカイブのルート `README.md` として生成する用途中立の索引文書。選択されたケース、実際に含まれたディレクトリ、対象またはコンパニオンの description、選択された設定位置、ディレクトリ決定方法、選択ファイル数、必要に応じて空結果方針を機械的に記録する。固定文言では生成ツール名や下流用途を示さず、具体的な用途は設定された description に委ねる。同じ実ディレクトリに複数の役割が重なった場合は、そのディレクトリを一度だけ索引し各役割を個別に記録する。'''
        glossary @= True


    @term("0.1.0")
    class TERM_11:
        r'''現在の公開リリースのバージョン。README ではバージョン番号を直接記述せず、この語彙から差し込む。'''
        preserve_spelling @= True
