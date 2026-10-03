from shikumi_devdoc.fields.changelog import added, changed, fixed, version
from shikumi_devdoc.norms.common import canonical_source
from shikumi_devdoc.norms.document import title


@canonical_source('dirpluck CHANGELOG', filename='CHANGELOG.md', merge_policy="forbidden", heading="title")
class CHANGELOG:
    r"""
    dirpluck 0.10.0 以降のリリース履歴。0.9.x 以前の履歴は [Changelog Archive](docs/changelog/INDEX.md) を参照してください。
    """

    class RELEASE_25:
        r"""
        Ruff と basedpyright の既存 static-analysis policy に source tree を適合させる保守 release。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。
        """
        title @= '0.14.1'

        version @= '0.14.1'

        changed @= '既存の Ruff policy に従って source、test、documentation canonical source、repository tool の lint violation を解消する。空行と未使用 import を整理し、`TargetIgnorePattern` の type annotation 用 import を明示し、canonical document renderer の import placement を通常の module import block へ揃える。あわせて basedpyright の error diagnostics を解消し、Python 3.11 を解析基準として明示しつつ repository-local test helper import を `tests.*` の package-qualified form に統一する。Runtime source では archive tree の再帰型と内部 builder import を明示化し、test source では Optional / union の narrowing と意図的な不正型入力を局所的に型付けする。この release は静的解析上の整合性を改善する保守 refactor であり、runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。'

        changed @= 'basedpyright の warning diagnostics も repository の用途別に整理し、`src` を解析 path に追加したうえで、documentation canonical source の宣言型 DSL、test の副作用目的 call、package 内部 private helper など意図的な pattern だけを execution environment ごとの policy として限定する。残る warning は TOML / JSON / argparse など dynamic boundary の `Any` / `Unknown` を `object` と明示的な narrowing / cast で封じ込め、deprecated typing import、暗黙 string literal concatenation、validation-only return value、test helper annotation を静的に明確化して 0 error / 0 warning にする。参照されない内部 helper `_resolve_target_both` は dead code として削除する。これらは型情報と repository-local validation の明確化だけを目的とし、runtime behavior と公開 contract は変更しない。'

        changed @= '肥大化していた CHANGELOG を shikumi-devdoc の document collection 方針に沿って分割する。Repository root の `CHANGELOG.md` は 0.10.0 以降の現行履歴と安定した公開 URL を維持し、0.9.x と 0.1.0〜0.8.0 の履歴は `docs/changelog/` の archive collection へ移す。Archive の `INDEX.md` は各 canonical source の `order` / `summary` metadata から生成し、公開 `docs/` tree と同じ構造で wheel にも同梱する。'

        changed @= '`_effective.py` に集中していた Effective Configuration 処理を処理 phase ごとに分割する。Target / Scope reference と selector の解決を `_target_resolution.py`、base/shared/namespace と Scope root / Output boundary を含む Configuration 合成・検証を `_configuration_composition.py`、request/case/Always と resolved source の最終 orchestration を `_effective.py` に配置する。新しい private module 間の内部 interface は module-level public name として明示し、package の公式 Python API は拡張しない。この変更は内部責務と依存方向を明確化する保守 refactor であり、Target resolution、Configuration composition、Archive semantics を変更しない。'

        changed @= 'Ruff formatter を repository の正式な Python formatter として採用し、`line-length = 100` を基準に `src/`、`tests/`、`tools/` を統一 format する。Canonical source は Python syntax を使う文書 DSL で raw document content の indentation も意味を持つため formatter 対象から除外し、`ruff check .` の lint 対象には引き続き含める。CI と local release check では `ruff format --check src tests tools` を品質 gate として実行し、formatter version を quality dependency group で固定する。'

        changed @= 'GitHub Actions の品質 gate を reusable `.github/workflows/checks.yml` へ集約する。共通 checks は Ruff format、Ruff lint、basedpyright、canonical document drift、Python 3.11〜3.14 の `unittest` matrix を実行し、Python 3.13 では従来の `discover -s tests` 形式も互換確認する。通常 CI は共通 checks と distribution build/metadata/contents verification を分離し、release workflow は release tag と dynamic package version の一致を先に検証したうえで同じ checks を release tag に対して再利用し、成功した distribution artifact だけを smoke test 後に PyPI Trusted Publishing へ渡す。`tools/check_release.py` も同じ format/lint/type/test/document gate を local で再現する。'

        fixed @= '`tests` が package であることに合わせ、repository-local helper import を `tests._temp` / `tests._builder_support` / `tests._config_support` の package-qualified form に統一する。これにより従来の `python -m unittest discover -s tests` と repository root を top-level にする `python -m unittest discover -s tests -t .` の両方で同じ test suite を実行できるようにする。Helper lookup のためだけに追加していた `[tool.pytest.ini_options] pythonpath = ["tests"]` と basedpyright の `tests` extra path は不要になったため削除する。'

    class RELEASE_24:
        r"""
        Selection reference syntax を明示的な structured inline table へ移行し、従来の1要素 nested array を互換入力として非推奨化する。
        """
        title @= '0.14.0'

        version @= '0.14.0'

        added @= '`must` / `may` の Shared reference に `{ shared = "name" }` inline table を追加する。`ignore` でも `{ shared = "name" }` を使用し、reference namespace は従来どおり記述 field から `shared.must` / `shared.may` / `shared.ignore` に決定する。Shared reference の解決時期と base composition 後の rebinding semantics は変更しない。'

        added @= '`ignore` の concrete Selection-relative path に `{ path = "relative/path" }` inline table を追加する。`path` は Selection root 基準の relative path に限定し、absolute path、`..`、glob、backslash を拒否する。先頭の `./` と path 内の `.` component は正規化し、`{ path = "foo" }` と `{ path = "./foo" }` を同じ path として扱う。末尾 `/` による directory-only semantics と subtree pruning は従来の concrete path reference と同じとする。'

        added @= 'GitHub Actions の CI / release workflow を追加する。CI は `main` push / pull request で Python 3.11〜3.14 の test matrix、canonical document drift check、wheel / sdist build、distribution metadata / contents check を行う。GitHub Release の `published` event では release tag と package version を照合し、Python 3.13 で canonical check と test suite を再実行してから distribution を build・検証し、isolated environment で built wheel を smoke test した同一 artifact を PyPI Trusted Publishing で公開する。CI と local で同じ文書検証 dependency を導入できるよう `.[test]` optional dependency を追加する。'

        changed @= '1要素 nested array による Shared reference (`["name"]`) と `ignore` concrete path reference (`["./path"]`) は 0.14.0 から非推奨とし、1.0.0 で削除する。0.14.0 以上 1.0.0 未満では互換入力として引き続き受理するが、CLI は旧記法を含む読み込み済み Configuration file ごとに1回だけ stderr へ warning を表示し、`{ shared = "..." }` / `{ path = "..." }` への移行と 1.0.0 での削除を案内する。Base chain の Configuration も対象とし、warning は stdout と exit status を変更しない。'

        changed @= '公式 Python API の `dirpluck.run()` でも deprecated nested-array Configuration syntax を検出し、読み込んだ Configuration file ごとに公開 `ConfigurationDeprecationWarning` (`FutureWarning` subclass) を報告する。Python の既定 filter で表示され、warning location は dirpluck package 外の最初の caller frame に帰属させる。Base chain も対象とする。Configuration syntax の lifecycle warning は planning diagnostic と分離し、`RunResult.warnings` には含めない。CLI は同じ diagnostic を従来どおり stderr へ整形表示し、CLI 実行時に追加の Python warning は発行しない。'

        fixed @= '`pyproject.toml` に `[tool.pytest.ini_options] pythonpath = ["tests"]` を追加し、editable install 済みの source checkout で `pytest` を直接実行した場合も `tests/_temp.py` など repository-local test helper を収集できるようにする。公式 CI runner は引き続き `unittest` とする。'

        changed @= '公開 source repository を `https://github.com/minoru-jp/dirpluck` として package metadata と文書 navigation に反映する。Root README の公開文書 link は GitHub `main` branch 上の absolute URL に変更し、PyPI の project description からも解決できるようにする。`pyproject.toml` の `[project.urls]` に Homepage、Documentation、Repository、Issues、Changelog を追加し、STATUS の distribution note も公開後の状態へ更新する。'

    class RELEASE_23:
        r"""
        公開文書の canonical source を shikumi-devdoc 0.3.2 の merge policy へ移行し、文書生成 dependency と version snapshot を同期する patch release。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics は変更しない。
        """
        title @= '0.13.1'

        version @= '0.13.1'

        changed @= '公開文書の canonical source で deprecated な `placeholders` policy から shikumi-devdoc 0.3.2 の `merge_policy` へ移行する。外部 context に依存させない自己完結文書は `merge_policy="local"`、履歴 snapshot である CHANGELOG は `merge_policy="forbidden"` とし、文書内容を変えずに意図した merge 境界を明示する。'

        changed @= '文書生成 dependency を `shikumi-devdoc>=0.3.2` に更新し、`dirpluck.__version__` と文書生成用 context / 公開 README の current-version snapshot を `0.13.1` に同期する。この release は repository-local documentation tooling と release metadata の更新であり、runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics には機能変更を加えない。'

    class RELEASE_22:
        r"""
        Scope の Target candidate type を `directory` / `file` / `both` から選べるようにし、Target selector を全 kind へ一般化する。あわせて Selection に full-path regular expression を使う structured `match` entry を追加する。
        """
        title @= '0.13.0'

        version @= '0.13.0'

        added @= '`[scope]` / `[scope.<name>]` の `target_kind` に `"both"` を追加する。Both mode は Scope 直下の eligible regular directory と regular file の両方を Target candidate とし、directory Target には effective Pluck Selection、file Target には atomic-file semantics を適用する。Pluck がない Configuration でも both-kind Scope から file だけを選ぶ run は有効だが、directory Target が1件でも解決された場合は Pluck を必要とする。'

        changed @= '`:[...]` / `SCOPE:[...]` と `:<...>` / `SCOPE:<...>` を file Target selector から Target selector へ一般化し、`target_kind = "directory"` / `"file"` / `"both"` のすべてで使用できるようにする。List selector は eligible direct-child Target name の literal list、regular-expression selector は file を `NAME`、directory を `NAME/` と正規化した eligible direct-child Target name 全体への Python-compatible full-match とする。'

        changed @= '`target_kind` を Scope 直下の Target candidate に対する type filter として整理する。Scope expansion、literal Target resolution、list selector、regular-expression selector は同じ type filter / Scope `ignore` / link-like exclusion を共有し、`both` で file と directory が混在しても resolved Target ごとの実際の type を保持する。'

        added @= 'Selection の `must` / `may` / `ignore` と Shared pattern set に `{ match = "..." }` structured entry を追加する。`match` は Selection root 配下の root-relative POSIX-style path 全体へ Python-compatible regular expression を full-match semantics で適用し、regular directory path は末尾 `/`、regular file path は末尾 `/` なしで照合する。Pattern は non-empty、512 character 以下とし、invalid regular expression は Configuration error とする。'

        added @= '`must` / `may` の structured `match` は file と directory の両方を selection candidate とし、directory に一致した場合は通常の directory leaf と同じく subtree を収集する。`must` は1件以上の non-ignored selectable match を必要とし、`may` は0件 match を許容する。`ignore` の structured `match` は file を除外し、directory に一致した場合は subtree を prune する。通常 string pattern、Shared expansion、structured match が同じ file を選んでも最終 Selection では1件に deduplicate する。'

        changed @= '通常の Selection string pattern は従来どおり guided traversal 用の制限された grammar として維持し、structured `match` だけを表現力の高い full-path regular-expression selection とする。実装は `match` の regular expression から guided traversal plan を推論する必要はなく、Selection root 配下を走査して候補 path を照合できる。'

        changed @= '`ignore` は除外規則として意図的に広く扱う。通常の Selection ignore string、concrete ignore path reference、Scope ignore pattern は末尾 `/` がなければ matching file / directory の両方を除外し、末尾 `/` がある場合だけ directory に限定する。Include / Target reference を型明示へ変更しても、従来の広い exclusion semantics は維持する。File だけを除外したい場合は structured `{ match = "..." }` を使用できる。'

        changed @= '**Breaking:** include Selection と Target reference の file / directory 型を末尾 `/` で明示する。通常の `must` / `may` string は最終 component の末尾 `/` なしを file、末尾 `/` ありを directory とし、literal Target reference と Target list も同じ原則へ揃える。これらの参照で filesystem 上の実体型から意味を推測する従来挙動を廃止する。Directory Selection は `must = ["src/"]`、named Scope の directory Target は `work/project/` のように移行する。'

        changed @= '**Breaking:** default Scope では `NAME/` が named Scope expansion と衝突するため、directory Target の literal reference に `./NAME/` を導入する。`NAME` / `./NAME` は default Scope の file Target、`./NAME/` は directory Target とする。Target list は `/` を item separator と directory marker の両方に使い、途中の directory item は `NAME//NEXT`、末尾 directory item は `NAME/]` と表現し、3連以上の `/` を error とする。'

        changed @= 'Regular-expression Target selector は file candidate を `NAME`、directory candidate を `NAME/` として照合し、`/` を pattern 内で使用可能にする。`<repo>` は file、`<repo/>` は directory、`<repo/?>` は両方を明示できる。Candidate discovery は引き続き Scope 直下だけで、regex に `/` があっても再帰探索しない。'

        fixed @= 'Strict entry-type migration の diagnostic を改善する。`may` string pattern が期待型では一致せず、同名 / 同patternの反対型 regular entry が存在する場合も `may` は optional missing のまま成功可能とし、source label 付きで末尾 `/` の追加または削除を案内する warning を生成する。`must` は通常 build の既存 unsatisfied error に同じ hint を含め、`--preview` では missing semantics を維持したまま warning を生成する。CLI は通常 build / `--preview` の warning を stderr へ表示し、公式 Python API は同じ内容を `RunResult.warnings` に返す。複数 source の同内容 warning は source label により区別し、Selection error の source 接頭辞は `source: detail` 形式へ整える。Literal Target の既存 error も型 marker hint を含める。'

        fixed @= '`--preview` で未一致の structured `{ match = "..." }` expression に `/` が含まれる場合、それを archive path として分割して偽の directory tree を描画していた表示 bug を修正する。Structured match の未一致は opaque な Selection expression として別表示する。'

    class RELEASE_21:
        r"""
        File-kind Scope の Target reference に selector syntax を追加し、Scope 直下の regular file を明示列挙または正規表現で選べるようにする。既存の literal Target reference と全展開の意味は変更しない。
        """
        title @= '0.12.0'

        version @= '0.12.0'

        added @= '`target_kind = "file"` の Scope に file Target selector を追加する。`SCOPE:[name-a/name-b]` / `:[name-a/name-b]` は `/` 区切りの literal file-name list、`SCOPE:<regex>` / `:<regex>` は eligible direct-child file name 全体へ適用する regular-expression selector とする。Selector syntax は file-kind Scope だけで使用でき、directory-kind Scope では error とする。'

        added @= 'Regular-expression selector は Python-compatible regular expression を `fullmatch` semantics で適用する。Pattern は空を許可せず、`/` を含めず、512 character 以下とする。不正な regular expression と0件 match は error とする。Selector は Scope の `target_kind` / `ignore` / link-like exclusion で eligible file Target を確定した後に適用する。'

        changed @= 'File selector と既存 literal Target reference / 別 selector が同じ filesystem entry を解決した場合、その selector overlap は1 Target にまとめる。既存の literal Target reference 同士だけを重複指定した場合の distinct-entry validation は維持する。CLI と `.dirpluck-inv` の `targets` は同じ selector grammar を使用する。Shell では `[]`、`<>`、regular-expression metacharacter の解釈を避けるため selector reference 全体を quote することを推奨する。'

    class RELEASE_20:
        r"""
        生成 Archive README を簡潔化し、Archive path そのものから読み取れる Namespace / Source root の補助 metadata を削除する。Namespace の配置 semantics 自体は変更しない。
        """
        title @= '0.11.1'

        version @= '0.11.1'

        changed @= '生成 Archive README から Namespace の説明文と、各 namespaced source section の `Namespace` / `Source root` metadata を削除する。Namespaced source は引き続き final Archive root を section heading として表示し、Namespace は従来どおり Archive placement に適用される。この変更は人間向け README の書式整理であり、Configuration、CLI、公式 Python API、Archive entry path の semantics は変更しない。README の exact formatting を機械的に解析している consumer は調整が必要になる場合がある。'

    class RELEASE_19:
        r"""
        Scope が direct-child regular file を Target として扱える opt-in mode を追加し、directory Target と file Target の責務境界を明確化する。既存 Scope は既定の directory mode のままとし、0.10.x Configuration の Target discovery と Archive 結果を維持する。
        """
        title @= '0.11.0'

        version @= '0.11.0'

        added @= '`[scope]` / `[scope.<name>]` に `target_kind = "directory" | "file"` を追加する。既定は `"directory"` で従来挙動を維持する。`"file"` の Scope は direct-child regular file だけを Target candidate とし、single Target と `SCOPE/` expansion の両方で atomic file Target として扱う。Directory、symbolic link / Windows junction、特殊 filesystem entry は file Target candidate にしない。'

        added @= 'Scope に optional `description` を追加する。生成 Archive README では Target section に Scope description を表示し、directory Target ではその後に Pluck description、file Target では Scope description だけを表示する。'

        changed @= 'Pluck の役割を directory Target の content Selection として明確化する。File Target には Pluck selection を適用せず、その regular file 自体を1個の Archive entry として収録する。Pluck がない Configuration でも file-kind Scope の file Target reference は使用できるが、directory Target は引き続き Pluck を必要とする。'

        changed @= '既存 Namespace mechanism を file Target にも適用する。File Target の source root は file name 1 segment とし、Namespace がある場合は `NAMESPACE/FILENAME` を final archive file path とする。'

    class RELEASE_18:
        r"""
        配布物の役割を明確化し、build backend を Hatchling へ統一する。Wheel は実装と公開文書一式を提供し、sdist は release の再構築・検証に必要な完全な source を提供する。
        """
        title @= '0.10.2'

        version @= '0.10.2'

        changed @= 'Build backend を setuptools から Hatchling へ移行する。Version は引き続き `dirpluck.__version__` を正本とし、Hatchling の version source から project metadata へ反映する。Setuptools 専用の `MANIFEST.in` と generated `*.egg-info` は配布設計から除外する。'

        changed @= 'Wheel 専用の compact documentation を廃止する。`src/dirpluck/docs/`、`canonical_sources/package_cli/`、`canonical_sources/package_configuration/`、`canonical_sources/package_trust/`、および `canonical_documents/package/` の独立 publication channel を削除し、公開文書の二重管理をやめる。'

        changed @= 'Wheel には実装に加えて repository の公開 `README.md`、`GLOSSARY.md`、`CHANGELOG.md`、`STATUS.md`、`docs/` 全体を `dirpluck/_docs/` 以下へ同梱する。CLI、Configuration、Python API、Trust、Specification、Glossary を同じ release の wheel だけから参照できるようにする。'

        changed @= 'sdist は特定 directory を列挙する方式ではなく、VCS ignore rules を尊重した release source 全体を収録する方針へ変更する。`tests/`、`tools/`、`devdocs/`、公開文書、実装を含め、repository operation 専用の `.github/` は除外する。'

    class RELEASE_17:
        r"""
        0.10.0 の runtime behavior と公開 API / Configuration semantics を維持したまま、release metadata と公開文書を 0.10.1 release として同期する。
        """
        title @= '0.10.1'

        version @= '0.10.1'

        changed @= 'Package version と文書の current-version snapshot を 0.10.1 へ更新する。Runtime behavior、公式 Python API、CLI、Configuration language、Archive semantics の機能変更は行わない。'

        changed @= 'Release-preparation 文書を現在の shikumi / shikumi-devdoc baseline と整合させ、STATUS の documentation tooling 記述を今回の release baseline である Shikumi 0.2.0 と shikumi-devdoc 0.3.0 に揃える。'

    class RELEASE_16:
        r"""
        Runtime から Output destination と overwrite policy を指定できるようにし、Configuration の抽出定義を保ったまま書き出し場所を invocation ごとに変更できるようにする。
        """
        title @= '0.10.0'

        version @= '0.10.0'

        added @= 'CLI に `--here[=FILENAME]`、`-o PATH` / `--output PATH`、`-f` / `--force` を追加する。`--here` は runtime cwd、`--output` は runtime cwd 基準の明示 path を Output として使用し、末尾 `/` の `--output` は directory 指定として timestamp filename を自動生成する。`--here=FILENAME` は cwd 直下の filename だけを受理し、path を指定する場合は `--output` を使用する。'

        added @= '公式 Python API の `run()` に `output` と `force` を追加する。`output` は CLI `--output` と同じ path semantics を持ち、末尾 `/` なら automatic timestamp filename、末尾 `/` がなければ exact output file path とする。Relative `output` は API の `cwd` を基準に解決する。'

        changed @= 'Runtime Output が指定された build では root Configuration に Output declaration を要求しない。Exact runtime output はその filename をそのまま使い、automatic runtime output は root Configuration が `[output.timestamp]` を宣言している場合だけその `prefix` / `suffix` naming rule を再利用する。Root に timestamp Output がない場合は `dirpluck-YYYYMMDD-HHMMSS.zip` を既定名とする。Configuration 側の output directory / fixed path は runtime destination へ引き継がない。'

        changed @= '`--sequence N` は Configuration timestamp output に加えて、`--here` と末尾 `/` の runtime Output が生成する automatic timestamp filename にも適用する。Exact runtime file path と組み合わせた場合は error とする。Generated name の collision に対する自動採番・自動 rename・timestamp 再取得は行わない。'

        changed @= 'Runtime Output の default overwrite policy は `false` とし、`--force` / `force=True` で effective Output を overwrite 可能にする。`--force` は runtime Output だけでなく Configuration の fixed / timestamp Output にも適用できる。Runtime path notation は Configuration と同じく OS にかかわらず `/` separator を使用し、backslash を受理しない。'

        changed @= '`--preview` / `preview=True` は Output を解決・書き込みしないため、runtime Output を指定する `--here` / `--output` / `output=`、overwrite を要求する `--force` / `force=True`、および output filename を変更する `--sequence` との組み合わせを error とする。指定した runtime Output option を preview が暗黙に無視する挙動は行わない。'

        changed @= '公開文書の情報設計を整理し、README の end-to-end example を `docs/GETTING_STARTED.md` へ分離する。従来の単一 `docs/CONFIGURATION.md` は `docs/configuration/INDEX.md` を入口とする collection に分割し、overview、source、selection、base composition、Output、complete example を目的別に参照できるようにする。Wheel 同梱の compact `dirpluck/docs/CONFIGURATION.md` は引き続き1文書の quick reference として維持する。'

        changed @= 'CLI guide も単一 `docs/CLI.md` から `docs/cli/INDEX.md` を入口とする collection へ分割し、基本操作、Invocation Template、Target / Case、preview / runtime Output を目的別に参照できるようにする。Wheel 同梱の `dirpluck/docs/CLI.md` は compact quick reference として維持する。また collection の公開 `INDEX.md` は shikumi-devdoc が生成する canonical index の翻訳に限定し、追加の説明や導線は各 `overview.md` の canonical source に置く。'

        changed @= '分割後の Specification に残っていた旧 monolithic 文書の節番号参照を廃止し、Filesystem path notation、Runtime Target、Archive planning、Output など意味上の規範名で参照する。規範間の依存は循環 import を生まない範囲で `related` metadata に保持し、旧 `N節` / `Section N` 形式が再混入しない回帰テストを追加する。'

        changed @= '開発文書の正本を shikumi-devdoc 0.3.0 の現行 authoring contract へ同期する。Nested title は `@title(...)` ではなく `title @= ...` に統一し、各 canonical source で `heading="title"` / `heading="identity"` を明示する。テストから直接検証する文書断片は `code_field` ではなく presentation を持たない `test_target_field` に分離し、Markdown fence は docstring 側へ置く。Vocabulary term は既定で Glossary 公開とし、冗長な `glossary @= True` を削除する。Specification は stable related target を維持するため identity heading policy を使用する。'
