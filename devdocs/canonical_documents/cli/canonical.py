from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} CLI Guide")
class TITLE_1:
    r'''この文書は `dirpluck` CLI の使い方を説明します。TOML の書き方は `CONFIGURATION.md`、解決や validation の厳密な意味論は `SPECIFICATION.md` を参照してください。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("基本形")
    class TITLE_2:
        r'''```text
{{TERM_1}} [TARGET ...] [--config PATH] [--case NAME] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
{{TERM_1}} -i PATH [-e NAME] [--case NAME] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
{{TERM_1}} --version
```

選択した{{TERM_15}}に Pluck がある場合は、1個以上の `TARGET` reference を指定します。Pluck がない場合は positional argument を指定しません。

```console
{{TERM_1}} example
{{TERM_1}} work/project-a work/project-b
{{TERM_1}} --config snapshot
```

Target reference は `NAME`、`SCOPE/NAME`、`/`、`SCOPE/` の4形です。どの形式も{{TERM_16}}から{{TERM_3}}を選びます。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_3, terms.TERM_15, terms.TERM_16)

    @title("Configuration を選ぶ")
    class TITLE_3:
        r'''Configuration document は TOML syntax を使用しますが、filename extension は `.dirpluck` です。`--config` を省略した場合だけ、runtime cwd の `default.dirpluck` を自動的に使用します。これは CLI が暗黙に探す唯一の Configuration です。

別の Configuration は `--config PATH` で明示します。`PATH` は filesystem location と同じ `/` separator の表記を使い、relative path は runtime cwd、absolute path は host filesystem を基準にします。末尾が `.dirpluck` でなければ suffix を付加するため、dot を含む document name もそのまま使えます。Windows でも CLI path separator には `\` ではなく `/` を使います。

```console
{{TERM_1}} example --config review
{{TERM_1}} example --config configs/release-1.2
{{TERM_1}} example --config ../shared/review.dirpluck
```

`--config` を指定した場合は、その path が表す1個の Configuration document だけを使用し、別 directory の同名 file を探索しません。Directory 自体を指定してその中の `default.dirpluck` を補うこともありません。Configuration document path は host OS の通常の filesystem semantics に従って解決し、symbolic link / Windows directory junction を含む path も control document の選択では特別に拒否しません。dirpluck は選択した path の absolute な表記を document location として保持し、その document 内の relative path はその location の directory を基準にします。dirpluck は file 内容から Configuration らしさを推論したり、任意の `*.dirpluck` file を自動選択・列挙したりしません。`.toml` file を Configuration として扱う互換 fallback もありません。

Output は `--preview` には不要で、実際に Archive を書き込む通常 build の root Configuration だけが自身の Output declaration を必要とします。Configuration が `about.base` で参照する Base Configuration は CLI の自動選択対象ではありません。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Invocation Template")
    class TITLE_35:
        r'''繰り返し使う CLI invocation は、{{TERM_19}}として `.dirpluck-inv` document に保存できます。1 file の `[invocation]` を default Invocation とし、`[invocation.<name>]` に名前付き Invocation entry を追加できます。

```toml
[invocation]
config = "release"
targets = ["work/frontend", "work/backend"]

[invocation.docs]
config = "release"
targets = ["docs/"]
case = "publish"
archive_mtime = "zip-epoch"
```

`config`、`targets`、`case`、`archive_mtime` は default Invocation と各 named entry のどちらでもすべて optional です。Named entry は default Invocation の差分ではなく独立した Invocation で、未指定 field を `[invocation]` から継承しません。`config` / `targets` / `case` / `archive_mtime` は field 名として予約されているため、同名の named Invocation entry は定義できません。`targets` は通常の CLI positional Target reference と同じ4形式をそのまま配列へ保存します。`config` は `--config PATH` と同じく `.dirpluck` suffix を省略でき、relative path は選択した `.dirpluck-inv` file path の directory を基準に解決します。Template file path や `config` path に symbolic link / Windows directory junction が含まれていても、control document の参照では host OS の通常の filesystem semantics に従います。`config` を省略した場合は runtime cwd の `default.dirpluck`、`targets` を省略した場合は Target なし、`case` を省略した場合は通常の default Case semantics、`archive_mtime` を省略した場合は従来の entry timestamp semantics を使います。

Template file は `-i PATH` または `--invocation-template PATH` で明示的に選びます。`PATH` は `--config` と同じ filesystem path notation を使い、relative path は runtime cwd、absolute path は host filesystem を基準にします。末尾が `.dirpluck-inv` でなければその suffix を付加します。Invocation Template document path は host OS の通常の filesystem semantics に従って解決し、選択した path の directory が Template 内 relative `config` の基準になります。Invocation Template file 自体に implicit default や別 directory の探索はありません。

`-e` / `--entry` を省略すると default `[invocation]` を選び、`-e NAME` では `[invocation.NAME]` を選びます。Named entry だけを記述した file でも TOML 上は親 `[invocation]` が成立するため、`-e` なしでは field を持たない default Invocation が選ばれます。完全に空の document は `[invocation]` 自体を持たないため無効です。

```console
{{TERM_1}} -i release
{{TERM_1}} -i release -e docs
{{TERM_1}} -i invocations/release --entry docs --case audit
{{TERM_1}} --invocation-template ../shared/release --preview
```

Field を1つも持たない Invocation も有効です。その Invocation は保存済みの実行入力を追加せず、CLI から与えた runtime value と通常の defaults を使います。成功した `--preview` または通常 build では、空の Invocation が選ばれたことを note として CLI output に表示します。これは warning ではなく、Always source だけを使う実行などが正当に成立し得る状態です。

Invocation Template は保存済み invocation を一般的に差分合成する仕組みではありません。`-i` / `--invocation-template` と positional `TARGET`、`--config` は組み合わせません。`--case NAME` は選択した Invocation の `case` を実行時に上書きでき、`--archive-mtime VALUE` は Invocation の `archive_mtime` を上書きできます。`--preview`、`--sequence`、`--archive-mtime`、`--paths` も runtime modifier として併用できます。`-e` / `--entry` は `-i` / `--invocation-template` と一緒にだけ使用できます。

`.dirpluck-inv` は Configuration ではなく、`about.base` の参照先にもなりません。選択した Invocation の Configuration / Target / Case / Archive mtime 解決後は通常の dirpluck execution と同じ semantics を使います。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_19)

    @title("Target の指定")
    class TITLE_4:
        r'''Pluck がある Configuration では、各 positional `TARGET` から解決した source directory へ同じ Pluck selection が独立して適用されます。

常設の default Scope から1 Target を選ぶ場合は directory name だけを指定します。Default Scope は常に root Configuration file の directory を root とします。Configuration を別 directory に置けば default Scope もその directory に移るため、別の Target root が必要な場合は named Scope を定義します。

```console
{{TERM_1}} acme contoso
```

名前付き Scope から選ぶ場合は `<scope>/<name>` を使います。

```console
{{TERM_1}} work/acme
```

`work/acme` は `work` Scope 直下の `acme` だけを Target とします。`work` Scope が未定義なら error で、別の relative path interpretation へ fallback しません。

Scope 直下の eligible directory をすべて Target にするには、次の expansion form を使います。

```console
{{TERM_1}} /
{{TERM_1}} work/
```

`/` は default Scope、`work/` は named Scope `work` を全展開します。`/` は filesystem root ではありません。どちらも direct child directory だけを展開し、再帰列挙しません。Scope の `ignore` に一致する directory は Target candidate から除きます。未使用の named Scope の path が現在存在しなくても、別の Scope だけを使う実行は失敗しません。

`./`、`./acme`、`/acme`、`work/team/acme`、absolute filesystem path は Target reference として受理しません。

Pluck がない Configuration は Always source など固定 source だけで実行できます。

```console
{{TERM_1}} --config project-snapshot
```

Scope と `ignore` の定義方法は `CONFIGURATION.md`、Target reference、boundary、archive path の厳密な規則は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Case")
    class TITLE_5:
        r'''名前付き{{TERM_4}}を選ぶには `--case NAME` を使います。

```console
{{TERM_1}} acme --case audit
```

1回の実行で指定する Case は1個です。Pluck と Always source が Case をどう選ぶかは `SPECIFICATION.md` に定義しています。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_4)

    @title("Preview")
    class TITLE_6:
        r'''`--preview` は Archive file を作らず、解決した ZIP contents を tree として表示します。

```console
{{TERM_1}} acme --preview
```

Configuration や workspace を変更した後、実際に Archive を書き込む前の確認に使えます。通常実行との差分は書き込みで、base chain、Scope / Target、Case、selection、archive planning の主要な解決処理は共通です。`--preview` は root Configuration に Output declaration がなくても使用できます。Output filename generation を行わないため `--sequence` とは組み合わせません。

Selection traversal で non-ignored symbolic link / Windows directory junction として認識した entry を除外した場合は、tree の後に除外件数を note として表示します。個々の path は列挙しません。正確な preview semantics と link-like entry の扱いは `SPECIFICATION.md` / `TRUST.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Archive index の source path")
    class TITLE_65:
        r'''生成される{{TERM_10}}は、既定では各 final archive root を見出しとして、その source の選択 file 数と任意の `description` を示す簡潔な index です。Scope / Pluck / Always、Configuration、Case など dirpluck 固有の resolution 情報や、source filesystem path は記録しません。

Source filesystem path も各 source section へ含めたい場合だけ `--paths` を指定します。

```console
{{TERM_1}} acme --paths
```

`--paths` は各 source section に解決済み source directory を追加します。Absolute path を含む local filesystem 情報を Archive に残し得るため、外部へ配布する Archive では必要性を確認して使用してください。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_10)

    @title("Timestamp output の sequence")
    class TITLE_7:
        r'''Timestamp output を使う Configuration で、同じ秒に複数 run を意図的に区別したい場合は正の整数 `--sequence N` を指定できます。

```console
{{TERM_1}} --config project-snapshot --sequence 2
```

`--sequence` は自動採番ではありません。Fixed output では使えません。Filename の正確な配置と collision rules は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Archive entry の mtime")
    class TITLE_75:
        r'''`--archive-mtime VALUE` は、生成する ZIP のすべての entry に1個の共通 timestamp を設定します。Configuration の `[output]` / `[output.timestamp]` には保存せず、CLI または Invocation Template の runtime policy として指定します。

```console
{{TERM_1}} example --archive-mtime 2026-01-01T00:00:00
{{TERM_1}} -i release --archive-mtime zip-epoch
{{TERM_1}} example --archive-mtime now
```

`VALUE` は次のいずれかです。

- `YYYY-MM-DDTHH:MM:SS`: timezone を持たない ZIP timestamp literal。1980-01-01T00:00:00 から 2107-12-31T23:59:59 の範囲。
- `now`: 1 run で local current time を1回だけ取得し、全 entry に同じ値を使う。
- `zip-epoch`: ZIP の最小 timestamp `1980-01-01T00:00:00` を使う。

ZIP の timestamp は2秒粒度なので、奇数秒は直前の偶数秒へ切り下げます。指定した値は生成 `README.md`、empty directory entry、source file のすべてに適用します。Option を省略した場合は従来どおり、source file は filesystem mtime、Dirpluck が生成する entry は生成時刻を使用します。

`zip-epoch` や固定 timestamp は entry timestamp による byte 差を取り除き、reproducible な Archive を作る一助になります。ただし source file の permission bits などの filesystem metadata も ZIP byte 列へ影響し得ます。Dirpluck は permission bits を正規化せず、compressor / runtime を含め Archive 全体の reproducibility をこの option だけで保証しません。`--archive-mtime` は timestamp output の filename に使う `YYYYMMDD-HHMMSS` を変更しません。`--preview` と併用できますが、Archive を書かないため preview result には影響しません。

Invocation Template では `archive_mtime = "zip-epoch"` のように保存できます。CLI で `--archive-mtime` を指定した場合は、選択した Invocation の値より CLI を優先します。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Help と version")
    class TITLE_8:
        r'''```console
{{TERM_1}} --help
{{TERM_1}} --version
```'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("終了とエラー")
    class TITLE_9:
        r'''正常終了は status 0 です。CLI argument error や dirpluck の validation / build error は status 2 で終了し、`dirpluck: error:` に続けて理由を表示します。

Archive を生成する通常実行では、成功すると output path を標準出力へ表示します。Selection traversal で symbolic link / Windows directory junction として認識した entry を除外していた場合は、その直後に除外件数を note として表示します。この runtime note は Archive 内の README には書き込みません。'''

    @title("次に読む文書")
    class TITLE_10:
        r'''- Configuration を新しく書く、または変更する: `CONFIGURATION.md`
- CLI と同じ実行 model を Python から使う: `PYTHON_API.md`
- 用語の意味を確認する: `../GLOSSARY.md`
- Configuration と filesystem 操作の trust boundary を確認する: `TRUST.md`
- base composition、matching、filesystem boundary、Archive README、output collision などを正確に確認する: `SPECIFICATION.md`'''
