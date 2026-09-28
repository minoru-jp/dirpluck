<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/changelog/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/canonical_documents/` にある日本語 canonical document はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの canonical document を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や canonical document を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck CHANGELOG

dirpluck のリリースごとの変更履歴。

## 0.13.1

公開文書の canonical source を shikumi-devdoc 0.3.2 の merge policy へ移行し、文書生成 dependency と version snapshot を同期する patch release。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。

version: 0.13.1

Changed:

- 公開文書の canonical source で deprecated な `placeholders` policy から shikumi-devdoc 0.3.2 の `merge_policy` へ移行する。外部 context に依存させない自己完結文書は `merge_policy="local"`、履歴 snapshot である CHANGELOG は `merge_policy="forbidden"` とし、文書内容を変えずに意図した merge 境界を明示する。
- 文書生成 dependency を `shikumi-devdoc>=0.3.2` に更新し、`dirpluck.__version__` と文書生成用 context / 公開 README の current-version snapshot を `0.13.1` に同期する。この release は repository-local documentation tooling と release metadata の更新であり、runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics には機能変更を加えない。

## 0.13.0

Scope の Target candidate type を `directory` / `file` / `both` から選べるようにし、Target selector を全 kind へ一般化する。あわせて Selection に full-path regular expression を使う structured `match` entry を追加する。

version: 0.13.0

Added:

- `[scope]` / `[scope.<name>]` の `target_kind` に `"both"` を追加する。Both mode は Scope 直下の eligible regular directory と regular file の両方を Target candidate とし、directory Target には effective Pluck Selection、file Target には atomic-file semantics を適用する。Pluck がない Configuration でも both-kind Scope から file だけを選ぶ run は有効だが、directory Target が1件でも解決された場合は Pluck を必要とする。
- Selection の `must` / `may` / `ignore` と Shared pattern set に `{ match = "..." }` structured entry を追加する。`match` は Selection root 配下の root-relative POSIX-style path 全体へ Python-compatible regular expression を full-match semantics で適用し、regular directory path は末尾 `/`、regular file path は末尾 `/` なしで照合する。Pattern は non-empty、512 character 以下とし、invalid regular expression は Configuration error とする。
- `must` / `may` の structured `match` は file と directory の両方を selection candidate とし、directory に一致した場合は通常の directory leaf と同じく subtree を収集する。`must` は1件以上の non-ignored selectable match を必要とし、`may` は0件 match を許容する。`ignore` の structured `match` は file を除外し、directory に一致した場合は subtree を prune する。通常 string pattern、Shared expansion、structured match が同じ file を選んでも最終 Selection では1件に deduplicate する。

Changed:

- `:[...]` / `SCOPE:[...]` と `:<...>` / `SCOPE:<...>` を file Target selector から Target selector へ一般化し、`target_kind = "directory"` / `"file"` / `"both"` のすべてで使用できるようにする。List selector は eligible direct-child Target name の literal list、regular-expression selector は file を `NAME`、directory を `NAME/` と正規化した eligible direct-child Target name 全体への Python-compatible full-match とする。
- `target_kind` を Scope 直下の Target candidate に対する type filter として整理する。Scope expansion、literal Target resolution、list selector、regular-expression selector は同じ type filter / Scope `ignore` / link-like exclusion を共有し、`both` で file と directory が混在しても resolved Target ごとの実際の type を保持する。
- 通常の Selection string pattern は従来どおり guided traversal 用の制限された grammar として維持し、structured `match` だけを表現力の高い full-path regular-expression selection とする。実装は `match` の regular expression から guided traversal plan を推論する必要はなく、Selection root 配下を走査して候補 path を照合できる。
- `ignore` は除外規則として意図的に広く扱う。通常の Selection ignore string、concrete ignore path reference、Scope ignore pattern は末尾 `/` がなければ matching file / directory の両方を除外し、末尾 `/` がある場合だけ directory に限定する。Include / Target reference を型明示へ変更しても、従来の広い exclusion semantics は維持する。File だけを除外したい場合は structured `{ match = "..." }` を使用できる。
- **Breaking:** include Selection と Target reference の file / directory 型を末尾 `/` で明示する。通常の `must` / `may` string は最終 component の末尾 `/` なしを file、末尾 `/` ありを directory とし、literal Target reference と Target list も同じ原則へ揃える。これらの参照で filesystem 上の実体型から意味を推測する従来挙動を廃止する。Directory Selection は `must = ["src/"]`、named Scope の directory Target は `work/project/` のように移行する。
- **Breaking:** default Scope では `NAME/` が named Scope expansion と衝突するため、directory Target の literal reference に `./NAME/` を導入する。`NAME` / `./NAME` は default Scope の file Target、`./NAME/` は directory Target とする。Target list は `/` を item separator と directory marker の両方に使い、途中の directory item は `NAME//NEXT`、末尾 directory item は `NAME/]` と表現し、3連以上の `/` を error とする。
- Regular-expression Target selector は file candidate を `NAME`、directory candidate を `NAME/` として照合し、`/` を pattern 内で使用可能にする。`<repo>` は file、`<repo/>` は directory、`<repo/?>` は両方を明示できる。Candidate discovery は引き続き Scope 直下だけで、regex に `/` があっても再帰探索しない。

Fixed:

- Strict entry-type migration の diagnostic を改善する。`may` string pattern が期待型では一致せず、同名 / 同patternの反対型 regular entry が存在する場合も `may` は optional missing のまま成功可能とし、source label 付きで末尾 `/` の追加または削除を案内する warning を生成する。`must` は通常 build の既存 unsatisfied error に同じ hint を含め、`--preview` では missing semantics を維持したまま warning を生成する。CLI は通常 build / `--preview` の warning を stderr へ表示し、公式 Python API は同じ内容を `RunResult.warnings` に返す。複数 source の同内容 warning は source label により区別し、Selection error の source 接頭辞は `source: detail` 形式へ整える。Literal Target の既存 error も型 marker hint を含める。
- `--preview` で未一致の structured `{ match = "..." }` expression に `/` が含まれる場合、それを archive path として分割して偽の directory tree を描画していた表示 bug を修正する。Structured match の未一致は opaque な Selection expression として別表示する。

## 0.12.0

File-kind Scope の Target reference に selector syntax を追加し、Scope 直下の regular file を明示列挙または正規表現で選べるようにする。既存の literal Target reference と全展開の意味は変更しない。

version: 0.12.0

Added:

- `target_kind = "file"` の Scope に file Target selector を追加する。`SCOPE:[name-a/name-b]` / `:[name-a/name-b]` は `/` 区切りの literal file-name list、`SCOPE:<regex>` / `:<regex>` は eligible direct-child file name 全体へ適用する regular-expression selector とする。Selector syntax は file-kind Scope だけで使用でき、directory-kind Scope では error とする。
- Regular-expression selector は Python-compatible regular expression を `fullmatch` semantics で適用する。Pattern は空を許可せず、`/` を含めず、512 character 以下とする。不正な regular expression と0件 match は error とする。Selector は Scope の `target_kind` / `ignore` / link-like exclusion で eligible file Target を確定した後に適用する。

Changed:

- File selector と既存 literal Target reference / 別 selector が同じ filesystem entry を解決した場合、その selector overlap は1 Target にまとめる。既存の literal Target reference 同士だけを重複指定した場合の distinct-entry validation は維持する。CLI と `.dirpluck-inv` の `targets` は同じ selector grammar を使用する。Shell では `[]`、`<>`、regular-expression metacharacter の解釈を避けるため selector reference 全体を quote することを推奨する。

## 0.11.1

生成 Archive README を簡潔化し、Archive path そのものから読み取れる Namespace / Source root の補助 metadata を削除する。Namespace の配置 semantics 自体は変更しない。

version: 0.11.1

Changed:

- 生成 Archive README から Namespace の説明文と、各 namespaced source section の `Namespace` / `Source root` metadata を削除する。Namespaced source は引き続き final Archive root を section heading として表示し、Namespace は従来どおり Archive placement に適用される。この変更は人間向け README の書式整理であり、Configuration、CLI、公式 Python API、Archive entry path の semantics は変更しない。README の exact formatting を機械的に解析している consumer は調整が必要になる場合がある。

## 0.11.0

Scope が direct-child regular file を Target として扱える opt-in mode を追加し、directory Target と file Target の責務境界を明確化する。既存 Scope は既定の directory mode のままとし、0.10.x Configuration の Target discovery と Archive 結果を維持する。

version: 0.11.0

Added:

- `[scope]` / `[scope.<name>]` に `target_kind = "directory" | "file"` を追加する。既定は `"directory"` で従来挙動を維持する。`"file"` の Scope は direct-child regular file だけを Target candidate とし、single Target と `SCOPE/` expansion の両方で atomic file Target として扱う。Directory、symbolic link / Windows junction、特殊 filesystem entry は file Target candidate にしない。
- Scope に optional `description` を追加する。生成 Archive README では Target section に Scope description を表示し、directory Target ではその後に Pluck description、file Target では Scope description だけを表示する。

Changed:

- Pluck の役割を directory Target の content Selection として明確化する。File Target には Pluck selection を適用せず、その regular file 自体を1個の Archive entry として収録する。Pluck がない Configuration でも file-kind Scope の file Target reference は使用できるが、directory Target は引き続き Pluck を必要とする。
- 既存 Namespace mechanism を file Target にも適用する。File Target の source root は file name 1 segment とし、Namespace がある場合は `NAMESPACE/FILENAME` を final archive file path とする。

## 0.10.2

配布物の役割を明確化し、build backend を Hatchling へ統一する。Wheel は実装と公開文書一式を提供し、sdist は release の再構築・検証に必要な完全な source を提供する。

version: 0.10.2

Changed:

- Build backend を setuptools から Hatchling へ移行する。Version は引き続き `dirpluck.__version__` を正本とし、Hatchling の version source から project metadata へ反映する。Setuptools 専用の `MANIFEST.in` と generated `*.egg-info` は配布設計から除外する。
- Wheel 専用の compact documentation を廃止する。`src/dirpluck/docs/`、`canonical_sources/package_cli/`、`canonical_sources/package_configuration/`、`canonical_sources/package_trust/`、および `canonical_documents/package/` の独立 publication channel を削除し、公開文書の二重管理をやめる。
- Wheel には実装に加えて repository の公開 `README.md`、`GLOSSARY.md`、`CHANGELOG.md`、`STATUS.md`、`docs/` 全体を `dirpluck/_docs/` 以下へ同梱する。CLI、Configuration、Python API、Trust、Specification、Glossary を同じ release の wheel だけから参照できるようにする。
- sdist は特定 directory を列挙する方式ではなく、VCS ignore rules を尊重した release source 全体を収録する方針へ変更する。`tests/`、`tools/`、`devdocs/`、公開文書、実装を含め、repository operation 専用の `.github/` は除外する。

## 0.10.1

0.10.0 の runtime behavior と公開 API / Configuration semantics を維持したまま、release metadata と公開文書を 0.10.1 release として同期する。

version: 0.10.1

Changed:

- Package version と文書の current-version snapshot を 0.10.1 へ更新する。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics の機能変更は行わない。
- Release-preparation 文書を現在の shikumi / shikumi-devdoc baseline と整合させ、STATUS の documentation tooling 記述を今回の release baseline である Shikumi 0.2.0 と shikumi-devdoc 0.3.0 に揃える。

## 0.10.0

Runtime から Output destination と overwrite policy を指定できるようにし、Configuration の抽出定義を保ったまま書き出し場所を invocation ごとに変更できるようにする。

version: 0.10.0

Added:

- CLI に `--here[=FILENAME]`、`-o PATH` / `--output PATH`、`-f` / `--force` を追加する。`--here` は runtime cwd、`--output` は runtime cwd 基準の明示 path を Output として使用し、末尾 `/` の `--output` は directory 指定として timestamp filename を自動生成する。`--here=FILENAME` は cwd 直下の filename だけを受理し、path を指定する場合は `--output` を使用する。
- 公式 Python API の `run()` に `output` と `force` を追加する。`output` は CLI `--output` と同じ path semantics を持ち、末尾 `/` なら automatic timestamp filename、末尾 `/` がなければ exact output file path とする。Relative `output` は API の `cwd` を基準に解決する。

Changed:

- Runtime Output が指定された build では root Configuration に Output declaration を要求しない。Exact runtime output はその filename をそのまま使い、automatic runtime output は root Configuration が `[output.timestamp]` を宣言している場合だけその `prefix` / `suffix` naming rule を再利用する。Root に timestamp Output がない場合は `dirpluck-YYYYMMDD-HHMMSS.zip` を既定名とする。Configuration 側の output directory / fixed path は runtime destination へ引き継がない。
- `--sequence N` は Configuration timestamp output に加えて、`--here` と末尾 `/` の runtime Output が生成する automatic timestamp filename にも適用する。Exact runtime file path と組み合わせた場合は error とする。Generated name の collision に対する自動採番・自動 rename・timestamp 再取得は行わない。
- Runtime Output の default overwrite policy は `false` とし、`--force` / `force=True` で effective Output を overwrite 可能にする。`--force` は runtime Output だけでなく Configuration の fixed / timestamp Output にも適用できる。Runtime path notation は Configuration と同じく OS にかかわらず `/` separator を使用し、backslash を受理しない。
- `--preview` / `preview=True` は Output を解決・書き込みしないため、runtime Output を指定する `--here` / `--output` / `output=`、overwrite を要求する `--force` / `force=True`、および output filename を変更する `--sequence` との組み合わせを error とする。指定した runtime Output option を preview が暗黙に無視する挙動は行わない。
- 公開文書の情報設計を整理し、README の end-to-end example を `docs/GETTING_STARTED.md` へ分離する。従来の単一 `docs/CONFIGURATION.md` は `docs/configuration/INDEX.md` を入口とする collection に分割し、overview、source、selection、base composition、Output、complete example を目的別に参照できるようにする。Wheel 同梱の compact `dirpluck/docs/CONFIGURATION.md` は引き続き1文書の quick reference として維持する。
- CLI guide も単一 `docs/CLI.md` から `docs/cli/INDEX.md` を入口とする collection へ分割し、基本操作、Invocation Template、Target / Case、preview / runtime Output を目的別に参照できるようにする。Wheel 同梱の `dirpluck/docs/CLI.md` は compact quick reference として維持する。また collection の公開 `INDEX.md` は shikumi-devdoc が生成する canonical index の翻訳に限定し、追加の説明や導線は各 `overview.md` の canonical source に置く。
- 分割後の Specification に残っていた旧 monolithic 文書の節番号参照を廃止し、Filesystem path notation、Runtime Target、Archive planning、Output など意味上の規範名で参照する。規範間の依存は循環 import を生まない範囲で `related` metadata に保持し、旧 `N節` / `Section N` 形式が再混入しない回帰テストを追加する。
- 開発文書の正本を shikumi-devdoc 0.3.0 の現行 authoring contract へ同期する。Nested title は `@title(...)` ではなく `title @= ...` に統一し、各 canonical source で `heading="title"` / `heading="identity"` を明示する。テストから直接検証する文書断片は `code_field` ではなく presentation を持たない `test_target_field` に分離し、Markdown fence は docstring 側へ置く。Vocabulary term は既定で Glossary 公開とし、冗長な `glossary @= True` を削除する。Specification は stable related target を維持するため identity heading policy を使用する。

## 0.9.1

Target と Always source が同じ physical material を独立した役割で含められるようにし、Archive planning と生成 README の重複表現を修正する。

この version は PyPI へ公開しなかった development milestone です。

version: 0.9.1

Fixed:

- Target と Always source が同じ physical file を選択して異なる Archive path へ配置する場合に ambiguity error として拒否していた制約を解除する。Target の Pluck と Always source の Selection は physical overlap の有無にかかわらず独立して評価し、Target 側の `ignore` や未選択結果によって Always source を抑止しない。同じ archive path に異なる physical file が衝突する場合は引き続き error とし、同じ archive path に同じ physical file が重なる場合は1回だけ書き込む。Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合は、生成 Archive README の Always source section に Target 側の final Archive root と重複 file 数を表示する。

## 0.9.0

1.0 に向けて Configuration language の語彙と filesystem model を整理し、公開設定面を新しい Pluck / Scope / Always / Base / Output model へ移行する。Development Status を Beta へ進める。

version: 0.9.0

Changed:

- Configuration vocabulary を全面的に整理する。`[target]` を `[pluck]`、`[companion.<name>]` を `[always.<name>]`、Target location を Configuration-level の `[scope]` / `[scope.<name>]` へ変更する。Selection は `include` / `include_if_exists` / `exclude` を `must` / `may` / `ignore`、`if_empty` を boolean `allow_empty` へ置き換える。旧 schema の compatibility layer は設けない。
- Configuration layering を `[about].base` による linear base chain へ単純化する。旧 `[import.<name>]`、`root`、`configuration` と import overlay Companion を廃止し、relative filesystem path は `about.base`、Scope、Always source、Output のいずれも、その field を記述した Configuration file の directory を基準に解決する。Base から継承した definition は outer Configuration の位置へ rebase しない。
- Target discovery を独立した Scope 群として整理する。Default Scope は常に root Configuration directory を探索 root とし、`[scope]` はその optional `ignore` を設定する。名前付き Scope は `path` で追加の探索 root を定め、base chain では同名 named Scope を outer layer が definition 全体で shadow する。CLI Target reference は `NAME`、`SCOPE/NAME`、`/`、`SCOPE/` の4形式とし、`/` は default Scope の direct-child expansion を表す。Scope `ignore` は単一選択と全展開の両方へ適用する。
- Shared pattern を `[shared.must]` / `[shared.may]` / `[shared.ignore]` の3 namespace に分け、専用 `*_pattern_refs` field を廃止する。Selection array の通常 string を direct pattern、1要素 nested array (`["name"]`) を同じ field の Shared reference として解釈し、effective Shared namespace で展開する。
- Output を fixed `[output]` と timestamp `[output.timestamp]` の排他的な2 mode に整理する。Fixed output は concrete file `path` と optional `overwrite` を持ち、`overwrite` の既定値は `false` とする。Timestamp output は末尾 `/` を持つ directory `path` と optional `prefix` / `suffix` を使い、旧 `directory` と boolean `timestamp = true` を廃止する。
- Base chain 上の Output について static writable destination を検証する。Fixed output は完全 file path、timestamp output は output directory tree を書き込み境界とし、同一 fixed file、重なる timestamp directory、timestamp boundary 内の fixed file を conflict とする。同じ directory に異なる filename の fixed output を置くことは許可する。実際に書き込むのは引き続きルート設定ファイル自身の Output だけとする。
- Project metadata の Development Status classifier を `3 - Alpha` から `4 - Beta` へ変更する。
- Filesystem traversal で symbolic link をたどる挙動を廃止する。Scope 直下の symbolic link は Target candidate にせず、Selection 内の file / directory symbolic link も selectable entry とせず Archive に含めない。明示 Target reference が symbolic link を指す場合は error とし、`must` / `may` pattern が symbolic link だけに一致する場合はそれぞれ required missing / optional missing として扱う。
- Output declaration を Configuration 単体の schema では optional にする。Output を持たない Configuration は共通 Base として利用でき、root Configuration でも Archive planning / `--preview` には Output を要求しない。実際に Archive file を書き込む build では root 自身の fixed または timestamp Output を直接宣言しなければならず、Base の Output は継承しない。Base chain の write-boundary validation には Output を実際に宣言した layer だけが参加する。
- Selection の内部表現を、Shared reference を保持する parse 済み `SelectionDefinition` と、effective Shared namespace で展開済みの `Selection` に分離する。parse 前後の状態を1つの object に二重保持していた `must_items` / `may_items` / `ignore_items` と、それに伴う型抑制・自己代入を廃止する。
- 現在の Configuration model に合わせて semantic test module と package-interface test の名称・対象を整理する。過去の release 段階を表す test 名ではなく、現在検証している Configuration semantics / effective-Configuration boundary を名前に使用する。
- 異なる resolved source が同じ final archive root に解決された場合、selected file が直接衝突しなくても黙って同一 directory へ merge せず error とする。衝突回避は明示的な Namespace で行い、自動 suffix や Scope / Always 名による暗黙 qualification は行わない。Namespace を使用する Archive README では final Archive root を見出しとし、Namespace / Source root を metadata として分け、Namespace が元 source path ではなく Archive 専用の outer directory であることを明示する。
- Archive を書き込まず生成予定内容を確認する CLI option を `--dry-run` から `--preview` へ変更する。互換 alias は設けない。また `--help` の positional `TARGET` 説明に `NAME`、`SCOPE/NAME`、`/`、`SCOPE/` の4形式と、それぞれ default / named Scope の単一選択・全展開であることを明示する。
- `--preview` と内部 `plan_archive()` は root Configuration に Output declaration がなくても Archive contents を解決できるようにする。実際に file を書き込む `build_archive()` だけが root 自身の Output を要求する。`--preview` は output filename generation を行わないため `--sequence` と同時指定できない。
- Configuration 候補を推論・一覧表示する `--configs` を廃止する。CLI が暗黙に選ぶ Configuration は runtime cwd の `default.dirpluck` だけに限定し、単独の別名 Configuration を implicit default として選ばず、file 内容から Configuration らしさを判定する heuristic discovery も行わない。別名または別 directory の Configuration は `--config PATH` で明示する。互換 alias は設けない。
- Configuration document の identity を `.toml` から `.dirpluck` extension へ移行する。内容の syntax は引き続き TOML とする。`--config` 省略時に暗黙使用する document は runtime cwd の `default.dirpluck` だけとし、`about.base` も concrete `.dirpluck` path を要求する。`.toml` Configuration、旧 `dirpluck.toml`、旧 `./dirpluck/` discovery location への compatibility alias / fallback は設けない。
- Invocation の `case` を固定値ではなく default Case として扱い、`-i` / `--invocation-template` と CLI `--case` を併用できるようにする。CLI `--case` が指定された場合は選択した default / named Invocation の `case` より優先し、CLI 側を省略した場合だけ Invocation の値を使用する。
- CLI の Configuration / Invocation Template path で `Path.suffix` による extension 判定をやめ、required suffix が末尾になければ `.dirpluck` / `.dirpluck-inv` をそのまま付加する。これにより `--config release-1.2` は cwd の `release-1.2.dirpluck`、`--config configs/release-1.2` は cwd の `configs/release-1.2.dirpluck`、`-i set-2.1` は cwd の `set-2.1.dirpluck-inv` を選び、stem 内の dot を不正 extension として拒否しない。
- CLI の document selection を単純化し、`--config` を省略した場合に自動選択する Configuration を runtime cwd の `default.dirpluck` だけへ限定する。`./.dirpluck/` は reserved discovery / control directory として扱わず、`.dirpluck` という directory name に Scope semantics 上の special case も持たせない。`--config PATH` と `-i PATH` は Configuration の filesystem-location notation と同じ `/` separator、glob / backslash なしの path 表記を受理し、relative path は runtime cwd、absolute path は host filesystem から1個の document を直接選ぶ。Directory 指定から default document を補完せず、別 location の同名 file を探索・ambiguity 解決しない。Default Scope root は常に Root Configuration file の directory とする。
- Configuration / Invocation Template の control document path は host OS の通常の filesystem semantics に従う形へ整理する。cwd の `default.dirpluck`、`--config PATH`、`-i PATH`、`[about].base`、Invocation の `config` では symbolic link / Windows directory junction を含む path も通常の filesystem semantics で扱い、選択・参照した lexical absolute path を document location として保持する。Relative reference はその location の directory を基準にし、Base chain の cycle detection のように file identity が必要な内部判定だけ実体 path を使う。Source tree の symbolic link / junction 非 traversal policy は独立した extraction boundary として維持する。
- Invocation の `config` path も CLI `--config PATH` と同じ suffix completion を行うようにし、`.dirpluck` を省略可能にする。`config = "configs/release-1.2"` は Template document の directory を基準に `configs/release-1.2.dirpluck` を参照する。`[about].base` は Configuration schema 内の explicit document reference として `.dirpluck` extension 必須のままとする。
- Source root と traversal entry の link handling を整理する。Configuration が `[scope.<name>].path` / `[always.<name>].path` で明示した root location は host OS の通常の filesystem semantics で解決し、symbolic link / Windows directory junction を含む location も root として使用できる。一方、解決した root から Dirpluck が自動的に行う Target discovery / Selection traversal では link-like entry を引き続き選択・走査しない。Always source の Archive source root は alias の実体 directory name へ置き換えず、Configuration に明示した lexical source location の name / relative path を保持する。
- Pluck / Always source / Case selection の `description` を必須 metadata から任意 metadata へ変更する。Selection の成立条件は `must` / `may` candidate と `allow_empty` policy だけで決まり、`description` を省略しても抽出意味論は変わらない。Archive README の source index は table ではなく final Archive root ごとの section とし、selected file 数を metadata、任意の `description` を section body として表示する。これにより複数行の description も table cell へ圧縮せず保持する。
- 文書開発 workspace を `_internal/document_source` / `_internal/document_build/ja` から公開 repository structure の `devdocs/` へ再編する。Canonical Python source は `devdocs/canonical_documents/`、shikumi-devdoc へ渡す repository configuration は `devdocs/config/`、日本語 intermediate Markdown は `devdocs/intermediate_documents/` に配置する。`canonical_documents` 自体を import package とし、Vocabulary 由来の生成 `terms.py` はその package root に置く。Intermediate documents は repository publication path を mirror し、wheel-facing artifacts は `package/` namespace に分離する。`devdocs/README.md` も canonical source から生成する。`devdocs/` は sdist に含め、wheel からは除外する。
- Output の concurrent-writer boundary を明確化する。Fixed output の `overwrite = false` と timestamp output は既存 destination を build 前および最終配置前に検査するが、この check と final placement は別 process に対する atomic な no-clobber operation ではない。同じ output path への concurrent write は dirpluck の調停対象外とし、並行実行する呼び出し側が異なる destination を割り当てる。実装の output policy 自体は変更しない。

Fixed:

- ZIP 作成時に selected file の mtime が ZIP format の timestamp 範囲外でも traceback せず、範囲内へ clamp して Archive を作成できるようにする。また selected file を Archive へ追加する際に `OSError` が発生した場合は `SelectionError` として扱い、CLI が raw traceback を表示せず一時 Archive を残さないようにする。
- Scope handling を単純化し、default Scope を root Configuration directory に常設する。これにより `[scope.<name>]` の TOML 親 table と明示 `[scope]` を区別する補助的な text detection を不要にする。また named Scope root の存在・directory validation はその Scope を Target resolution / expansion に実際に使用するときまで遅延し、未マウントなどで利用不能な未使用 Scope が別 Scope の実行を失敗させないようにする。
- Selection の directory `ignore` を再帰走査後の後処理 filter ではなく traversal-time pruning として適用する。Ignore 対象 directory の内部を列挙しないため、大きな ignored subtree の不要な走査を避け、内部の entry による traversal-time error も発生させない。
- README と wheel 同梱 Configuration quick reference の機密 file 除外例に `[pluck]` table header を追加し、`ignore = [...]` をそのまま top-level key として貼り付けて Configuration error になる曖昧さをなくす。
- 内部の `resolve_sources` / `plan_archive` / `build_archive` が受け取っていた `cwd` 引数を削除する。これらの引数は存在確認だけを行い resolution には使用されておらず、Configuration-relative path を制御できるように見える誤解を招いていた。Runtime cwd は implicit `default.dirpluck` selection と CLI で指定する relative document path の基準にだけ残し、source / Output resolution は引き続き各 Configuration file の位置だけを基準にする。
- Generated archive index が使用する root-level `README.md` を予約 path とし、resolved source の final archive root が case-insensitive にその path 自身またはその配下へ解決される場合は Archive 作成前に error とする。Namespace 名だけを特別扱いせず、Namespace なしの source root にも同じ規則を適用する。
- Default Scope の `ignore` / `namespace` は root-local であり base composition されないことを Configuration 文書で明示する。Base に `[scope]` を書くこと自体は有効で、その Configuration 自身を Root として使用した場合だけ default Scope 設定として適用される。
- Symbolic link の非 traversal policy を Windows directory junction にも拡張し、Python 3.11 でも `lstat` の reparse tag から junction を認識できる共通 helper を使用する。Selection traversal で認識して Archive から除外した link-like entry は path を列挙せず件数だけを `--preview` と通常 build の CLI output に note として表示する。`must` pattern が link-like entry だけに一致した場合は単なる `no matches` ではなく、link-like entry が selectable でないことを示す error にする。TRUST 文書では platform 固有の未知の link-like mechanism を完全には検出保証しないこと、および第三者 extractor の展開時解釈を dirpluck が保証しないことを明記する。
- 型検査で見つかった内部の型不整合を修正する。Effective Configuration validation では Scope binding と Always binding の loop 変数を別名にして異なる binding 型を混同しないようにし、Configuration table の key validation helper は実際の TOML table に合わせて `Mapping[str, object]` を受け取る。Windows 固有の `stat_result.st_reparse_tag` は `getattr` で取得し、type checker が非 Windows の `stat_result` に存在しない属性への直接参照として扱わないようにする。Runtime behavior と公開 API は変更しない。
- Archive build の Output preflight を archive planning より前へ戻す。Root Output の有無、`--sequence` の妥当性、解決済み output path、既存 output に対する overwrite policy を先に検証し、失敗が確定している build で大きな source tree を走査しないようにする。Planning 後にしか判定できない「output 自身が selected input に含まれる」検査と、directory 作成・ZIP 書き込みなどの副作用は引き続き planning 後に行う。
- Selection `ignore` の優先順位を明確化し、ignored entry は link-like entry としての skipped count や link-only `must` error の根拠にしない。`must` が ignored entry にしか一致しない場合は通常の unsatisfied pattern として扱い、directory `ignore` で枝刈りした subtree と同様に「無視する」という Configuration の明示指示を runtime diagnostics より優先する。
- Windows directory junction の safety boundary を fail-closed にする。対応 Windows runtime で `IO_REPARSE_TAG_MOUNT_POINT` または `st_reparse_tag` を取得できない場合に junction 判定を黙って無効化せず error とし、Windows CI の junction integration test は junction 作成失敗を skip せず test failure として扱う。
- CLI が skipped-link count を受け取るための build-and-plan helper を内部名へ戻し、Python module の公開面に新しい API を増やさない。あわせて Ruff の preview E3 blank-line rule (`E301`〜`E306`) を explicit rule として repository の lint 設定へ追加し、`src` / `tests` / `tools` の空行を整える。Runtime behavior と package-root public interface は変更しない。
- Selection が扱う filesystem object の境界を regular file / regular directory に明確化する。FIFO、socket、device などその他の non-regular entry は Archive に含めず、directory traversal 中や optional `may` match では静かに除外する。`must` pattern が non-ignored special entry だけに一致した場合は単なる `no matches` ではなく、unsupported special filesystem entry が selectable でないことを示す理由付き error にする。`ignore` に一致した special entry は種類別 diagnostic より先に除外する。
- 空の `.dirpluck-inv` document に対する diagnostic を `[invocation]: expected a table` から `[invocation] table is required` へ変更し、required table 自体の欠落と、`invocation = ...` のような table 型違いを区別する。Field を持たない空の `[invocation]` table は引き続き有効とする。
- `[invocation.config]`、`[invocation.targets]`、`[invocation.case]` を field value の型 error として報告していた ambiguity を解消する。`config` / `targets` / `case` は root Invocation の field 名として予約し、named Invocation entry name には使用できないことを schema と diagnostic で明示する。
- Filesystem-location notation で backslash を拒否する diagnostic に、host OS が Windows の場合も `/` を path separator として使用することを明示する。受理する path grammar 自体は変更せず、CLI の `--config PATH` / `-i PATH` と Configuration / Invocation Template 内の filesystem-location field で共通の説明を返す。
- Atomic Output write に使用する temporary file の `0600` mode が、そのまま final ZIP の permission になる実装依存を解消する。Temporary output を通常の new regular file と同じ creation mode で作成し、POSIX では process `umask` を適用した mode を final Archive へ保持する。`overwrite = true` でも既存 destination の mode は継承せず、その run の新規 file creation semantics を使用する。

Added:

- Archive placement 専用の名前付き `[namespace.<name>]` definition を追加する。Namespace は現時点では属性を持たない空 table とし、名前そのものを Archive directory component とする。Default / named Scope と Always source は optional `namespace = "<name>"` で effective Namespace を参照でき、指定した source の通常 source root の外側へ Namespace を常に追加する。
- 繰り返し使う CLI invocation を保存する `.dirpluck-inv` Invocation Template document と、`-i PATH` / `--invocation-template PATH`、`-e NAME` / `--entry NAME` を追加する。1 file は root `[invocation]` を default Invocation、`[invocation.<name>]` を named Invocation entry として複数の呼び出しを保持できる。各 Invocation は optional `config` / `targets` / `case` / `archive_mtime` を独立して持ち、named entry は root から field を継承しない。CLI では cwd 基準の relative path または absolute path で Template file を明示選択し、`-e` 省略時は root、指定時は named entry を選ぶ。Relative `config` path は Template file 自身の directory 基準とする。Field を持たない Invocation も有効で CLI runtime value と normal defaults を使い、成功した preview / build では note を表示する。Template 使用時は positional Target / `--config` の override や一般的な差分合成を提供しない一方、`--case` と `--archive-mtime` は選択した Invocation の保存値を実行時に上書きできる。`--preview` / `--sequence` / `--archive-mtime` / `--paths` も runtime modifier として併用できる。
- Selection `ignore` に Selection-root-relative の concrete path reference を追加する。`ignore = [["./tests/fixtures/big.bin"], ["./src/generated/"]]` のように、1要素 nested array の string を `./` で始めた場合は Shared ignore reference ではなく path reference として解釈する。Pluck では Target root、Always source ではその source root を基準とし、末尾 `/` で directory を明示する。Path reference は Selection root 内へ限定し、`..`、absolute path、glob、backslash を拒否する。Name pattern / Shared ignore / path reference の semantic overlap は error とせず除外条件の和として扱い、directory reference は subtree traversal 前に prune できる。
- Beta 公開面として最小の公式 Python API を package root に追加する。`dirpluck.run()` は CLI と同じ Configuration / Target / Case / Invocation Template / Entry / preview / output semantics を programmatic に実行し、`RunResult` で output path、preview tree、Archive entry、生成 README、link-like skip count、空 Invocation の状態を返す。公式 package-root export は `run`、`RunResult`、`DirpluckError`、`__version__` に限定し、builder / config / invocation などの低 level module は引き続き互換性保証対象外とする。CLI は argparse 後に同じ application layer を呼ぶ adapter とする。
- Archive entry timestamp を runtime で統一する `--archive-mtime VALUE` と Invocation Template の `archive_mtime` field を追加する。`VALUE` は `YYYY-MM-DDTHH:MM:SS`、`now`、`zip-epoch` を受理し、CLI value は選択した Invocation の保存値を上書きする。`now` は1 run で local current time を1回だけ取得し、`zip-epoch` は ZIP 最小 timestamp `1980-01-01T00:00:00` を使う。ZIP の2秒粒度に合わせて奇数秒を切り下げ、generated README / empty directory / source file の全 entry へ同じ timestamp を設定する。Option を省略した場合は従来の entry timestamp behavior を維持する。固定 mtime は timestamp 差を取り除き reproducible な Archive を作る一助になるが、source file の permission bits など他の metadata は正規化せず、Archive 全体の byte-for-byte reproducibility は保証しない。

## 0.8.0

Target discovery を direct-child model に単純化し、cwd / Target location ごとに Target candidate directory を `skip` できるようにする。

version: 0.8.0

Changed:

- CLI Target reference を `NAME`、`LOCATION/NAME`、`LOCATION/` の3形式へ限定する。cwd Target と location Target はそれぞれ resolution base の直下 directory だけを対象とし、`work/team/project` のような多階層 Target、`.`、`./project` を受理しない。`LOCATION/NAME` の location が未定義の場合は cwd-relative path へ fallback せず error とする。これにより Target の内部 directory が別の Target として再帰的に解決される状態をなくす。
- Target の archive root は cwd / location のどちらから選んだ場合も direct child directory name 1 segment とし、logical location 名を archive path へ含めない。Named-location expansion は `skip` 適用後の eligible direct child directory だけを展開し、0件なら error とする。

Added:

- `[target].skip` と `[target.location.<name>].skip` を追加する。前者は cwd 直下、後者は各 location 直下の Target candidate directory name に適用し、explicit Target reference と `LOCATION/` expansion の両方から一致 directory を除外する。Pattern は case-sensitive な exact (`name`)、prefix (`name*`)、suffix (`*name`)、substring (`*name*`) を受理し、file selection の `exclude` とは独立させる。

## 0.7.0

Target を Configuration workspace から独立して配置できるようにし、named Target location と logical CLI reference による Target resolution を導入する。

version: 0.7.0

Added:

- `[target.location.<name>]` を追加する。Location は Target definition に属する named filesystem base で、relative `path` はその Target definition を所有する Configuration layer の execution root、absolute `path` は host filesystem 上の directory を参照する。Outer Target が inner Target を shadow すると、Case と同様に location 集合も Target definition 全体とともに置き換わる。
- `<location>/` の形を named-location expansion として追加する。対応する location 直下の directory だけを独立した runtime Target として展開し、再帰列挙や regular file の Target 化は行わない。未定義 location、0 directory の展開、location boundary 外へ解決する directory symbolic link は error とする。複数の通常 Target reference と expansion は同じ run で併用できる。

Changed:

- CLI positional argument を raw directory path ではなく Target reference として解決する。`work/project` の先頭 segment が effective Target location 名と一致すれば残りをその location から解決し、一致しなければ従来どおり cwd 相対で解決する。`./work/project` は location lookup を明示的に回避する。Absolute positional Target reference は受理せず、cwd 外の Target には Target location を使用する。
- Target location から解決した Target の archive path は logical location 名を含めず、location directory から見た filesystem-relative path を保持する。cwd-relative Target は引き続き cwd からの relative path を保持する。どちらの Target も最終的に解決された Target directory 自体を file selection boundary とする。

## 0.6.2

0.6.1 公開後の文書配布を微調整し、共有前の注意を入口文書へ戻すとともに、wheel だけでも trust model を参照できるようにする。実装上の挙動変更はない。

version: 0.6.2

Changed:

- README と wheel 同梱の Configuration quick reference に、外部へ渡す Archive の selection を確認する短い注意と `exclude = [".git/", ".env*", "*.pem", "*.key"]` の例を追加する。`docs/TRUST.md` 自体も wheel に同梱し、簡易文書から trust model へ直接到達できるようにする。

## 0.6.1

LLM-assisted work の位置付けと Configuration の trust boundary を文書上で明確化し、過剰な再現可能性の表現を取り除く。実装上の挙動変更はない。

version: 0.6.1

Added:

- `docs/TRUST.md` を追加し、Configuration を filesystem 操作の実行指示として扱うこと、dirpluck は参照先の機密性や操作の適切さを推論して補正しないこと、OS permission と明示された path が実際の権限境界であることをまとめて説明する。Source boundary や schema validation などの structural checks と、内容や意図を判断する guard を区別する。

Changed:

- README の LLM-assisted work の説明を、非ローカルの対話型 LLM へ upload する Archive、またはローカル agent workspace へ配置する Archive を準備する用途として明確化する。LLM が dirpluck を直接操作することを前提とするように読める表現を削除し、trust model の詳細は `docs/TRUST.md` へ集約する。
- README から `reproducibly` / 「再現可能」の売り文句を削除する。dirpluck の価値は TOML に明示した selection intent から必要な file をまとめることとして説明し、ZIP byte stream の再現性を示唆する専門的な意味を持たせない。

## 0.6.0

Filesystem location の表現力を拡張し、Archive README を配布向けの単純な索引へ整理するとともに、Configuration 全体の説明を記述できるようにする。

version: 0.6.0

Changed:

- Configuration の filesystem location は OS にかかわらず `/` separator で記述する。Companion `path`、import `root`、Root output の `path` / `directory` は host OS が認識する absolute path を受理し、relative path では field ごとの基準に従って `.` / `..` を扱う。別 OS の absolute-root notation への変換、`~` expansion、environment-variable interpolation は行わない。Include pattern と imported `configuration` は引き続き relative path に限定し、backslash を拒否する。
- Companion が Configuration execution root の外側を含む任意の実在 source directory を relative `..` または absolute `path` で直接参照できるようにする。解決済み Companion source directory 自体を selection boundary とし、include や symbolic link からその外へ逸脱することは引き続き拒否する。Resolution base 外の Companion は解決済み source directory の最終 directory name を archive root とし、host の absolute path、drive、UNC share 名を archive path へ埋め込まない。
- Archive root の `README.md` を dirpluck の resolution report から単純な contents index へ変更する。各 resolved source は final Archive root を見出しとして、selected file 数と任意の `description` を section body に記録する。description は table cell に圧縮せず複数行も保持する。Target / Companion、Case、Configuration chain、execution root などの dirpluck 固有情報や source filesystem path は既定では含めず、CLI `--paths` を指定した場合だけ各 source section に解決済み source directory を追加する。

Added:

- 任意の `[about].description` を追加する。Configuration chain では outermost layer から inward に探索して最初に定義された値を effective description とし、存在する場合は Archive README の見出し直下、contents index の前へ表示する。Chain 全体に定義がない場合は全体説明を省略する。

## 0.5.2

公開文書体系を用途ごとに再構成し、語彙を概念上の基盤として分離するとともに、wheel には実行時に必要な最小限の参照文書だけを収録する。

version: 0.5.2

Changed:

- 公開文書を `README.md`、`GLOSSARY.md`、`CHANGELOG.md` と `docs/CLI.md`、`docs/CONFIGURATION.md`、`docs/SPECIFICATION.md` に整理する。従来の `USAGE.md` は廃止し、CLI 操作と TOML Configuration の記述方法をそれぞれ専用文書へ分離する。README は用途と導入判断、Glossary は概念、各 `docs/` 文書は必要時に読む詳細という役割を明確にする。
- `GLOSSARY.md` から個数制約、shadowing、path 規則、validation などの仕様詳細を外し、文書体系で共有する概念定義に限定する。厳密な挙動は `docs/SPECIFICATION.md` に集約し、CLI と Configuration のガイドでは作業に必要な範囲だけを説明して、より詳細な意味論へは参照を設ける。
- wheel の同梱文書を、簡潔な `dirpluck/docs/CLI.md` と `dirpluck/docs/CONFIGURATION.md` の2つへ変更する。完全な Glossary、詳細ガイド、Specification、文書正本、日本語中間文書は sdist から参照できる構成を維持し、実行時の軽量な参照と詳細調査の導線を分離する。

## 0.5.1

0.5.0 の実効 Target binding を修正し、Target 定義の origin layer に依存せず runtime directory を CLI から受け取る一貫したモデルへ戻す。

version: 0.5.1

Fixed:

- 実効設定に Target が存在する場合、Target 定義がルート設定ファイル自身または import chain 内側のどちらに由来していても CLI `DIRECTORY` を1個以上必須とする。0.5.0 で導入した imported Target の Configuration placement から project directory を推定する規則と、imported Target への CLI `DIRECTORY` 禁止を廃止する。Target Selection は chain で名前解決し、runtime Target directory は常にルート設定ファイルの execution root 内で解決する。

## 0.5.0

Configuration import を1本の linear layering として一般化し、Target、Companion、共有パターンを import 先から import 元へ同じ名前解決規則で構成できるようにする。

version: 0.5.0

Changed:

- 各 Configuration が持てる `[import.<name>]` を最大1個に限定する一方、import 先からさらに1個の Configuration を import する linear chain を許可する。chain の深さには上限を設けず、同じ解決済み Configuration file が現在の chain に再登場した場合だけ循環参照として拒否する。
- Configuration chain を最深部から最外側へ解決して実効設定を作る。Target は singleton 名 `target`、Companion と共有パターンは各自の名前で解決し、外側の同名定義が内側の定義全体を shadow する。共有パターン参照は最終的な実効名前空間で解決し、0.4.x の `<import>.<pattern>` 修飾名前空間を名前解決の必須モデルとして扱わない。
- import chain で最終的に残った Target を実行対象として使用できるようにする。ルート設定ファイル自身の Target が残る場合は従来どおり CLI `DIRECTORY` を束縛し、import 由来 Target が残る場合はその Target を定義した Configuration の project directory を `dirpluck.toml` または `dirpluck/<name>.toml` の配置から解決する。外側 Target が存在する場合は内側 Target とその Case をまとめて shadow する。
- Case 選択を import ごとの独立指定から実効設定全体への1個の選択へ整理し、`[import.<name>].case` を使用しない。最終的な Target / Companion 定義に対して CLI `--case` を適用し、source が shadow された場合はその source の Case 定義も一緒に置き換える。
- 最終出力は引き続きルート設定ファイル自身の `[output]` だけを使用し、import chain 内側の output は実行しない。0.4.x の再帰 import 禁止に伴うバージョン固定エラー文言を廃止し、循環参照は解決 chain を示す version-independent な Configuration error として扱う。

## 0.4.1

現在のパッケージバージョンを `dirpluck.__version__` に一本化し、文書生成ではそこから生成した外部 JSON context を利用する。

version: 0.4.1

Changed:

- 現在のリリース番号を用語集の語彙として保持する方式を廃止する。文書生成用の外部 context JSON は `dirpluck.__version__` から生成し、README など現在バージョンを必要とする文書は `version` context 値を参照する。CHANGELOG の各リリース番号は履歴情報として canonical source に直接記述する。

## 0.4.0

import 先 Configuration の共有 include / exclude パターンを、import 名前空間付きで Root 側から明示的に再利用できるようにする。

version: 0.4.0

Added:

- 設定インポートで読み込んだ Configuration の `[shared.include_patterns]` / `[shared.exclude_patterns]` を、ルート設定ファイル側から `<import-name>.<pattern-name>` の修飾名で参照できるようにする。Root local の共有パターンは従来どおりローカル名で参照し、include / exclude の種別は分離したまま維持する。
- import 由来の修飾共有パターンを、ルート設定ファイルが所有する Target、Root Companion、`[import.<name>.companion.<name>]` の base / Case Selection から利用できるようにする。import 先 Configuration 自身が宣言する Companion は、引き続きその Configuration 自身の共有パターンをローカル名で解決し、Root 側の名前空間へ再束縛しない。
- Root local の共有パターン名と import 由来の修飾共有パターン名が同じ参照文字列になる場合は、暗黙の優先順位を設けず設定エラーにする。共有パターンは import によって merge・自動適用されず、各 Selection が参照名を明示する既存モデルを維持する。

## 0.3.0

別ディレクトリの dirpluck Configuration が宣言する Companion を明示的に取り込み、各 Configuration の境界を保ったままひとつのアーカイブへ統合できるようにする。

version: 0.3.0

Added:

- 設定インポートを導入する。ルート設定ファイルの `[import.<name>]` に `root`、`configuration`、必要に応じて `case` を記述し、別の dirpluck 設定ファイルが宣言する Companion の抽出結果を同じ archive plan へ統合できるようにする。Root Configuration はローカル source を持たず設定インポートだけで構成することもできる。
- 設定インポートの `root` を、ルート設定ファイルの cwd 境界を明示的に越えられる唯一の path として定義する。`root` はルート設定ファイル自身の所在ディレクトリからの相対 path に限定し、POSIX / Windows / UNC の絶対指定を OS にかかわらず拒否する。import root を解決した後は、`configuration`、import 先 Companion、選択ファイルをその root 内へ再び限定し、各 Configuration が独立した filesystem boundary を持つようにする。
- ルート設定ファイルの CLI `DIRECTORY` と `--case` を import 先へ暗黙に伝播させず、import 先の Target は使用しない。`case` は import 先 Companion 群だけへ独立して適用する。import 先設定の `[output]` は schema validation だけを行って実行時には使用せず、最終出力はルート設定ファイルの `[output]` だけとする。0.3.0 では import 先からさらに設定を import する再帰構成を拒否する。
- Archive path を、各ファイルを選択した Configuration の execution root から見た相対 path として統合する。同じ archive path に同じ物理ファイルが重なる場合は1回だけ格納し、異なる物理ファイルが同じ archive path へ衝突する場合、または同じ物理ファイルが異なる archive path へ解決される場合は曖昧としてエラーにする。アーカイブ README には使用した設定インポートと各 execution root を記録する。
- 設定インポートではルート設定ファイルから `[import.<name>.companion.<companion-name>]` を定義し、import root 内の追加 source を Target ではなく Companion として取り込めるようにする。import 配下の Companion は import 先設定由来か Root 側追加かにかかわらず `<import>.<companion>` の論理名を持ち、同じ import 内での重複を拒否する。Root 側追加 Companion は Root の shared pattern を、import 先設定由来 Companion は import 先の shared pattern を使用し、`path = "."` によって import root 自体を Companion として選べる。

## 0.2.0

共有パターンを導入し、抽出条件をケース間や source 間で明示的に再利用できるようにする。

version: 0.2.0

Added:

- 共有パターンを導入する。`[shared.include_patterns]` と `[shared.exclude_patterns]` に `name = [...]` の形で名前付きパターン集合を定義し、対象またはコンパニオンの base / case 選択から `include_pattern_refs` / `include_if_exists_pattern_refs` / `exclude_pattern_refs` で明示的に参照できるようにする。共有パターンは参照した選択にだけ追加され、base から case への継承や暗黙の merge、source 間の自動適用は行わない。
- include 用の共有パターンは include のパターン文法で、exclude 用の共有パターンは exclude のパターン文法で検証する。include 用の共有パターンは `include_pattern_refs` から必須候補、`include_if_exists_pattern_refs` から任意候補として参照でき、exclude 用は `exclude_pattern_refs` から参照できる。いずれも直接記述した `include` / `include_if_exists` / `exclude` と併用できる。
- sdist をリリースの再構築・検証に使えるソース配布物として拡充し、従来の tests と公開文書に加えて `_internal/` の文書正本・日本語中間文書と `tools/` の同期・配布検証ツールを収録する。`_internal/`、`tools/`、tests、`.github/` は wheel へ含めない。
- 実行時に必要な操作規則を短く確認できる公開 `USAGE.md` を追加する。文書は正本から日本語中間文書を生成して英訳する既存フローで管理し、リポジトリルート、sdist、および wheel の `dirpluck/docs/USAGE.md` に収録する。wheel に同梱する文書は `USAGE.md` のみに整理し、`README.md`、`CONFIGURATION.md`、`GLOSSARY.md`、`SPECIFICATION.md` は sdist またはリポジトリで提供する。

## 0.1.0

最初の公開リリース。

version: 0.1.0

Added:

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
