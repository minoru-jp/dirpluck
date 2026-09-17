from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} 仕様")
class TITLE_0:
    r'''{{TERM_1}} がサポートする CLI と{{TERM_2}}形式の厳密な動作意味論を定義する。README は用途と設計モデル、`CONFIGURATION.md` は TOML の書き方を説明する。正確な挙動が必要な場合はこの文書を参照する。'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_2)

    @title('1. 公開面')
    class TITLE_1:
        r'''互換性を保証する公開面は `dirpluck` CLI と、この文書で定義する TOML 設定形式です。パッケージ内の Python モジュールは、将来 Python API として明示されない限り内部実装として扱います。'''

    @title('2. 設定探索')
    class TITLE_2:
        r'''設定探索は再帰せず、cwd を基準とした次の2箇所だけで行います。

- cwd 直下
- `./dirpluck/` 直下

`--config` を省略した場合の候補名は `dirpluck.toml` です。`--config NAME` を指定した場合、`NAME` は任意パスではなくファイル名として扱い、`.toml` は省略できます。

一致する候補が0件ならエラーです。同じ候補名が両方の探索位置に存在する場合は曖昧として拒否し、どちらかを暗黙に優先しません。

`--configs` は検出可能な候補を列挙します。cwd 直下では dirpluck 設定らしい構造を持つ TOML だけを列挙し、`./dirpluck/` 直下では TOML を候補として列挙します。両方に同名がある場合は ambiguous と表示します。'''

    @title('3. トップレベル構造')
    class TITLE_3:
        r'''受理するトップレベル構造は次だけです。

```text
[shared.include_patterns]
[shared.exclude_patterns]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

検証対象の各階層で未知のキーはエラーです。

ひとつの設定ファイルはひとつの抽出意図を表し、次を含みます。

- 0個以上の名前付き{{TERM_12}}
- 0個または1個の論理的な対象定義
- 0個以上のコンパニオン
- 対象またはコンパニオンの少なくとも1個の source
- ちょうどひとつの出力定義

対象は runtime-bound source 定義で、1個の論理的な `[target]` 定義を CLI から受け取った1個以上のディレクトリへ適用します。すべての runtime 対象は同じ選択済み対象定義を使います。コンパニオンは設定の `path` に固定される configuration-bound source です。

{{TERM_12}}は名前付きパターン配列だけを再利用する仕組みで、完全な共有選択定義ではありません。bundle、設定継承、設定 merge、CLI からの選択 override はありません。

`[shared.include_patterns]` と `[shared.exclude_patterns]` はそれぞれ省略可能です。`[shared]` を記述する場合は少なくともどちらか一方が必要で、記述した各 table には少なくとも1個の名前付き配列が必要です。各名前は空でない文字列で、各配列は1件以上の文字列を含みます。include 用の配列は include パターン文法、exclude 用の配列は exclude パターン文法で設定ロード時に検証します。定義しただけの共有パターンはどの選択にも適用されません。'''

        vocabulary_refs @= (terms.TERM_12,)

    @title('4. ケース')
    class TITLE_4:
        r'''ケースは設定ファイル全体で0個または1個だけ有効になる平坦な名前付き selection variation です。ケース名は組み合わせず、多階層化せず、`--case` は最大1回だけ指定できます。

ケースが変更できるのは source の選択だけです。対象やコンパニオンの追加・削除、コンパニオンの `path`、出力方針は変更しません。

ケース未指定時、対象がある場合は `[target]` を使い、対象に既定選択がなければエラーです。各コンパニオンは base の `[companion.<name>]` を使います。

ケース指定時に対象がある場合、同名の `[target.case.<name>]` が必須です。各コンパニオンは `[companion.<companion-name>.case.<name>]` があれば使い、なければ base へフォールバックします。対象に存在しないケース名をコンパニオンだけが定義することは到達不能なので設定エラーです。

ケース指定時に対象がない場合、少なくとも1個のコンパニオンが同名ケースを定義する必要があります。各コンパニオンは同名ケースがあれば使い、なければ base へフォールバックします。

対象ケースとコンパニオンケースはいずれも完全な選択定義で、base を継承・merge しません。base 選択にある共有パターン参照も継承しないため、ケースで同じ共有パターンを使う場合はそのケース自身が同じ名前を明示的に参照します。'''

    @title('5. 対象とコンパニオン')
    class TITLE_5:
        r'''対象は省略可能です。`[target]` または `[target.case.<name>]` が存在する場合、その設定はひとつの runtime-bound 対象規則を定義します。対象の `path` は設定ファイルへ保存せず、TOML から複数の別個な対象規則を定義することもできません。

対象を定義する設定では CLI の位置引数 `DIRECTORY` が1個以上必須です。選択された対象定義を CLI 順に各ディレクトリへ独立して適用し、すべての runtime 対象ディレクトリは互いに異なる実ディレクトリへ解決される必要があります。対象を定義しない設定へ位置引数 `DIRECTORY` を指定するとエラーです。

`[target]` は `--case` を省略した実行で使う既定の対象選択です。対象は `[target]` を省略して名前付きケースだけを定義することもでき、その場合は `--case` を省略するとエラーです。

各 runtime 対象ディレクトリは実行時に存在し、ファイルシステム境界規則に従って解決される必要があります。

各 `[companion.<name>]` は cwd 相対の固定 `path`、空でない `description`、完全な base 選択定義を必須とします。コンパニオンは対象の有無にかかわらず source 集合へ常に参加し、実行時にそのディレクトリが存在する必要があります。

必要なら `[companion.<name>.case.<case-name>]` に完全な代替選択を追加できます。選択ケースが存在しないコンパニオンは削除されず、base 選択へフォールバックします。'''

    @title('6. 選択定義')
    class TITLE_6:
        r'''各 `[target]`、`[target.case.<name>]`、`[companion.<name>]`、`[companion.<name>.case.<case-name>]` の選択には、空でない `description` と、直接記述または共有参照による `include` / `include_if_exists` 相当の候補の少なくとも一方が必要です。

直接記述の `include` と `include_if_exists` は、それぞれ1件以上の文字列を含む必要があります。共有参照フィールドも、指定する場合は1件以上の共有名を含む文字列配列です。同一フィールド内の重複参照は拒否します。

### `include` と `include_pattern_refs`

`include` は必須 include パターンを直接記述します。`include_pattern_refs` は `[shared.include_patterns]` の名前を参照し、その配列を必須 include パターンとして展開します。通常実行では、展開後のすべての必須パターンが少なくとも1件のファイルシステム実体に一致する必要があります。0件一致はエラーです。

### `include_if_exists` と `include_if_exists_pattern_refs`

`include_if_exists` は任意 include パターンを直接記述します。`include_if_exists_pattern_refs` は `[shared.include_patterns]` の名前を参照し、その配列を任意 include パターンとして展開します。必須 include と同じパターン文法を使いますが、0件一致を正常として扱い、選択へ何も追加しません。

同じ共有 include パターン集合を、ある選択では `include_pattern_refs`、別の選択では `include_if_exists_pattern_refs` から参照できます。必須か任意かは共有定義ではなく参照側が決めます。

### `exclude` と `exclude_pattern_refs`

`exclude` は除外パターンを直接記述します。`exclude_pattern_refs` は `[shared.exclude_patterns]` の名前を参照して除外パターンを展開します。どちらも include によって既に選ばれた範囲の実体名だけをフィルタし、場所を選択しません。

### 展開と重複

共有参照は参照配列の順序で展開し、その後に同種の直接記述パターンを追加します。存在しない共有名の参照は設定エラーです。展開後、必須 include 内、任意 include 内、exclude 内に同じ実効パターンが重複した場合は設定エラーです。必須 include と任意 include の両方に同じ正規化済みパターンが現れる場合も設定エラーです。

### `if_empty`

既定値は `error` です。

`if_empty = "allow"` は展開後の必須 include パターンを持たない optional-only の選択だけで指定できます。最終ファイル数が0件で空を許す場合、その対象ディレクトリをアーカイブ内の明示的な空ディレクトリエントリとして保持できます。'''

    @title('7. include パターン文法')
    class TITLE_7:
        r'''include パターンは対象またはコンパニオンからの POSIX 形式の相対パスです。絶対パス、パターン全体としての `.`、`..` による逸脱を拒否します。検証前にバックスラッシュは `/` へ正規化します。

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

`**`、`?`、文字クラス (`[]`)、`!` はサポートしません。複数一致した場合にバージョン、更新日時、その他のメタデータを解釈しません。'''

    @title('8. exclude パターン文法')
    class TITLE_8:
        r'''exclude は相対パスではなく、ひとつの実体名を照合します。

末尾が `/` のパターンはディレクトリ名、`/` のないパターンはファイル名へ適用します。

対応形式は次です。

```text
name      完全一致
name*     前方一致
*name     後方一致
*name*    部分一致
```

`*` 単体、`*/`、`foo*bar` のような内部 wildcard、`**`、`?`、文字クラス、`!`、バックスラッシュ、パス区切りは拒否します。'''

    @title('9. ファイルシステム境界とシンボリックリンク')
    class TITLE_9:
        r'''cwd を実行境界とします。

使用される対象ディレクトリとすべてのコンパニオンディレクトリは存在し、cwd 内へ解決されなければなりません。シンボリックリンク経由で cwd 外へ逸脱するパスは拒否します。

選択されたファイルは、それぞれの対象またはコンパニオンディレクトリ内へ解決される必要があります。外部へ解決されるファイルシンボリックリンクは拒否します。

ディレクトリを再帰収集するとき、ディレクトリシンボリックリンクはたどりません。対象ディレクトリ外へ解決されるディレクトリリンクはエラーとし、内部へ解決されるリンクは循環と重複を防ぐため無視します。

対象には `.` として cwd 自体を指定できます。この場合も cwd の内容を ZIP ルートへ平坦化せず、cwd の実ディレクトリ名を先頭要素として保持します。'''

    @title('10. アーカイブ計画とパス')
    class TITLE_10:
        r'''選択されたファイルは ZIP 内で cwd から見た実際のファイルシステム相対パスを保持します。

複数の source が同じ実ディレクトリへ解決される場合、その選択は実際のアーカイブパスで union します。複数の宣言目的から選択されても同じ物理ファイルは一度だけ書き込みます。

アーカイブのルートには、有効なケース（未指定時は `default`）、参加するディレクトリ、設定された description、実際に選択された設定位置、ディレクトリ決定方法、選択件数、必要な空結果方針など、解決済み計画の事実だけを索引する `README.md` を生成します。固定文言では生成ツール名や下流用途を示しません。用途固有の意味は各対象・コンパニオンの `description` からのみ持ち込みます。

アーカイブ計画は決定的な順序で作成し、偶発的なファイルシステム列挙順序へ依存しません。'''

    @title('11. 出力')
    class TITLE_11:
        r'''`[output]` は必須で、固定出力または動的命名出力のどちらか一方だけを定義します。両形式のフィールドを混在させると設定エラーです。

### 固定出力

```toml
[output]
path = "artifacts/context.zip"
if_exists = "error"
```

固定出力では `path` と `if_exists` の両方が必須です。`path` は cwd より下にある具体的な cwd 相対パスでなければならず、絶対パス、`..`、glob を拒否します。必要な親ディレクトリは作成します。シンボリックリンクによって cwd 外へ解決される出力先は拒否します。

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

`directory` は cwd 内の具体的な cwd 相対ディレクトリでなければならず、`.` は cwd 自体を表す値として使用できます。絶対パス、`..`、glob を拒否します。必要なディレクトリは作成し、シンボリックリンクによる cwd 外への逸脱を拒否します。

`prefix` と `suffix` は空でない1個の portable filename fragment とし、`.`、`..`、path separator、制御文字、`< > : " | ? *` を拒否します。

生成するファイル名は次の固定形式です。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

時刻は実行プロセスのローカル時刻を使い、ビルド開始時に一度だけ確定します。自由な timestamp 書式、変数展開、命名テンプレートはありません。

`N` は CLI の `--sequence N` から受け取る1以上の整数です。指定されなければ番号部分を省略します。ライブラリは既存出力を探索して番号を推測せず、自動採番・自動リネームを行いません。`--sequence` は動的命名出力だけで使用でき、複数回指定できません。

動的命名出力で確認時点に同名ファイルが既に存在する場合はエラーです。上書き設定は存在しません。競合するプロセス間の同期は行わないため、並行する可能性がある呼び出し側は、たとえば異なる `--sequence N` を与えて出力 path を分ける必要があります。

どちらの形式でも、出力ファイル自身をアーカイブ入力として選択することはできません。'''

    @title('12. dry-run')
    class TITLE_12:
        r'''`--dry-run` は通常実行と同じ source 解決、ケース解決、選択、アーカイブ計画ロジックを使いますが、出力を作成・変更しません。

不足する必須 `include` は `[missing]`、不足する任意パターンは `[optional missing]` と表示します。

最終選択が0件の対象は、許可される場合 `empty, allowed`、通常実行なら空のため失敗する場合 `empty, would error` と表示します。

設定矛盾、対象と `DIRECTORY` の不整合、不正なパス、存在しないケース名、固定出力での `--sequence` 指定は dry-run でもエラーです。dry-run は出力を書かないため、timestamp から実出力名を確定せず、既存出力との衝突方針も適用しません。'''

    @title('13. CLI 形式')
    class TITLE_13:
        r'''対象を定義する設定を1個以上の runtime ディレクトリで生成します。

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

コンパニオンだけで構成する設定を生成します。

```console
dirpluck --config NAME
```

名前付きケースで生成します。

```console
dirpluck DIRECTORY [DIRECTORY ...] --case NAME
```

対象を持たない設定でもケースを指定できます。

```console
dirpluck --config NAME --case NAME
```

別の検出可能な設定を使います。

```console
dirpluck DIRECTORY [DIRECTORY ...] --config NAME
```

書き込まずに確認します。

```console
dirpluck DIRECTORY [DIRECTORY ...] --dry-run
```

検出可能な設定を列挙します。

```console
dirpluck --configs
```

動的命名出力で、同じ秒に複数の実行を明示的に区別します。

```console
dirpluck --config NAME --sequence N
```

`N` は1以上の整数で、`--sequence` は最大1回だけ指定できます。固定出力ではエラーです。

インストールされているバージョンを表示します。

```console
dirpluck --version
```

`build` サブコマンドはなく、選択規則や出力形式を一時的に上書きする CLI オプションもありません。`--sequence` は動的命名形式が定義する任意の番号位置へ実行時の値を与えるだけです。'''
