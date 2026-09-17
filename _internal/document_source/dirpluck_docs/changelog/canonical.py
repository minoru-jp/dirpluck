from shikumi_devdoc.norms.changelog import ADDED, canonical, change, changelog, release, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@changelog("dirpluck CHANGELOG")
class CHANGELOG:
    r'''{{TERM_1}} のリリースごとの変更履歴。'''
    vocabulary_refs @= (terms.TERM_1,)

    @release("0.1.0")
    class RELEASE_1:
        r'''最初の公開リリース。'''

        @change(ADDED)
        class CHANGE_1:
            r'''ひとつの{{TERM_2}}をひとつの抽出意図として扱い、省略可能な runtime-bound {{TERM_3}}定義と0個以上の固定{{TERM_5}}の少なくとも一方、必須の{{TERM_9}}から ZIP {{TERM_8}}を生成できるようにする。対象を定義する場合は同じ対象規則へ CLI から1個以上のディレクトリを与えられ、TOML の対象定義自体は1個のままにする。対象を持たない設定は位置引数なしで実行し、その設定へ `DIRECTORY` を渡すことはエラーにする。抽出条件は各 source へ直接記述し、名前付きの共有抽出規則やバンドル参照を持たない。'''
            vocabulary_refs @= (terms.TERM_2, terms.TERM_3, terms.TERM_5, terms.TERM_8, terms.TERM_9)

        @change(ADDED)
        class CHANGE_2:
            r'''{{TERM_4}}を設定ファイル全体で1個だけ有効になる平坦な名前付き selection variation として一般化する。対象がある場合は `[target.case.<name>]` が選択ケースを必ず定義し、各コンパニオンは同名の `[companion.<name>.case.<name>]` があれば使い、なければ base へフォールバックする。対象がない場合は少なくとも1個のコンパニオンがケースを定義する。ケース定義は完全な選択で継承・merge せず、source 構成、コンパニオン path、出力方針は変更しない。ケースの組み合わせと多階層化も拒否する。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_4)

        @change(ADDED)
        class CHANGE_3:
            r'''`include` と `include_if_exists` で階層数を明示した相対パスを指定し、各パス要素に最大1個の `*` を使って同一階層の実体名だけを可変にできるようにする。`include` は一致を必須とし、`include_if_exists` は0件一致を許容する。`**` による任意深度検索は提供しない。'''

        @change(ADDED)
        class CHANGE_4:
            r'''`exclude` で、選択済み範囲のファイル名またはディレクトリ名に対する exact / prefix / suffix / contains の限定された除外フィルタを提供する。'''

        @change(ADDED)
        class CHANGE_5:
            r'''`if_empty` の既定値を `error` とし、`include_if_exists` だけを持つ対象またはコンパニオンでは `allow` を明示して0件の最終選択を正常として扱えるようにする。空を許したディレクトリは{{TERM_8}}へ空ディレクトリとして保持できる。'''
            vocabulary_refs @= (terms.TERM_8,)

        @change(ADDED)
        class CHANGE_6:
            r'''`--dry-run` で ZIP を作成せず生成予定の構成を tree 形式で表示する。不足する `include` は `[missing]`、不足する `include_if_exists` は `[optional missing]` として表示し、空結果の方針も可視化する。'''

        @change(ADDED)
        class CHANGE_7:
            r'''処理対象を実行時のカレントディレクトリ内に限定し、シンボリックリンクによる対象外への逸脱を拒否する。{{TERM_3}}には cwd 自体も指定でき、その場合も{{TERM_8}}内では cwd の実ディレクトリ名を保持する。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_8)

        @change(ADDED)
        class CHANGE_8:
            r'''各{{TERM_3}}ケースと{{TERM_5}}に `description` を必須化し、{{TERM_8}}ルートへ{{TERM_10}}を自動生成する。同じ実ディレクトリが複数の目的から要求された場合はファイルを実パスで合成し、README にそれぞれの目的を併記する。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_5, terms.TERM_8, terms.TERM_10)

        @change(ADDED)
        class CHANGE_9:
            r'''Python 3.11 以降を対象とし、MIT License で配布する。実行時のサードパーティ依存は持たない。'''

        @change(ADDED)
        class CHANGE_10:
            r'''PyPI 配布物の内容を明示する。wheel には実行コードと公開 `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md` を収録し、sdist にはさらに tests と公開文書を含める。`_internal/` と `.github/` はリポジトリ専用とし、配布物には含めない。'''

        @change(ADDED)
        class CHANGE_11:
            r'''CLI の通常形を `dirpluck DIRECTORY [DIRECTORY ...]` とし、`build` サブコマンドを廃止する。{{TERM_2}}は cwd と `./dirpluck/` の直下だけから探索し、既定では `dirpluck.toml`、`--config NAME` 指定時は同名の TOML を両方の場所から探す。候補が複数なら暗黙に優先せず曖昧としてエラーにし、`--configs` で検出候補と競合を列挙できるようにする。'''
            vocabulary_refs @= (terms.TERM_2,)
        @change(ADDED)
        class CHANGE_12:
            r'''`README.md` を具体的な利用例と反復可能なファイル集合の価値を中心に再構成し、TOML の書き方を `CONFIGURATION.md`、厳密な動作意味論を `SPECIFICATION.md` へ分離する。'''

        @change(ADDED)
        class CHANGE_13:
            r'''{{TERM_8}}ルートの{{TERM_10}}を用途中立の索引に限定する。固定文言から生成ツール名と下流用途の説明を除き、具体的な用途は各{{TERM_3}}・{{TERM_5}}の `description` に委ねる。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_5, terms.TERM_8, terms.TERM_10)

        @change(ADDED)
        class CHANGE_14:
            r'''{{TERM_9}}に固定出力と動的命名出力の2形式を設ける。動的命名では `directory`、`timestamp = true`、任意の `prefix` / `suffix` から `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` を生成し、通常実行では既存の同名出力を拒否する。`--sequence N` で呼び出し側が正の整数を明示できるが、自動採番、自動リネーム、上書きは行わない。非同期・並列実行の競合調停は行わず、同じ出力 path への並行書き込みは呼び出し側が避ける。'''
            vocabulary_refs @= (terms.TERM_9,)


        @change(ADDED)
        class CHANGE_15:
            r'''README と `CONFIGURATION.md` で、ディレクトリを選択すると配下を再帰的に収集し、`.env`、秘密鍵、`.git` などを秘密情報として推論・自動除外しない責任境界を明示する。広い選択では用途に応じた `exclude` を設定する。'''

