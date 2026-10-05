<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/changelog/current.py` です。
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

dirpluck 0.10.0 以降のリリース履歴。0.9.x 以前の履歴は [Changelog Archive](docs/changelog/INDEX.md) を参照してください。

## 0.16.0

0.15.0 で予定していた公開変更を未公開のまま取り込み、Always / Case / Targetless run の契約更新と、内部実行 pipeline の責務再編をまとめて公開する breaking release。

version: 0.16.0

Changed:

- **Compatibility policy:** 0.10.0 以降に掲げていた「公開 surface の Breaking Change を原則として避ける」という pre-1.0 方針を取り下げる。実運用から 1.0 前に修正すべき中核設計が残っていることが確認されたため、残りの 0.x series は 1.0 の公開契約を収束させる期間とし、必要な Breaking Change を許容する。可能な場合は deprecation、migration warning、Migration Guide を提供するが、旧設計を互換性のためだけに固定しない。1.0.0 で安定した互換性契約へ移行する。
- **Release numbering:** 0.15.0 は公開せず、そこで予定していた変更を 0.16.0 に統合する。0.14.x からの upgrade は `docs/migration/0.16.md` を基準とし、0.15.0 を経由する必要はない。
- **Internal architecture:** CLI / Configuration / Invocation の入力解釈と正規化、filesystem からの実体抽出、Archive / message 出力を明確な3段階として再構成する。Base、Shared、Namespace、Case、Target grammar などの入力言語上の概念は正規化段階で可能な限り消費し、抽出層は typed な Target / Selection / fixed source と filesystem semantics に限定する。Archive planning と ZIP writer も分離し、writer は確定済み payload だけを受け取る。Canonical な CLI / Configuration / Invocation grammar と、明示的に変更した項目を除く selection / archive semantics は維持する。
- **Specification / test structure:** 公開 Specification から内部 object、処理 phase、具体的 algorithm を固定する記述を除き、公開 contract、pre-1.0 compatibility、implementation invariant を分離する。Test suite も public contract、0.x compatibility、内部 characterization、architecture invariant を区別し、内部実装の置換が公開契約を不必要に固定しない構造へ整理する。
- 異なる Scope が同じ filesystem directory へ解決されること自体は Configuration error としない。Scope は名前によって明示的に選択できるため、重複した physical root は許可し、実際の重複 source や Archive path collision は Target / Archive planning の通常の規則で扱う。
- Base chain の inactive な Output definition 同士について write-boundary overlap を検証して Configuration 全体を拒否する規則を削除する。実際の run で有効な Output は root Configuration の Output だけとし、その Output と input / Archive の安全性を実行時に検証する。
- **Breaking:** `[always.<name>]` の `<name>` を Always source の final Archive directory identity とする。`path` は filesystem 上の source directory / Selection root だけを指定し、path の basename や Configuration directory からの relative path は Archive root の決定に使用しない。たとえば `[always.docs] path = "../external/documentation"` は `docs/` の下へ source directory からの relative selected path を配置する。Always name は TOML key として解釈された後、1個の Archive directory component として扱う。dirpluck は host OS 固有の予約名や filename rule を独自判定しない。
- `[always.<name>].namespace` は 0.16.x 以降の 0.x series では pre-1.0 compatibility として受理し、指定した Namespace name が `<name>` を置き換えた effective Always name として Archive placement に使用される。旧来の `NAMESPACE/SOURCE_ROOT` prefix semantics は Always には適用しない。Always namespace を検出した場合は公開 `AlwaysMigrationWarning`（CLI では同内容の stderr warning）で、この field が 1.0.0 で削除されることと、目的の Archive directory name を `[always.<name>]` に直接記述する移行先を必ず案内する。Unknown Namespace reference は引き続き Configuration error とする。
- Final Archive root を destination region identity として整理する。Target 同士と Always 同士は引き続き大文字小文字を区別しない比較で一意とする一方、Target と Always が完全に同じ spelling の root を持つ場合は同じ destination region への composition として共有を許可する。Target `App` と Always `app` のように casefold 後だけ一致する別 spelling は曖昧なので error とし、共有 region 内の実 entry collision は Archive planner の通常の collision rule で検出する。
- Always `path` は concrete directory path であり、解決した directory 自体を Selection boundary とすることを明確化する。Archive identity が Always name から得られるため、source-root name を導出できないことだけを理由に filesystem root を Always source として拒否していた制限は削除する。Selection traversal の link-like entry / special entry handling は変更しない。
- **Breaking grammar change with migration path:** Pluck Case の canonical syntax を `[pluck.case.<name>]` から `[case.pluck.<name>]` へ移す。0.16.0 から 1.0.0 未満では旧 `[pluck.case.<name>]` も同じ semantics で互換受理し、公開 `ConfigurationDeprecationWarning`（CLI では stderr migration notice）で新構文への移行を案内する。同じ Configuration document で同名 Case を新旧両構文へ重複定義した場合は error とし、1.0.0 で legacy syntax を削除する。
- Runtime Case selector を Pluck / Always の独立2軸へ変更する。`--case PLUCK` は Pluck Case だけ、`--case .ALWAYS` は Always Case だけ、`--case PLUCK.ALWAYS` は両方を指定する。CLI、`dirpluck.run(case=...)`、Invocation の `case` field は同じ grammar を使用する。Case validity は参加 source 数から独立して判定し、定義済み Case の結果が0 sourceでも README-only Archive として正常に扱う。
- Archive directory identity の名前検証から host OS 固有の予約名や filename rule を模倣する portable 保証を外し、TOML / Configuration と Archive identity の責務を分離する。Always / Namespace name は1個の Archive directory component として必要な最小条件だけを検証し、OS 間での展開可否は利用者の責任とする。一方、一般的な case-insensitive 展開での衝突を避けるため、Namespace definition、Always effective name、resolved Target archive root の一意性は大文字小文字を区別せず判定し、実際の Archive spelling は保持する。
- Generated Archive README の情報構造を整理する。Always source はすべて Target より先に表示し、各 source の `description` は `Files` / `Source` / overlap metadata より先に置く。Target は Scope 単位にまとめ、directory Target はその Scope の Pluck group 配下へ final Archive path を列挙することで、同じ Scope / Pluck description を Target ごとに繰り返さない。File Target は Pluck を使わないため Scope 直下に置く。README 冒頭では `Scope: "..."` が Target の選択範囲だけを表し、優先度・重要度・階層関係を意味しないことを明記し、追加の意味がある場合は Scope `description` に記述する。これは人間向け generated README の presentation / context 改善であり、Selection、Archive entry path、CLI / Python API の機械可読 contract は変更しない。

Added:

- Always Case を `[case.always.<name>]` として追加する。Always Case は個々の Always Selection を上書きせず、Base composition 後の effective Always source 集合を `include` または `exclude` で filter する。両 field は同時指定不可、`include = []` は明示的な0件選択、`exclude = []` または両 field 未指定は全 source 参加とする。参照名は TOML 上の Always identifier とし、未定義参照は effective composition 後に Configuration error とする。
- Positional Target reference を常に0個以上として扱い、resolved source が0件でも正常に build / preview できるようにする。Targetless run では Pluck を source selection に参加させず、Always source があればそれらだけを解決し、Always source もなければ generated `README.md` だけの Archive を生成する。CLI は source 0件を warning ではなく通常の informational output として表示し、Python API は `RunResult.archive_entries == ("README.md",)` と generated README の注記から同じ結果を観測できる。Targetless Pluck-only run では named Pluck Case を指定しても source 0件の正常結果を許可する一方、未定義 Case は引き続き error とする。この変更は従来 error だった入力を新たに受理する後方互換な機能追加とする。
- 0.16.0 から 1.0.0 直前まで、0.14.x で有効だった Always source の旧 Archive identity と 0.16.x の effective Always name を比較し、実際に Archive root が変わる source だけへ公開 `AlwaysMigrationWarning` を報告する。Warning には旧 root と新 root を含め、Python API では標準 warnings framework、CLI では同じ診断を stderr から確認できる。旧・新 identity が一致する Always には layout warning を出さない。Namespace 使用時は layout 差分の有無とは独立して 1.0.0 での削除を案内する compatibility warning を報告する。0.16 migration guide では旧 `path` / Namespace placement と新しい Always-name-based placement の before/after を示す。

Fixed:

- Archive directory identity の最小 validation から誤って外していた ASCII control character と backslash の拒否を復元する。U+0000..U+001F と U+007F は ZIP entry name の切り詰めや warning / preview 表示崩れを防ぐため拒否し、`\` は `/` と同様に path separator として解釈され得るため1個の Archive directory component に受理しない。これは host OS 固有の予約名を模倣する portable policy ではなく、Archive path の構造と identity を保持するための format-level safety rule とする。
- Scope 全展開で directory enumeration が `OSError` になった場合と、generated `README.md` / empty-directory entry の ZIP 書き込みが `OSError` になった場合を、他の filesystem / Archive I/O failure と同じ `SelectionError` に正規化する。CLI ではこれらの失敗を traceback ではなく通常の `dirpluck: error:` diagnostic として報告し、未完成の Output / temporary output を残さない。
- Windows host で drive root filesystem location（例: `C:/`）を正規化した際に trailing root separator を失って `C:` へ変換し、Configuration directory 相対の drive-relative path として扱う場合があった不具合を修正する。Host が受理する Windows absolute drive-root notation は `/` separator のまま root identity を保持する。あわせて Windows CI で全 test suite を実行し、control-document absolute path、source byte newline、generated README の source path 表示、junction inspection の test expectation を host-independent にする。

## 0.14.1

Ruff と basedpyright の既存 static-analysis policy に source tree を適合させる保守 release。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。

version: 0.14.1

Changed:

- 既存の Ruff policy に従って source、test、documentation canonical source、repository tool の lint violation を解消する。空行と未使用 import を整理し、`TargetIgnorePattern` の type annotation 用 import を明示し、canonical document renderer の import placement を通常の module import block へ揃える。あわせて basedpyright の error diagnostics を解消し、Python 3.11 を解析基準として明示しつつ repository-local test helper import を `tests.*` の package-qualified form に統一する。Runtime source では archive tree の再帰型と内部 builder import を明示化し、test source では Optional / union の narrowing と意図的な不正型入力を局所的に型付けする。この release は静的解析上の整合性を改善する保守 refactor であり、runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。
- basedpyright の warning diagnostics も repository の用途別に整理し、`src` を解析 path に追加したうえで、documentation canonical source の宣言型 DSL、test の副作用目的 call、package 内部 private helper など意図的な pattern だけを execution environment ごとの policy として限定する。残る warning は TOML / JSON / argparse など dynamic boundary の `Any` / `Unknown` を `object` と明示的な narrowing / cast で封じ込め、deprecated typing import、暗黙 string literal concatenation、validation-only return value、test helper annotation を静的に明確化して 0 error / 0 warning にする。参照されない内部 helper `_resolve_target_both` は dead code として削除する。これらは型情報と repository-local validation の明確化だけを目的とし、runtime behavior と公開 contract は変更しない。
- 肥大化していた CHANGELOG を shikumi-devdoc の document collection 方針に沿って分割する。Repository root の `CHANGELOG.md` は 0.10.0 以降の現行履歴と安定した公開 URL を維持し、0.9.x と 0.1.0〜0.8.0 の履歴は `docs/changelog/` の archive collection へ移す。Archive の `INDEX.md` は各 canonical source の `order` / `summary` metadata から生成し、公開 `docs/` tree と同じ構造で wheel にも同梱する。
- `_effective.py` に集中していた Effective Configuration 処理を処理 phase ごとに分割する。Target / Scope reference と selector の解決を `_target_resolution.py`、base/shared/namespace と Scope root / Output boundary を含む Configuration 合成・検証を `_configuration_composition.py`、request/case/Always と resolved source の最終 orchestration を `_effective.py` に配置する。新しい private module 間の内部 interface は module-level public name として明示し、package の公式 Python API は拡張しない。この変更は内部責務と依存方向を明確化する保守 refactor であり、Target resolution、Configuration composition、Archive semantics を変更しない。
- Ruff formatter を repository の正式な Python formatter として採用し、`line-length = 100` を基準に `src/`、`tests/`、`tools/` を統一 format する。Canonical source は Python syntax を使う文書 DSL で raw document content の indentation も意味を持つため formatter 対象から除外し、`ruff check .` の lint 対象には引き続き含める。CI と local release check では `ruff format --check src tests tools` を品質 gate として実行し、formatter version を quality dependency group で固定する。
- GitHub Actions の品質 gate を reusable `.github/workflows/checks.yml` へ集約する。共通 checks は Ruff format、Ruff lint、basedpyright、canonical document drift、Python 3.11〜3.14 の `unittest` matrix を実行し、Python 3.13 では従来の `discover -s tests` 形式も互換確認する。通常 CI は共通 checks と distribution build/metadata/contents verification を分離し、release workflow は release tag と dynamic package version の一致を先に検証したうえで同じ checks を release tag に対して再利用し、成功した distribution artifact だけを smoke test 後に PyPI Trusted Publishing へ渡す。`tools/check_release.py` も同じ format/lint/type/test/document gate を local で再現する。

Fixed:

- `tests` が package であることに合わせ、repository-local helper import を `tests._temp` / `tests._builder_support` / `tests._config_support` の package-qualified form に統一する。これにより従来の `python -m unittest discover -s tests` と repository root を top-level にする `python -m unittest discover -s tests -t .` の両方で同じ test suite を実行できるようにする。Helper lookup のためだけに追加していた `[tool.pytest.ini_options] pythonpath = ["tests"]` と basedpyright の `tests` extra path は不要になったため削除する。

## 0.14.0

Selection reference syntax を明示的な structured inline table へ移行し、従来の1要素 nested array を互換入力として非推奨化する。

version: 0.14.0

Added:

- `must` / `may` の Shared reference に `{ shared = "name" }` inline table を追加する。`ignore` でも `{ shared = "name" }` を使用し、reference namespace は従来どおり記述 field から `shared.must` / `shared.may` / `shared.ignore` に決定する。Shared reference の解決時期と base composition 後の rebinding semantics は変更しない。
- `ignore` の concrete Selection-relative path に `{ path = "relative/path" }` inline table を追加する。`path` は Selection root 基準の relative path に限定し、absolute path、`..`、glob、backslash を拒否する。先頭の `./` と path 内の `.` component は正規化し、`{ path = "foo" }` と `{ path = "./foo" }` を同じ path として扱う。末尾 `/` による directory-only semantics と subtree pruning は従来の concrete path reference と同じとする。
- GitHub Actions の CI / release workflow を追加する。CI は `main` push / pull request で Python 3.11〜3.14 の test matrix、canonical document drift check、wheel / sdist build、distribution metadata / contents check を行う。GitHub Release の `published` event では release tag と package version を照合し、Python 3.13 で canonical check と test suite を再実行してから distribution を build・検証し、isolated environment で built wheel を smoke test した同一 artifact を PyPI Trusted Publishing で公開する。CI と local で同じ文書検証 dependency を導入できるよう `.[test]` optional dependency を追加する。

Changed:

- 1要素 nested array による Shared reference (`["name"]`) と `ignore` concrete path reference (`["./path"]`) は 0.14.0 から非推奨とし、1.0.0 で削除する。0.14.0 以上 1.0.0 未満では互換入力として引き続き受理するが、CLI は旧記法を含む読み込み済み Configuration file ごとに1回だけ stderr へ warning を表示し、`{ shared = "..." }` / `{ path = "..." }` への移行と 1.0.0 での削除を案内する。Base chain の Configuration も対象とし、warning は stdout と exit status を変更しない。
- 公式 Python API の `dirpluck.run()` でも deprecated nested-array Configuration syntax を検出し、読み込んだ Configuration file ごとに公開 `ConfigurationDeprecationWarning` (`FutureWarning` subclass) を報告する。Python の既定 filter で表示され、warning location は dirpluck package 外の最初の caller frame に帰属させる。Base chain も対象とする。Configuration syntax の lifecycle warning は planning diagnostic と分離し、`RunResult.warnings` には含めない。CLI は同じ diagnostic を従来どおり stderr へ整形表示し、CLI 実行時に追加の Python warning は発行しない。
- 公開 source repository を `https://github.com/minoru-jp/dirpluck` として package metadata と文書 navigation に反映する。Root README の公開文書 link は GitHub `main` branch 上の absolute URL に変更し、PyPI の project description からも解決できるようにする。`pyproject.toml` の `[project.urls]` に Homepage、Documentation、Repository、Issues、Changelog を追加し、STATUS の distribution note も公開後の状態へ更新する。

Fixed:

- `pyproject.toml` に `[tool.pytest.ini_options] pythonpath = ["tests"]` を追加し、editable install 済みの source checkout で `pytest` を直接実行した場合も `tests/_temp.py` など repository-local test helper を収集できるようにする。公式 CI runner は引き続き `unittest` とする。

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
