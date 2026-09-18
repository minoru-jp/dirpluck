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
正本は `dirpluck_docs/changelog/canonical.py` です。
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

## 0.4.1

現在のパッケージバージョンを `dirpluck.__version__` に一本化し、文書生成ではそこから生成した外部 JSON context を利用する。

### Added

- 現在のリリース番号を用語集の語彙として保持する方式を廃止する。文書生成用の外部 context JSON は `dirpluck.__version__` から生成し、README など現在バージョンを必要とする文書は `version` context 値を参照する。CHANGELOG の各リリース番号は履歴情報として canonical source に直接記述する。

## 0.4.0

import 先 Configuration の共有 include / exclude パターンを、import 名前空間付きで Root 側から明示的に再利用できるようにする。

### Added

- 設定インポートで読み込んだ Configuration の `[shared.include_patterns]` / `[shared.exclude_patterns]` を、ルート設定ファイル側から `<import-name>.<pattern-name>` の修飾名で参照できるようにする。Root local の共有パターンは従来どおりローカル名で参照し、include / exclude の種別は分離したまま維持する。
- import 由来の修飾共有パターンを、ルート設定ファイルが所有する Target、Root Companion、`[import.<name>.companion.<name>]` の base / Case Selection から利用できるようにする。import 先 Configuration 自身が宣言する Companion は、引き続きその Configuration 自身の共有パターンをローカル名で解決し、Root 側の名前空間へ再束縛しない。
- Root local の共有パターン名と import 由来の修飾共有パターン名が同じ参照文字列になる場合は、暗黙の優先順位を設けず設定エラーにする。共有パターンは import によって merge・自動適用されず、各 Selection が参照名を明示する既存モデルを維持する。

## 0.3.0

別ディレクトリの dirpluck Configuration が宣言する Companion を明示的に取り込み、各 Configuration の境界を保ったままひとつのアーカイブへ統合できるようにする。

### Added

- 設定インポートを導入する。ルート設定ファイルの `[import.<name>]` に `root`、`configuration`、必要に応じて `case` を記述し、別の dirpluck 設定ファイルが宣言する Companion の抽出結果を同じ archive plan へ統合できるようにする。Root Configuration はローカル source を持たず設定インポートだけで構成することもできる。
- 設定インポートの `root` を、ルート設定ファイルの cwd 境界を明示的に越えられる唯一の path として定義する。`root` はルート設定ファイル自身の所在ディレクトリからの相対 path に限定し、POSIX / Windows / UNC の絶対指定を OS にかかわらず拒否する。import root を解決した後は、`configuration`、import 先 Companion、選択ファイルをその root 内へ再び限定し、各 Configuration が独立した filesystem boundary を持つようにする。
- ルート設定ファイルの CLI `DIRECTORY` と `--case` を import 先へ暗黙に伝播させず、import 先の Target は使用しない。`case` は import 先 Companion 群だけへ独立して適用する。import 先設定の `[output]` は schema validation だけを行って実行時には使用せず、最終出力はルート設定ファイルの `[output]` だけとする。0.3.0 では import 先からさらに設定を import する再帰構成を拒否する。
- Archive path を、各ファイルを選択した Configuration の execution root から見た相対 path として統合する。同じ archive path に同じ物理ファイルが重なる場合は1回だけ格納し、異なる物理ファイルが同じ archive path へ衝突する場合、または同じ物理ファイルが異なる archive path へ解決される場合は曖昧としてエラーにする。アーカイブ README には使用した設定インポートと各 execution root を記録する。
- 設定インポートではルート設定ファイルから `[import.<name>.companion.<companion-name>]` を定義し、import root 内の追加 source を Target ではなく Companion として取り込めるようにする。import 配下の Companion は import 先設定由来か Root 側追加かにかかわらず `<import>.<companion>` の論理名を持ち、同じ import 内での重複を拒否する。Root 側追加 Companion は Root の shared pattern を、import 先設定由来 Companion は import 先の shared pattern を使用し、`path = "."` によって import root 自体を Companion として選べる。

## 0.2.0

共有パターンを導入し、抽出条件をケース間や source 間で明示的に再利用できるようにする。

### Added

- 共有パターンを導入する。`[shared.include_patterns]` と `[shared.exclude_patterns]` に `name = [...]` の形で名前付きパターン集合を定義し、対象またはコンパニオンの base / case 選択から `include_pattern_refs` / `include_if_exists_pattern_refs` / `exclude_pattern_refs` で明示的に参照できるようにする。共有パターンは参照した選択にだけ追加され、base から case への継承や暗黙の merge、source 間の自動適用は行わない。
- include 用の共有パターンは include のパターン文法で、exclude 用の共有パターンは exclude のパターン文法で検証する。include 用の共有パターンは `include_pattern_refs` から必須候補、`include_if_exists_pattern_refs` から任意候補として参照でき、exclude 用は `exclude_pattern_refs` から参照できる。いずれも直接記述した `include` / `include_if_exists` / `exclude` と併用できる。
- sdist をリリースの再構築・検証に使えるソース配布物として拡充し、従来の tests と公開文書に加えて `_internal/` の文書正本・日本語中間文書と `tools/` の同期・配布検証ツールを収録する。`_internal/`、`tools/`、tests、`.github/` は wheel へ含めない。
- 実行時に必要な操作規則を短く確認できる公開 `USAGE.md` を追加する。文書は正本から日本語中間文書を生成して英訳する既存フローで管理し、リポジトリルート、sdist、および wheel の `dirpluck/docs/USAGE.md` に収録する。wheel に同梱する文書は `USAGE.md` のみに整理し、`README.md`、`CONFIGURATION.md`、`GLOSSARY.md`、`SPECIFICATION.md` は sdist またはリポジトリで提供する。

## 0.1.0

最初の公開リリース。

### Added

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
- `README.md` を具体的な利用例と反復可能なファイル集合の価値を中心に再構成し、TOML の書き方を `CONFIGURATION.md`、厳密な動作意味論を `SPECIFICATION.md` へ分離する。
- アーカイブルートのアーカイブREADMEを用途中立の索引に限定する。固定文言から生成ツール名と下流用途の説明を除き、具体的な用途は各対象・コンパニオンの `description` に委ねる。
- 出力定義に固定出力と動的命名出力の2形式を設ける。動的命名では `directory`、`timestamp = true`、任意の `prefix` / `suffix` から `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` を生成し、通常実行では既存の同名出力を拒否する。`--sequence N` で呼び出し側が正の整数を明示できるが、自動採番、自動リネーム、上書きは行わない。非同期・並列実行の競合調停は行わず、同じ出力 path への並行書き込みは呼び出し側が避ける。
- README と `CONFIGURATION.md` で、ディレクトリを選択すると配下を再帰的に収集し、`.env`、秘密鍵、`.git` などを秘密情報として推論・自動除外しない責任境界を明示する。広い選択では用途に応じた `exclude` を設定する。
