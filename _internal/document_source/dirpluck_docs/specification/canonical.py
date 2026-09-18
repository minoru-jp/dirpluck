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

    @title('2. ルート設定ファイルの探索')
    class TITLE_2:
        r'''CLI から{{TERM_14}}を選ぶ設定探索は再帰せず、cwd を基準とした次の2箇所だけで行います。

- cwd 直下
- `./dirpluck/` 直下

`--config` を省略した場合の候補名は `dirpluck.toml` です。`--config NAME` を指定した場合、`NAME` は任意パスではなくファイル名として扱い、`.toml` は省略できます。

一致する候補が0件ならエラーです。同じ候補名が両方の探索位置に存在する場合は曖昧として拒否し、どちらかを暗黙に優先しません。

`--configs` は検出可能な root 候補を列挙します。cwd 直下では dirpluck 設定らしい構造を持つ TOML だけを列挙し、`./dirpluck/` 直下では TOML を候補として列挙します。両方に同名がある場合は ambiguous と表示します。

{{TERM_13}}ではこの探索を使用しません。各 import は `configuration` に import root 内の相対 TOML file path を1個だけ明示し、その file を直接読み込みます。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_14)

    @title('3. トップレベル構造')
    class TITLE_3:
        r'''受理するトップレベル構造は次だけです。

```text
[shared.include_patterns]
[shared.exclude_patterns]
[import.<name>]
[target]
[target.case.<name>]
[companion.<name>]
[companion.<name>.case.<name>]
[output]
```

検証対象の各階層で未知のキーはエラーです。

ひとつの設定ファイルはひとつの抽出意図を表し、次を含みます。

- 0個以上の名前付き{{TERM_12}}
- 0個以上の{{TERM_13}}
- 0個または1個の論理的な対象定義
- 0個以上のコンパニオン
- {{TERM_14}}ではローカル source または設定インポートの少なくとも1個
- ちょうどひとつの出力定義

対象は runtime-bound source 定義で、1個の論理的な `[target]` 定義を CLI から受け取った1個以上のディレクトリへ適用します。すべての runtime 対象は同じ選択済み対象定義を使います。コンパニオンは設定の `path` に固定される configuration-bound source です。

{{TERM_12}}は名前付きパターン配列だけを再利用する仕組みで、完全な共有選択定義ではありません。同じ設定ファイル内ではローカル名で参照し、{{TERM_14}}は明示的に import した Configuration の共有パターンを `<import>.<pattern>` の修飾名でも参照できます。{{TERM_13}}は別の完全な設定ファイルが宣言する Companion と共有パターンを明示的に再利用する仕組みで、設定継承や設定 merge ではありません。CLI からの選択 override もありません。

`[shared.include_patterns]` と `[shared.exclude_patterns]` はそれぞれ省略可能です。`[shared]` を記述する場合は少なくともどちらか一方が必要で、記述した各 table には少なくとも1個の名前付き配列が必要です。各名前は空でない文字列で、各配列は1件以上の文字列を含みます。include 用の配列は include パターン文法、exclude 用の配列は exclude パターン文法で設定ロード時に検証します。定義しただけの共有パターンはどの選択にも適用されません。'''

        vocabulary_refs @= (terms.TERM_12, terms.TERM_13, terms.TERM_14,)

    @title('4. 設定インポート')
    class TITLE_4:
        r'''{{TERM_13}}は{{TERM_14}}から0個以上宣言できます。形式は `[import.<name>]` で、`<name>` は空でない import 識別名です。import 名はアーカイブ path prefix ではなく、設定位置・エラー・アーカイブ索引で import を識別するために使います。

各 import が受理する field は次だけです。

```text
root            required string
configuration   required string
case            optional non-empty string
companion.<name> zero or more Root-owned Companion tables
```

### `root`

`root` は{{TERM_14}}自身の所在ディレクトリから見た相対ディレクトリ path です。空文字列、絶対 path、glob は拒否します。`.` と `..` path element は使用でき、`..` によって cwd 外の別ディレクトリを明示的に選べます。path separator は `/` を正規形とし、POSIX absolute path、Windows drive path、UNC path などの絶対指定は実行 OS にかかわらず拒否します。解決後は実在するディレクトリでなければなりません。

`root` は{{TERM_13}}だけに与える境界拡張です。解決された実ディレクトリを import 先設定の実行 root とし、import 実行で使用する Companion と選択ファイルはすべてこの root 内に留まる必要があります。root path 自体がシンボリックリンクを経由する場合は、その解決先ディレクトリを boundary とします。

### `configuration`

`configuration` は import root から見た相対 TOML file path です。空文字列、絶対 path、`.` / `..` による逸脱、glob、`.toml` 以外の拡張子を拒否します。解決先は import root 内の実在 regular file でなければなりません。

import では通常の設定探索を行いません。`configuration` が指す1 file を直接読み、通常の設定 schema として完全に parse / validate します。import 先設定の `[shared.include_patterns]` / `[shared.exclude_patterns]` は、その設定自身では従来どおりローカル名で有効です。さらに {{TERM_14}} 側からは `<import-name>.<pattern-name>` の修飾名として参照できます。Root local の共有パターンと import 由来の共有パターンを merge したり、import 先設定自身の参照先を Root 側の名前へ再束縛したりはしません。

import 先設定も通常形式として `[output]` を必須としますが、その output は import 実行では採用しません。output field の schema validation は行いますが、出力 path の作成、既存出力 collision の確認、書き込みは行いません。import 先に `[target]` / `[target.case.<name>]` が存在しても、それらは通常の直接実行用として検証するだけで、import 実行では source として使用しません。

{{TERM_14}}は `[import.<name>.companion.<companion-name>]` を0個以上宣言して、同じ import root 内へ追加 Companion を定義できます。schema は通常の `[companion.<name>]` と同じですが、`path = "."` を許可して import root 自体を Companion にできます。その他の絶対 path、`..`、glob は拒否し、解決結果は import root 内の実在ディレクトリでなければなりません。Root 側追加 Companion は {{TERM_14}} が所有する Selection なので、Root local の共有パターンをローカル名で、任意の import 由来共有パターンを `<import>.<pattern>` の修飾名で参照できます。import 先設定由来 Companion は import 先設定の shared pattern 名前空間だけをローカル名で解決します。

import 名は Companion と Root-visible shared pattern の論理名前空間です。Root の `[companion.x]` は `x`、`[import.a]` 配下の Companion `x` は import 先設定由来か Root 側追加かにかかわらず `a.x` を論理名とします。import 先の共有パターン `p` は Root 側から `a.p` として参照します。同じ import 内で import 先設定と Root 側追加が同じ Companion 名を定義する場合は論理名が重複するため設定エラーです。別 import や Root local Companion との同名は名前空間が異なるため許可します。Root local 共有パターン名と、import 由来の修飾共有パターン名が同じ参照文字列になる場合は曖昧なので設定エラーです。Companion 論理名は Archive path prefix には使いません。

各 import 名前空間には、import 先設定由来または Root 側追加の Companion が少なくとも1個必要です。

### `case`

`case` を省略した import は import 名前空間内の全 Companion の base 選択を使います。指定する場合、その名前を import 先設定由来または Root 側追加の Companion の少なくとも1個が Case として定義している必要があります。同名 Case を持つ Companion はその完全な Case 選択を使い、持たない Companion は base へフォールバックします。import 先 Target の Case は使用しません。

{{TERM_14}}の CLI `--case` は import 先へ伝播しません。各 import の Companion Case は `[import.<name>].case` だけで決定します。したがって root 設定と複数 import は、それぞれ独立した Case を同じ実行内で持てます。

### 再帰 import

import 先設定に `[import.<name>]` が1個でも存在する場合は設定エラーです。設定インポートの graph は1階層に限定し、循環参照、推移的 import、深さ依存の Case 束縛を提供しません。

{{TERM_14}}はローカル Target / Companion を持たず import だけを持つことができます。各 import では、import 先設定自身に Companion がなくても `[import.<name>.companion.<name>]` が1個以上あれば有効です。両方とも0個なら利用可能な source がないためエラーです。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_14)

    @title('5. ケース')
    class TITLE_5:
        r'''ケースはひとつの設定ファイル内で0個または1個だけ有効になる平坦な名前付き selection variation です。ケース名は組み合わせず、多階層化しません。{{TERM_14}}の Case は CLI `--case` から最大1個選び、各 import では import 先 Companion 群へ適用する Case を対応する `[import.<name>].case` から独立して最大1個選びます。

ケースが変更できるのは source の選択だけです。対象やコンパニオンの追加・削除、コンパニオンの `path`、出力方針は変更しません。

ケース未指定時、対象がある場合は `[target]` を使い、対象に既定選択がなければエラーです。各コンパニオンは base の `[companion.<name>]` を使います。

ケース指定時に対象がある場合、同名の `[target.case.<name>]` が必須です。各コンパニオンは `[companion.<companion-name>.case.<name>]` があれば使い、なければ base へフォールバックします。対象に存在しないケース名をコンパニオンだけが定義することは到達不能なので設定エラーです。

ケース指定時に対象がない場合、少なくとも1個のコンパニオンが同名ケースを定義する必要があります。各コンパニオンは同名ケースがあれば使い、なければ base へフォールバックします。設定インポートの `case` もこの Companion-only 規則を使い、import 先設定由来と Root 側追加の Companion を同じ import 名前空間として扱います。import 先に Target が存在しても Target Case は評価しません。

対象ケースとコンパニオンケースはいずれも完全な選択定義で、base を継承・merge しません。base 選択にある共有パターン参照も継承しないため、ケースで同じ共有パターンを使う場合はそのケース自身が同じ名前を明示的に参照します。Root と import の間でも Case や共有パターン定義を継承・merge しません。ただし Root が所有する Case Selection は、Root local の共有パターンに加えて import 由来の修飾共有パターンを明示参照できます。'''
        vocabulary_refs @= (terms.TERM_14,)

    @title('6. 対象とコンパニオン')
    class TITLE_6:
        r'''対象は省略可能です。`[target]` または `[target.case.<name>]` が存在する場合、その設定はひとつの runtime-bound 対象規則を定義します。対象の `path` は設定ファイルへ保存せず、TOML から複数の別個な対象規則を定義することもできません。

{{TERM_14}}が対象を定義する場合は CLI の位置引数 `DIRECTORY` が1個以上必須です。選択された対象定義を CLI 順に各ディレクトリへ独立して適用し、すべての runtime 対象ディレクトリは互いに異なる実ディレクトリへ解決される必要があります。{{TERM_14}}が対象を定義しない場合に位置引数 `DIRECTORY` を指定するとエラーです。import 先設定の Target は source として使用せず、CLI の `DIRECTORY` も import 先へ伝播しません。

`[target]` は `--case` を省略した実行で使う既定の対象選択です。対象は `[target]` を省略して名前付きケースだけを定義することもでき、その場合は `--case` を省略するとエラーです。

各 runtime 対象ディレクトリは実行時に存在し、その設定ファイルへ割り当てられた実行 root のファイルシステム境界規則に従って解決される必要があります。

各 `[companion.<name>]` はその設定ファイルの実行 root 相対の固定 `path`、空でない `description`、完全な base 選択定義を必須とします。{{TERM_14}}では実行 root は cwd、import 先設定では対応する import の `root` です。コンパニオンは対象の有無にかかわらず source 集合へ常に参加し、実行時にそのディレクトリが存在する必要があります。

必要なら `[companion.<name>.case.<case-name>]` に完全な代替選択を追加できます。選択ケースが存在しないコンパニオンは削除されず、base 選択へフォールバックします。'''
        vocabulary_refs @= (terms.TERM_14,)

    @title('7. 選択定義')
    class TITLE_7:
        r'''各 `[target]`、`[target.case.<name>]`、`[companion.<name>]`、`[companion.<name>.case.<case-name>]` の選択には、空でない `description` と、直接記述または共有参照による `include` / `include_if_exists` 相当の候補の少なくとも一方が必要です。

直接記述の `include` と `include_if_exists` は、それぞれ1件以上の文字列を含む必要があります。共有参照フィールドも、指定する場合は1件以上の共有名を含む文字列配列です。同一フィールド内の重複参照は拒否します。

### `include` と `include_pattern_refs`

`include` は必須 include パターンを直接記述します。`include_pattern_refs` は include 用共有パターン名を参照し、その配列を必須 include パターンとして展開します。Root が所有する Selection では Root local 名または `<import>.<pattern>` の修飾名を使用でき、import 先設定自身が所有する Companion Selection ではその設定自身のローカル名だけを使用します。通常実行では、展開後のすべての必須パターンが少なくとも1件のファイルシステム実体に一致する必要があります。0件一致はエラーです。

### `include_if_exists` と `include_if_exists_pattern_refs`

`include_if_exists` は任意 include パターンを直接記述します。`include_if_exists_pattern_refs` は include 用共有パターン名を参照し、その配列を任意 include パターンとして展開します。参照名の解決規則は `include_pattern_refs` と同じです。必須 include と同じパターン文法を使いますが、0件一致を正常として扱い、選択へ何も追加しません。

同じ共有 include パターン集合を、ある選択では `include_pattern_refs`、別の選択では `include_if_exists_pattern_refs` から参照できます。必須か任意かは共有定義ではなく参照側が決めます。

### `exclude` と `exclude_pattern_refs`

`exclude` は除外パターンを直接記述します。`exclude_pattern_refs` は exclude 用共有パターン名を参照して除外パターンを展開します。Root が所有する Selection では Root local 名または `<import>.<pattern>` の修飾名を使用でき、import 先設定自身が所有する Companion Selection ではその設定自身のローカル名だけを使用します。どちらも include によって既に選ばれた範囲の実体名だけをフィルタし、場所を選択しません。

### 展開と重複

共有参照は参照配列の順序で展開し、その後に同種の直接記述パターンを追加します。存在しない共有名の参照は設定エラーです。Root local の共有パターン参照名と import 由来の修飾参照名が同じ文字列になる場合も、どちらを選ぶか暗黙に決めず設定エラーです。展開後、必須 include 内、任意 include 内、exclude 内に同じ実効パターンが重複した場合は設定エラーです。必須 include と任意 include の両方に同じ正規化済みパターンが現れる場合も設定エラーです。

### `if_empty`

既定値は `error` です。

`if_empty = "allow"` は展開後の必須 include パターンを持たない optional-only の選択だけで指定できます。最終ファイル数が0件で空を許す場合、その対象ディレクトリをアーカイブ内の明示的な空ディレクトリエントリとして保持できます。'''

    @title('8. include パターン文法')
    class TITLE_8:
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

    @title('9. exclude パターン文法')
    class TITLE_9:
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

    @title('10. ファイルシステム境界とシンボリックリンク')
    class TITLE_10:
        r'''{{TERM_14}}では process cwd を自身の source 用 execution root / filesystem boundary とします。各{{TERM_13}}の `[import.<name>].root` は{{TERM_14}}自身の所在ディレクトリを基準に解決し、その実ディレクトリを import 先設定専用の execution root / filesystem boundary とします。

通常の Target、Companion、include、output path は自身の設定 root を越えられません。Root Configuration の boundary 外を明示できる path は import の `root` だけです。import root を確定した後、その import 先の `configuration`、Companion、選択ファイルは再び import root 内へ限定します。

使用される対象ディレクトリとすべてのコンパニオンディレクトリは存在し、それぞれを所有する設定 root 内へ解決されなければなりません。シンボリックリンク経由でその root 外へ逸脱する source path は拒否します。

選択されたファイルは、それぞれの対象またはコンパニオンディレクトリ内へ解決される必要があります。外部へ解決されるファイルシンボリックリンクは拒否します。

ディレクトリを再帰収集するとき、ディレクトリシンボリックリンクはたどりません。対象ディレクトリ外へ解決されるディレクトリリンクはエラーとし、内部へ解決されるリンクは循環と重複を防ぐため無視します。

対象には `.` としてその設定の execution root 自体を指定できます。この場合も root の内容を ZIP ルートへ平坦化せず、execution root の実ディレクトリ名を先頭要素として保持します。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_14)

    @title('11. アーカイブ計画とパス')
    class TITLE_11:
        r'''選択されたファイルは ZIP 内で、そのファイルを選択した設定ファイルの execution root から見た実際のファイルシステム相対パスを保持します。Root Configuration の local source は cwd 相対、import source はその import の `root` 相対です。

複数の source や import が同じ archive path に同じ物理ファイルを選択した場合は1回だけ書き込みます。同じ archive path が異なる物理ファイルへ対応する場合は collision error です。同じ物理ファイルが異なる execution root から異なる archive path へ対応する場合も、同じ内容を別名で黙って複製せず曖昧としてエラーにします。

アーカイブのルートには、{{TERM_14}}と使用された{{TERM_13}}、各設定の execution root、有効なケース（未指定時は `default`）、参加するディレクトリ、設定された description、実際に選択された設定位置、ディレクトリ決定方法、選択件数、必要な空結果方針など、解決済み計画の事実だけを索引する `README.md` を生成します。固定文言では生成ツール名や下流用途を示しません。用途固有の意味は root の対象・コンパニオンと import 先コンパニオンの `description` からのみ持ち込みます。

アーカイブ計画は決定的な順序で作成し、偶発的なファイルシステム列挙順序へ依存しません。'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_14)

    @title('12. 出力')
    class TITLE_12:
        r'''各設定ファイルの `[output]` は schema 上必須で、固定出力または動的命名出力のどちらか一方だけを定義します。両形式のフィールドを混在させると設定エラーです。

一回の実行で実際に計画・検証・書き込みする出力は{{TERM_14}}の `[output]` だけです。import 先設定の `[output]` は構文・field validation の対象にはなりますが、filesystem output path の解決、collision check、directory 作成、書き込みを行いません。

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

どちらの形式でも、出力ファイル自身をアーカイブ入力として選択することはできません。'''
        vocabulary_refs @= (terms.TERM_14,)

    @title('13. dry-run')
    class TITLE_13:
        r'''`--dry-run` は通常実行と同じ root source 解決、設定インポート解決、各設定のケース解決、選択、アーカイブ計画ロジックを使いますが、出力を作成・変更しません。

不足する必須 `include` は `[missing]`、不足する任意パターンは `[optional missing]` と表示します。

最終選択が0件の対象は、許可される場合 `empty, allowed`、通常実行なら空のため失敗する場合 `empty, would error` と表示します。

設定矛盾、対象と `DIRECTORY` の不整合、不正な import root / configuration path、不正な source path、存在しない root / import Companion Case、再帰 import、固定出力での `--sequence` 指定は dry-run でもエラーです。dry-run は出力を書かないため、timestamp から実出力名を確定せず、既存出力との衝突方針も適用しません。'''

    @title('14. CLI 形式')
    class TITLE_14:
        r'''Target を定義する{{TERM_14}}を1個以上の runtime ディレクトリで生成します。

```console
dirpluck DIRECTORY [DIRECTORY ...]
```

Root local source が Companion だけ、または設定インポートだけで構成される設定を生成します。

```console
dirpluck --config NAME
```

{{TERM_14}}自身の名前付きケースで生成します。Import 先 Companion 群の Case は各 `[import.<name>].case` が決めます。

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

`build` サブコマンドはなく、設定インポート用の追加 CLI path、選択規則や出力形式を一時的に上書きする CLI オプションもありません。`--sequence` は動的命名形式が定義する任意の番号位置へ実行時の値を与えるだけです。'''
        vocabulary_refs @= (terms.TERM_14,)
