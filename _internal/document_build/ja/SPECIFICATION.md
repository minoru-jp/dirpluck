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
正本は `dirpluck_docs/specification/canonical.py` です。
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

# dirpluck 仕様

dirpluck がサポートする CLI と設定ファイル形式の厳密な動作意味論を定義する。README は用途と設計モデル、`CONFIGURATION.md` は TOML の書き方を説明する。正確な挙動が必要な場合はこの文書を参照する。

## 1. 公開面

互換性を保証する公開面は `dirpluck` CLI と、この文書で定義する TOML 設定形式です。パッケージ内の Python モジュールは、将来 Python API として明示されない限り内部実装として扱います。

## 2. ルート設定ファイルの探索

CLI からルート設定ファイルを選ぶ設定探索は再帰せず、cwd を基準とした次の2箇所だけで行います。

- cwd 直下
- `./dirpluck/` 直下

`--config` を省略した場合の候補名は `dirpluck.toml` です。`--config NAME` を指定した場合、`NAME` は任意パスではなくファイル名として扱い、`.toml` は省略できます。

一致する候補が0件ならエラーです。同じ候補名が両方の探索位置に存在する場合は曖昧として拒否し、どちらかを暗黙に優先しません。

`--configs` は検出可能な root 候補を列挙します。cwd 直下では dirpluck 設定らしい構造を持つ TOML だけを列挙し、`./dirpluck/` 直下では TOML を候補として列挙します。両方に同名がある場合は ambiguous と表示します。

設定インポートではこの探索を使用しません。各 import は `configuration` に import root 内の相対 TOML file path を1個だけ明示し、その file を直接読み込みます。

## 3. トップレベル構造

受理するトップレベル構造は次です。

```text
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[import.<name>.companion.<name>]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

未知のキーはエラーです。各 Configuration では `[import.<name>]` は0個または1個、Target は0個または1個です。Companion と共有パターンは名前付きで複数定義できます。各 Configuration は通常形式として `[output]` を1個持ちますが、実行時に使用する output は最外側のルート設定ファイルだけです。

Configuration import がある場合、dirpluck は最深部から最外側へ definition layering を行い実効設定を構成します。Target は singleton `target`、Companion は Companion 名、共有パターンは include / exclude それぞれの pattern 名を名前解決キーとします。外側に同じキーがあれば内側の定義全体を shadow し、異なるキーは共存します。

Source 定義の shadow は部分 merge ではありません。Target または Companion を shadow すると、その `path`、`description`、base Selection、全 Case Selection を含む定義全体が置き換わります。共有パターンも配列全体を置き換えます。

Root Configuration 自身に Target / Companion がなくても、import chain の解決後に Target または Companion が少なくとも1個残れば有効です。

## 4. 設定インポートと名前解決

設定インポートは各 Configuration に0個または1個だけ宣言できます。形式は `[import.<name>]` です。`<name>` は link をエラー表示やアーカイブ索引で識別するための空でない名前であり、0.5.0 の Companion / shared pattern 名へ自動 prefix を付ける namespace ではありません。

各 import が受理する field は次です。

```text
root             required string
configuration    required string
companion.<name> zero or more import-root overlays
```

`case` field は受理しません。Case は chain を解決した実効設定へ CLI `--case` から1個だけ適用します。

### `root`

`root` は**その import を記述した Configuration file の所在ディレクトリ**から見た相対 directory path です。空文字列、絶対 path、glob を拒否します。`.` と `..` は使用でき、path separator は `/` を正規形とします。POSIX absolute path、Windows drive path、UNC path は実行 OS に関係なく拒否します。解決後は実在 directory でなければなりません。

解決した root は直下の imported Configuration の execution root / filesystem boundary になります。chain の次の import root も同じ規則で、その import を記述した Configuration file 自身を基準に解決します。

### `configuration`

`configuration` は import root から見た相対 TOML file path です。空文字列、絶対 path、import root 外へ出る `..`、glob、`.toml` 以外の拡張子を拒否します。解決先は import root 内の実在 regular file でなければなりません。通常の root Configuration 探索は行わず、この file を直接読み込みます。

### linear chain

import 先 Configuration も同じ schema で `[import.<name>]` を0個または1個持てます。import depth に上限は設けません。

解決時には Configuration file の正規化済み実パスを現在の chain として保持します。同じ file が現在の chain に再登場した場合は cycle error とし、循環した chain を診断へ含めます。深さ自体による error / warning はありません。

### definition resolution

chain の最深部を初期値とし、1 layer ずつ外側の定義を重ねます。

- Target: 外側に Target があれば内側 Target 全体を shadow する。
- Companion: 同名 Companion は外側が全体を shadow し、異なる名前は保持する。
- shared include patterns: 同名 pattern は外側が配列全体を shadow する。
- shared exclude patterns: include とは独立した名前空間で同じ規則を使う。

Selection の `include_pattern_refs` / `include_if_exists_pattern_refs` / `exclude_pattern_refs` は、各 source の origin layer だけではなく、chain 全体を重ね終えた実効 shared namespace で解決します。したがって内側 source が参照する名前を外側 layer が提供または override できます。最終解決後も存在しない参照名は Configuration error です。

### import-root Companion overlay

`[import.<name>.companion.<companion-name>]` は、直下の import root を path 基準とする Companion 定義です。通常 Companion と同じ Selection schema を使い、`path = "."` を許可します。その他の絶対 path、`..`、glob は拒否します。

この定義は Companion 名 `<companion-name>` として outer layer から名前解決へ参加するため、直下 imported Configuration の同名 Companion を shadow できます。同じ Configuration layer で `[companion.x]` と `[import.<name>.companion.x]` を両方定義することはできません。

### Target directory resolution

実効設定に Target が存在する場合、その Target 定義の origin layer にかかわらず CLI `DIRECTORY` を1個以上必要とし、同じ Target Selection をそれぞれへ適用します。各 `DIRECTORY` はルート設定ファイルの execution root、つまり process cwd 内で解決します。

Target Selection の origin Configuration は selection / Case / shared pattern の名前解決にだけ影響し、runtime Target directory の自動推定には使用しません。import chain 内側の Target が実効 Targetとして残っていても、Configuration file の配置から project directory を推定することはありません。

import chain 内側の `[output]` は schema validation の対象ですが実行しません。最終 output はルート設定ファイルの `[output]` だけです。

## 5. ケース

Case は実効設定全体で0個または1個だけ有効になる平坦な名前付き selection variation です。CLI `--case` から最大1個選びます。import layer ごとに別 Case を束縛する field はありません。

Target / Companion が outer layer によって shadow された場合、その source の base と全 Case 定義も一緒に置き換わります。shadow されずに残った source の Case は origin layer に関係なく実効設定へ参加します。

Case 未指定時は Target があれば `[target]`、各 Companion は base `[companion.<name>]` を使います。

Case 指定時に Target がある場合、同名 `[target.case.<name>]` が必須です。各 Companion は同名 Case があれば使い、なければ base へフォールバックします。Target がない場合は、少なくとも1個の Companion が同名 Case を定義する必要があります。

Case Selection は base の差分ではなく完全な Selection で、include / exclude / shared pattern refs を継承しません。

## 6. 対象とコンパニオン

各 Configuration の Target 定義は最大1個です。Target は `path` を保存せず、base または Case Selection を持ちます。Configuration chain では外側 Target が内側 Target を定義全体として shadow するため、実効設定に残る Target は最大1個です。

Target が実効設定に存在するなら origin layer にかかわらず CLI `DIRECTORY` を1個以上束縛します。Target がない実効設定では `DIRECTORY` を受理しません。

各 Companion は固定 `path`、空でない `description`、完全な base Selection を持ちます。通常 Companion の `path` は定義を所有する Configuration layer の execution root 相対です。`[import.<name>.companion.<name>]` overlay は直下 import root 相対です。

同名 Companion を outer layer が定義した場合は inner definition を path / description / base / Case ごと shadow します。異なる名前の Companion はすべて実効設定へ残ります。

## 7. 選択定義

各 Target / Companion の base または Case Selection には、空でない `description` と、直接記述または shared pattern reference による `include` / `include_if_exists` 相当候補の少なくとも一方が必要です。

`include_pattern_refs` と `include_if_exists_pattern_refs` は実効 include shared namespace、`exclude_pattern_refs` は実効 exclude shared namespaceの名前を参照します。0.5.0では import 名を prefix した修飾参照を必要とせず、通常の pattern 名を chain 全体で解決します。

Shared namespace は chain の最深部から最外側へ同名定義を shadow して構成します。Source Selection が内側 layer に由来していても参照はこの最終 namespace で解決するため、outer layer は同名 shared pattern を定義して inner source の参照先を override できます。また inner layer に参照先定義がなくても outer layer で最終的に解決できれば有効です。

存在しない shared name の参照は chain 全体の解決後に Configuration error です。Shared refs は参照配列の順に展開し、その後に同種の直接 pattern を追加します。展開後の必須 include 内、任意 include 内、exclude 内の重複、および必須 / 任意 include 間の重複は Configuration error です。

`if_empty = "allow"` は展開後に必須 include pattern を持たない optional-only Selection だけで指定できます。

## 8. include パターン文法

include パターンは対象またはコンパニオンからの POSIX 形式の相対パスです。絶対パス、パターン全体としての `.`、`..` による逸脱を拒否します。検証前にバックスラッシュは `/` へ正規化します。

各パス要素には `*` を最大1個だけ含められます。`*` はひとつの実体名の内部で0文字以上に一致し、パス区切りを越えません。そのため、設定に書いたパス階層数は固定されます。

例:

```text
src
README.md
dist/package-*.whl
packages/*/dist/package-*.whl
```

最後に一致した実体がファイルならそのファイルを選択し、ディレクトリなら除外規則とシンボリックリンク規則に従って配下のファイルを再帰収集します。隠しファイル、リポジトリメタデータ、環境設定ファイル、秘密鍵などに対する暗黙の除外は行いません。選択されたツリー内にあり `exclude` されていなければ通常のファイルと同じように対象になります。

複数一致した場合はすべて選択します。照合は OS に依存せず大文字と小文字を区別します。

`**`、`?`、文字クラス (`[]`)、`!` はサポートしません。複数一致した場合にバージョン、更新日時、その他のメタデータを解釈しません。

## 9. exclude パターン文法

exclude は相対パスではなく、ひとつの実体名を照合します。

末尾が `/` のパターンはディレクトリ名、`/` のないパターンはファイル名へ適用します。

対応形式は次です。

```text
name      完全一致
name*     前方一致
*name     後方一致
*name*    部分一致
```

`*` 単体、`*/`、`foo*bar` のような内部 wildcard、`**`、`?`、文字クラス、`!`、バックスラッシュ、パス区切りは拒否します。

## 10. ファイルシステム境界とシンボリックリンク

ルート設定ファイルの execution root / filesystem boundary は process cwd です。各 import layer の execution root は、その layer を読み込んだ `[import.<name>].root` の解決結果です。

Import root を解決できる唯一の越境 path とし、その root 確定後は imported `configuration`、その layer の通常 Companion、Companion の選択ファイルを対応する execution root 内へ限定します。Target directory は常にルート設定ファイルの execution root 内で CLI から解決します。次の import root は importing Configuration file 自身の所在 directory から解決するため、chain が深くても各 boundary は独立して確定します。

通常 Companion は定義 origin layer の execution root、import-root overlay Companion は直下 import root を path 基準として保持します。Definition が shadow された場合は shadow した outer definition の root 情報へ置き換わります。

シンボリックリンクを利用した boundary 外への source path / selected file の逸脱は拒否します。Directory recursion では directory symlink をたどらず、外部へ解決する link は error、内部へ解決する link は循環と重複防止のため無視します。

## 11. アーカイブ計画とパス

Target の選択ファイルは、Target 定義の origin layer にかかわらずルート設定ファイルの execution root から見た filesystem relative path を ZIP 内で保持します。Companion の選択ファイルは、その effective Companion definition に対応する execution root から見た相対 path を保持します。Shadow されずに inner layer から残った Companion は inner execution root、outer definition に置き換わった Companion は outer execution root を使います。

同じ archive path に同じ物理 file が重なる場合は1回だけ書き込みます。異なる物理 file が同じ archive path へ衝突する場合、または同じ物理 file が異なる execution root から異なる archive path へ解決される場合は ambiguity error です。

Archive root の `README.md` には Configuration chain、各 execution root、どの layer の definition が実効設定へ残ったか、選択 Case、参加 source、description、selection count など解決済み計画の事実を記録します。

## 12. 出力

各 Configuration の `[output]` は schema 上必須で、固定出力または動的命名出力のどちらか一方だけを定義します。Output は Configuration layering の名前解決対象にしません。一回の実行で計画・検証・書き込みするのは最外側のルート設定ファイルの `[output]` だけで、chain 内側の output は schema validation だけを行い filesystem path 解決、collision check、directory 作成、書き込みを行いません。

### 固定出力

```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

固定出力では `path` と `if_exists` の両方が必須です。Root Configuration の `path` は cwd より下にある具体的な cwd 相対パスでなければならず、絶対パス、`..`、glob を拒否します。必要な親ディレクトリは作成します。シンボリックリンクによって cwd 外へ解決される出力先は拒否します。

`if_exists` は次だけを受理します。

- `error`: 既存出力を変更せずに失敗する
- `overwrite`: 出力先ディレクトリの一時ファイルへ新しい ZIP を完成させたあとで既存出力を置換する

`error` ではビルド前と最終配置の直前に出力先が存在しないことを確認します。ZIP は同一出力ディレクトリ内の一時ファイルへ完成させてから最終 path へ配置します。非同期実行や並列実行どうしの lock や競合調停は提供せず、同じ出力 path への並行書き込みはサポート対象外です。

### 動的命名出力

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

動的命名出力では `directory` と `timestamp = true` が必須で、`prefix` と `suffix` は任意です。`path` と `if_exists` は指定できません。

Root Configuration の `directory` は cwd 内の具体的な cwd 相対ディレクトリでなければならず、`.` は cwd 自体を表す値として使用できます。絶対パス、`..`、glob を拒否します。必要なディレクトリは作成し、シンボリックリンクによる cwd 外への逸脱を拒否します。

`prefix` と `suffix` は空でない1個の portable filename fragment とし、`.`、`..`、path separator、制御文字、`< > : " | ? *` を拒否します。

生成するファイル名は次の固定形式です。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

時刻は実行プロセスのローカル時刻を使い、ビルド開始時に一度だけ確定します。自由な timestamp 書式、変数展開、命名テンプレートはありません。

`N` は CLI の `--sequence N` から受け取る1以上の整数です。指定されなければ番号部分を省略します。ライブラリは既存出力を探索して番号を推測せず、自動採番・自動リネームを行いません。`--sequence` は動的命名出力だけで使用でき、複数回指定できません。

動的命名出力で確認時点に同名ファイルが既に存在する場合はエラーです。上書き設定は存在しません。競合するプロセス間の同期は行わないため、並行する可能性がある呼び出し側は、たとえば異なる `--sequence N` を与えて出力 path を分ける必要があります。

どちらの形式でも、出力ファイル自身をアーカイブ入力として選択することはできません。

## 13. dry-run

`--dry-run` は通常実行と同じ import chain 解決、cycle detection、definition layering、Target directory resolution、Case 選択、file selection、archive plan logic を使いますが、output を作成・変更しません。

不足する必須 `include` は `[missing]`、不足する任意 pattern は `[optional missing]` と表示します。最終選択0件は policy に応じて `empty, allowed` または `empty, would error` と表示します。

複数 import を同じ Configuration に定義した場合、import cycle、不正 root / configuration path、未解決 shared pattern ref、不正 source path、Case 矛盾などは dry-run でも error です。Import depth 自体は error / warning にしません。

## 14. CLI 形式

ルート設定ファイル自身の Target が実効設定へ残る場合は1個以上の runtime directory を指定します。

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

Target が実効設定に存在する場合は、その origin layer にかかわらず `DIRECTORY` を指定します。Target を持たない effective Configuration では `DIRECTORY` を指定しません。

```console
dirpluck --config NAME
```

Effective Configuration 全体の named Case を選びます。

```console
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
dirpluck --config NAME --case NAME
```

別の検出可能な Root Configuration を使う `--config`、書き込まない `--dry-run`、候補列挙の `--configs`、動的 output 用 `--sequence N`、`--version` は従来どおりです。

Import chain 用の追加 CLI path や layer ごとの Case option はありません。Import は TOML の `[import.<name>]` だけで構成し、Case は名前解決後の実効設定へ1個だけ適用します。
