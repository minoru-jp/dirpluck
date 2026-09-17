<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `_internal/document_source/dirpluck_docs/changelog/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `_internal/document_build/ja/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck CHANGELOG

dirpluck のリリースごとの変更履歴。

## 0.1.0

最初の公開リリース。

### Added

- 出力定義に固定出力と動的命名出力の2形式を設ける。動的命名では `directory`、`timestamp = true`、任意の `prefix` / `suffix` から `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` を生成し、通常実行では既存の同名出力を拒否する。`--sequence N` で呼び出し側が正の整数を明示できるが、自動採番、自動リネーム、上書きは行わない。非同期・並列実行の競合調停は行わず、同じ出力 path への並行書き込みは呼び出し側が避ける。
- README と `CONFIGURATION.md` で、ディレクトリを選択すると配下を再帰的に収集し、`.env`、秘密鍵、`.git` などを秘密情報として推論・自動除外しない責任境界を明示する。広い選択では用途に応じた `exclude` を設定する。
- `README.md` を具体的な利用例と反復可能なファイル集合の価値を中心に再構成し、TOML の書き方を `CONFIGURATION.md`、厳密な動作意味論を `SPECIFICATION.md` へ分離する。
- アーカイブ・ルートのアーカイブREADMEを用途中立の索引に限定する。固定文言から生成ツール名と下流用途の説明を除き、具体的な用途は各対象・コンパニオンの `description` に委ねる。
- ひとつの設定ファイルをひとつの抽出意図として扱い、省略可能な runtime-bound 対象定義と0個以上の固定コンパニオンの少なくとも一方、必須の出力定義から ZIP アーカイブを生成できるようにする。対象を定義する場合は同じ対象規則へ CLI から1個以上のディレクトリを与えられ、TOML の対象定義自体は1個のままにする。対象を持たない設定は位置引数なしで実行し、その設定へ `DIRECTORY` を渡すことはエラーにする。抽出条件は各 source へ直接記述し、名前付きの共有抽出規則やバンドル参照を持たない。
- ケースを設定ファイル全体で1個だけ有効になる平坦な名前付き selection variation として一般化する。対象がある場合は `[target.case.<name>]` が選択ケースを必ず定義し、各コンパニオンは同名の `[companion.<name>.case.<name>]` があれば使い、なければ base へフォールバックする。対象がない場合は少なくとも1個のコンパニオンがケースを定義する。ケース定義は完全な選択で継承・merge せず、source 構成、コンパニオン path、出力方針は変更しない。ケースの組み合わせと多階層化も拒否する。
- `include` と `include_if_exists` で階層数を明示した相対パスを指定し、各パス要素に最大1個の `*` を使って同一階層の実体名だけを可変にできるようにする。`include` は一致を必須とし、`include_if_exists` は0件一致を許容する。`**` による任意深度検索は提供しない。
- `exclude` で、選択済み範囲のファイル名またはディレクトリ名に対する exact / prefix / suffix / contains の限定された除外フィルタを提供する。
- `if_empty` の既定値を `error` とし、`include_if_exists` だけを持つ対象またはコンパニオンでは `allow` を明示して0件の最終選択を正常として扱えるようにする。空を許したディレクトリはアーカイブへ空ディレクトリとして保持できる。
- `--dry-run` で ZIP を作成せず生成予定の構成を tree 形式で表示する。不足する `include` は `[missing]`、不足する `include_if_exists` は `[optional missing]` として表示し、空結果の方針も可視化する。
- 処理対象を実行時のカレントディレクトリ内に限定し、シンボリックリンクによる対象外への逸脱を拒否する。対象には cwd 自体も指定でき、その場合もアーカイブ内では cwd の実ディレクトリ名を保持する。
- 各対象ケースとコンパニオンに `description` を必須化し、アーカイブルートへアーカイブREADMEを自動生成する。同じ実ディレクトリが複数の目的から要求された場合はファイルを実パスで合成し、README にそれぞれの目的を併記する。
- Python 3.11 以降を対象とし、MIT License で配布する。実行時のサードパーティ依存は持たない。
- PyPI 配布物の内容を明示する。wheel には実行コードと公開 `README.md` / `CONFIGURATION.md` / `GLOSSARY.md` / `SPECIFICATION.md` を収録し、sdist にはさらに tests と公開文書を含める。`_internal/` と `.github/` はリポジトリ専用とし、配布物には含めない。
- CLI の通常形を `dirpluck DIRECTORY [DIRECTORY ...]` とし、`build` サブコマンドを廃止する。設定ファイルは cwd と `./dirpluck/` の直下だけから探索し、既定では `dirpluck.toml`、`--config NAME` 指定時は同名の TOML を両方の場所から探す。候補が複数なら暗黙に優先せず曖昧としてエラーにし、`--configs` で検出候補と競合を列挙できるようにする。
