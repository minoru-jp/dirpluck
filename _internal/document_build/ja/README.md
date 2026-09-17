<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "0.2.0"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `_internal/document_source/dirpluck_docs/readme/canonical.py` です。
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

# dirpluck

dirpluck は、宣言されたファイル抽出意図を再現可能な ZIP アーカイブへ変換する CLI ツールです。「どのファイルを一緒に扱うか」が一度限りの手作業ではなく繰り返し現れる判断であるときに使えます。必要なファイルは1個のディレクトリにまとまっていても、複数の場所に分散していてもよく、実行ごとに変わるものと、同じ目的へ常に付随する固定資料を組み合わせることもできます。

その集合を記憶、シェル履歴、会話履歴、ローカルな慣習から毎回組み立て直す代わりに、一度 TOML へ記述します。後の実行では同じ宣言済み source を解決し、同じ選択規則を適用します。得られるものは周辺をすべて複製するバックアップではなく、明示した目的のために組み立てたパッケージです。

## dirpluck を使える場面

### 複数の場所に分散した関連資料をまとめる

ひとつの用途に必要な資料が、ひとつのルートへ保存されているとは限りません。提案資料なら `sales/` の文書、`research/` の調査結果、`legal/` の法務資料を一緒に必要とするかもしれません。定例会議の資料なら、ノート、レポート、参照資料がワークスペース内の別々の場所で管理されていることがあります。

dirpluck ではそれらを固定コンパニオンとして記述でき、実行時の対象を持たずにパッケージを生成できます。

```toml
[companion.proposal]
path = "sales/proposal"
description = "The proposal being prepared for delivery."
include = ["*.pdf"]

[companion.research]
path = "research"
description = "Research material supporting the proposal."
include = ["*.md", "data/*.csv"]

[output]
path = "artifacts/proposal-package.zip"
if_exists = "overwrite"
```

```console
dirpluck --config proposal-package
```

設定ファイルには、それらのディレクトリがなぜ一緒に扱われるのかを残せます。各ディレクトリに共通の「主ディレクトリ」を置く必要はありません。実行時の cwd 境界内にあれば、同じ目的へ付随する source として扱えます。

### 繰り返し使う作業資料を再構成する

同じ種類のファイル集合を繰り返し必要とするからこそ、固定しておく価値がある場合があります。週次レビュー、編集サイクル、調査、報告作業などでは、内容は変化しても毎回同じ種類の資料を必要とします。

設定ファイルにその選択を残せば、前回どのフォルダ、レポート、参照資料を使ったかを毎回探索し直す必要がありません。ワークスペースが変化したときは `--dry-run` で解決後のアーカイブ計画を確認してから生成できます。

### レビューや引き渡しに必要な範囲だけをまとめる

リポジトリや作業ディレクトリ全体を共有する必要があるとは限りません。レビューなら現在の文書、根拠資料、チェックリストが必要かもしれません。引き渡しなら成果物、運用メモ、選択した参照資料が必要かもしれません。コードレビューなら source、tests、依存ライブラリが必要になります。

dirpluck ではその境界を明示できます。必須資料は `include`、存在しないことが正常な既知候補は `include_if_exists` で分けられます。そのため必須資料の欠落は、「完成して見えるが不完全なパッケージ」を黙って作る代わりにエラーになります。

### 意味のあるスナップショットを残す

スナップショットは必ずしも「現在あるものを全部コピーする」ことではありません。調査、執筆、分析、制作、リリース準備などでは、現在の状態を説明する文書、選択した source data、意思決定、存在している生成物だけを残す方が有用な場合があります。

コンパニオンだけの設定ファイルはこの用途にそのまま使えます。固定 source がスナップショットを構成する範囲を定義し、任意選択を使えば、生成物が存在するときだけ含めても、その不在をエラーにする必要はありません。後で同じ設定を実行すれば、内容が変化していても同じ定義のスナップショットを再現できます。

蓄積するスナップショットでは、固定 path を上書きする代わりに、設定ファイルへ時刻ベースの動的命名を宣言できます。

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

実行ごとに `project-YYYYMMDD-HHMMSS.zip` のような新しい名前を作り、確認時点で同名出力が既に存在すればエラーにします。同じ秒に複数実行するスクリプトでは、必要なときだけ呼び出し側が `--sequence N` を明示して区別できます。自動採番や自動リネームは行いません。

dirpluck は非同期実行や並列実行どうしの競合制御を行いません。複数実行が重なる可能性がある場合、呼び出し側が異なる出力名を与える必要があります。動的命名では異なる `--sequence N` を明示する方法があります。同じ出力 path への並行書き込みはサポート対象外です。

### 実行ごとに変わる対象群へ固定資料を付随させる

一方で、実行ごとに変わる同種の対象がひとつ以上ある作業もあります。異なるプロジェクトを同じガイドラインでレビューしたり、複数の案件ディレクトリを同じ参照資料と一緒に調べたり、複数の提出物を同じテンプレートと指示書でまとめたりする場合です。

この違いはそのまま設定へ表せます。`[target]` は1個の共通選択規則として設定に残し、CLI からその実行で扱う1個以上の対象ディレクトリを受け取ります。TOML に複数の対象定義を持つわけではなく、同じ対象規則を各ディレクトリへ独立して適用します。コンパニオンは設定ファイルへ固定します。

```toml
[target]
description = "The submission currently being reviewed."
include = ["documents", "metadata.json"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck submissions/acme
```

同じ規則を1回の実行で複数の対象へ適用することもできます。

```console
dirpluck submissions/acme submissions/contoso submissions/globex
```

各対象は cwd から見た自身のディレクトリ path をアーカイブ内で保持し、同じ対象選択を使います。ひとつの対象でも複数の対象でも TOML の対象定義を増やす必要はありません。

### LLM と扱う作業コンテキストを再現可能にする

LLM を使う作業も同じ問題のひとつです。継続的な作業では、人間と LLM が同じ source、参照資料、生成物、関連プロジェクトを繰り返し必要とすることがあります。それらが会話履歴にしか残っていなければ、新しいセッションごとに再構成する必要があり、毎回同じ集合になる保証もありません。

設定ファイルがあれば、何を一緒に扱うかを双方が確認できる形で残せます。LLM は設定を読み、各 source がなぜ含まれるかを説明し、変更を支援し、`--dry-run` で結果を確認できます。継続する判断は以前の会話をモデルが覚えているかではなく TOML に残ります。

## 広いディレクトリ選択では除外を明示する

`include` または `include_if_exists` でディレクトリを選ぶと、その配下のファイルは再帰的に収集対象になります。dirpluck は隠しファイル、リポジトリのメタデータ、環境設定ファイル、認証情報、秘密鍵などを特別扱いしません。そのため `include = ["src"]` や `include = ["*"]` のような広い選択では、選択されたディレクトリ配下にあるものが `exclude` で除外されない限り対象になります。

アーカイブを共有したり外部へ渡したりする場合は、広い選択を確認し、そのワークスペースに必要な除外を明示してください。`.git/`、`.env*`、`*.pem`、`*.key` などは典型例ですが、どの名前が秘密情報かを網羅的に判断できる一覧ではありません。dirpluck 自身が秘密情報を推論して自動除外することはありません。

同じ除外一覧を base と複数ケース、または複数 source から使う場合は、共有パターンとして一度だけ定義できます。共有するのは完全な選択ではなくパターン配列だけで、利用する各選択が名前を明示的に参照します。たとえば通常の開発範囲と「ほぼ全部」を含めるケースで同じ除外を使えます。

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
    "*.pyc",
    ".DS_Store",
]

[target]
description = "The current development target."
include_if_exists = ["src", "tests", "README.md"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[target.case.all]
description = "All target files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

ケースは base を継承しないため、`exclude_pattern_refs` も必要な選択ごとに明示します。これにより Case の完全置換というルールを保ったまま、長いパターン配列だけを再利用できます。

## なぜモデルを意図的に狭くするのか

ここまでの例はすべて、**ひとつの設定ファイルはひとつの抽出意図を表す**という同じ主張の別の使い方です。dirpluck は設定ファイルを汎用検索言語や再利用 profile の階層へ広げず、抽出意図を局所的で明示的なまま保ちます。再利用できるのは名前付きの include / exclude パターン配列であり、source や Case の完全な選択定義を暗黙に共有・継承する仕組みではありません。

そのため dirpluck は、どのファイルが重要かを推論したり、最新成果物を選んだり、任意深度を探索したり、source 間の関係を自動で発明したりしません。それらの判断は設定ファイル上に残ります。source の構成、コンパニオン path、出力方針が異なる2つの作業は、暗黙の override を重ねるのではなく別の設定ファイルとして表します。

ケースも profile システムより小さい概念です。一回の実行で選べるのは最大1個の平坦なケース名です。そのケースは対象と、同名ケースを持つコンパニオンの完全な選択を切り替えられます。ケースを持たないコンパニオンは base 選択を使い続けます。ケースは source の追加・削除、コンパニオン path、出力方針を変更しません。

必須資料と任意資料も分けます。`include` は宣言した意図に一致が必要であることを意味し、`include_if_exists` は存在しないことが正常であることを意味します。これにより「今日は存在しない」と「パッケージが不完全」を区別できます。

## モデルの要点

設定ファイルには少なくとも1個の source と、ちょうど1個の出力定義があります。**対象**は省略可能な CLI 束縛の source 定義で、設定が対象を定義している場合は CLI から1個以上のディレクトリを渡し、同じ対象選択をそれぞれへ適用します。TOML に記述する `[target]` 定義は引き続き最大1個です。**コンパニオン**は設定ファイル自体に path を固定する source で、対象に同伴することも、対象を持たない設定を構成することもできます。

**ケース**は設定ファイル全体で共有する1個の平坦な選択 variation です。対象がある場合は対象が選択ケースを定義し、各コンパニオンは同名ケースがあれば使い、なければ base へフォールバックします。対象がない場合は少なくとも1個のコンパニオンがそのケースを定義します。

各 source の選択では必須項目と任意項目を記述します。同じパターン集合を繰り返す場合は共有パターンとして名前を付け、必要な選択から明示的に参照できます。出力も設定ファイルに属し、固定 path を更新するか、時刻ベースの名前で成果物を蓄積するかを宣言できます。動的命名では既存名を上書きせず、同じ秒の実行を区別する番号も必要な場合だけ CLI から明示します。

TOML の完全な書き方、対象とコンパニオンの形、ケース、選択フィールド、完全な例は `CONFIGURATION.md` を参照してください。matching、設定探索、ファイルシステム境界、アーカイブ、出力、dry-run、エラーの厳密な意味論は `SPECIFICATION.md` に定義します。

## CLI

サポート対象の公開インターフェースは CLI です。

対象を定義する設定では1個以上の `DIRECTORY` を指定します。同じ `[target]` 選択がすべてへ適用されます。

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

コンパニオンだけで構成する設定では位置引数を指定しません。

```console
dirpluck --config snapshot
```

名前付きケースを使う場合は `--case` を指定します。

```console
dirpluck DIRECTORY [DIRECTORY ...] --case review
```

コンパニオンだけの設定でもケースを使えます。

```console
dirpluck --config snapshot --case archive
```

別の設定ファイルを使う場合は `--config NAME` を指定します。`NAME` は任意パスではなくファイル名で、`.toml` は省略できます。

```console
dirpluck DIRECTORY [DIRECTORY ...] --config review
```

現在の cwd から検出できる設定ファイルを列挙します。

```console
dirpluck --configs
```

出力を作成・変更せず、同じアーカイブ計画を確認します。

```console
dirpluck DIRECTORY [DIRECTORY ...] --case review --dry-run
```

動的命名出力を使う設定では、同じ秒に複数の実行を区別する必要がある場合だけ正の整数を指定できます。

```console
dirpluck --config snapshot --sequence 2
```

選択規則や出力形式を一時的に置き換える CLI オプションは意図的に提供しません。それらは設定ファイルに属する判断であり、同じ宣言された意図から実行を説明できる状態を保つためです。`--sequence` は命名規則の override ではなく、動的命名が明示的に用意する番号部分への実行時入力です。

## インストール

Python 3.11 以降を使用します。現在のリリースは `0.2.0` です。

```console
pip install dirpluck
```

インストール後は次のコマンドで確認できます。

```console
dirpluck --version
```

dirpluck は実行時のサードパーティ依存を持ちません。

## 公開インターフェースと文書

互換性を保証する dirpluck の公開インターフェースは CLI です。パッケージ内の Python モジュールや関数は実装の分離とテストのために import できますが、現時点では互換性を保証する公開 Python API ではありません。

公開文書は役割で分けます。

- **README.md** は dirpluck を何に使えるか、その用途へモデルがどう対応するか、主要な設計境界を説明します。
- **USAGE.md** は実行時に必要な正の運用規則を短く確認するための操作リファレンスです。
- **CONFIGURATION.md** は TOML 設定ファイルの書き方と完全な記述例を説明します。
- **SPECIFICATION.md** は matching、探索、境界、アーカイブ、出力、dry-run、エラーの厳密な意味論を定義します。
- **GLOSSARY.md** はプロジェクト内で使うドメイン用語を短く定義します。

wheel にはインストール後の利用時に必要な `USAGE.md` だけを `dirpluck/docs/` 配下へ収録します。README、CONFIGURATION、SPECIFICATION、GLOSSARY、CHANGELOG、および文書生成設備は sdist またはリポジトリから参照します。
