from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} CLI Quick Reference")
class TITLE_1:
    r'''wheel に同梱する最小 CLI reference です。

```text
{{TERM_1}} [TARGET ...] [--config PATH] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
{{TERM_1}} -i PATH [-e NAME] [--case NAME] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
{{TERM_1}} --version
```

- Effective Configuration に Pluck がある場合は1個以上の positional `TARGET` reference を指定します。Pluck がない場合は指定しません。
- `project` は常設の default Scope 直下の `project`、`work/project` は named Scope `work` 直下の `project` を選びます。Default Scope root は常に root Configuration file の directory です。Target は Scope root の direct child directory に限定します。
- `/` は default Scope、`work/` は named Scope `work` の eligible directory をすべて Target として展開します。Scope の `ignore` に一致する directory は除きます。Unknown Scope は error です。未使用の named Scope root は存在確認しません。
- `--config` 省略時は cwd の `default.dirpluck` だけを自動的に使用します。`--config PATH` は cwd 基準の relative path または host filesystem の absolute path で1個の Configuration document を明示し、別 directory を探索しません。末尾が `.dirpluck` でなければ suffix を付加するため、`release-1.2` や `configs/release-1.2` のような path も使えます。Document path は symbolic link / Windows directory junction を含めて host OS の通常の filesystem semantics に従います。選択した document path の location は relative document reference の基準として保持します。Path separator は Windows でも `/` です。`.toml` 互換 fallback はありません。
- `--case NAME` は named Case を1個選びます。
- `-i PATH` / `--invocation-template PATH` は cwd 基準の relative path または host filesystem の absolute path で1個の `.dirpluck-inv` Invocation Template file を明示します。別 directoryは探索せず、document path は symbolic link / Windows directory junction を含めて host OS の通常の filesystem semantics に従います。末尾が `.dirpluck-inv` でなければ suffix を付加します。Root `[invocation]` は `-e` 省略時の default Invocation、`[invocation.<name>]` は `-e NAME` / `--entry NAME` で選ぶ named Invocation entry です。各 Invocation の optional `config` / `targets` / `case` / `archive_mtime` は独立しており、named entry は root から field を継承しません。これらの field 名は entry name としては予約語です。Relative `config` path は選択した Template file path の directory 基準で、`.dirpluck` suffix は省略できます。Control document path の symbolic link / Windows directory junction は host OS の通常の filesystem semantics に従います。Field を持たない Invocation も有効で、CLI runtime value と通常の defaults を使い、成功した preview / build では note を表示します。Template と positional `TARGET` / `--config` は組み合わせません。CLI `--case NAME` は選択した Invocation の `case`、`--archive-mtime VALUE` は `archive_mtime` を上書きします。`--here` / `--output` / `--force` / `--preview` / `--sequence` / `--archive-mtime` / `--paths` も、それぞれ通常の組み合わせ制約に従う runtime modifier として使用できます。
- `--here` は cwd に `dirpluck-YYYYMMDD-HHMMSS.zip` を生成します。Root Configuration が `[output.timestamp]` を持つ場合はその `prefix` / `suffix` naming rule を再利用します。`--here=FILENAME` では cwd 直下の filename を明示し、path component は受理しません。
- `-o PATH` / `--output PATH` は runtime Output を指定します。末尾 `/` があれば directory + automatic timestamp filename、なければ exact output file path です。Relative path は cwd 基準で、Windows でも separator は `/` です。Backslash は受理しません。`--here` と `--output` は同時に指定できません。
- `-f` / `--force` は effective Output の overwrite policy を true にします。Runtime Output の既定は no-overwrite です。Configuration の fixed / timestamp Outputにも適用できます。Automatic name の collision は `--force` がなければ error で、自動 rename はしません。
- `--preview` は Archive を書き込まず ZIP contents の plan を表示します。Root Configuration に Output declaration がなくても使用できますが、Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` とは組み合わせません。Selection traversal で non-ignored symbolic link / Windows directory junction を除外した場合は件数を note として表示します。通常 build でも同じ件数を output path の後に表示します。
- `--paths` は生成される Archive README に解決済み source filesystem path を追加します。既定では path を記録しません。
- `--sequence N` は automatic timestamp output name の明示的な正整数 sequence です。自動採番ではありません。Exact runtime output では使えません。
- `--archive-mtime VALUE` は全 ZIP entry に同じ timestamp を設定します。`VALUE` は `YYYY-MM-DDTHH:MM:SS`、`now`、`zip-epoch` のいずれかです。明示 timestamp は ZIP の 1980..2107 範囲で、奇数秒は2秒粒度へ切り下げます。`zip-epoch` は `1980-01-01T00:00:00`、`now` は1 run で local current time を一度だけ取得します。省略時は従来の entry timestamp を使います。固定 timestamp は reproducible な Archive を作る一助になりますが、source file の permission bits など他の metadata は正規化しません。Archive 全体の byte-for-byte reproducibility は保証しません。Timestamp output filename の時刻には影響しません。

```console
{{TERM_1}} example --preview
{{TERM_1}} work/example --case audit
{{TERM_1}} /
{{TERM_1}} work/
{{TERM_1}} --config snapshot
{{TERM_1}} -i release
{{TERM_1}} -i release -e docs
```

TOML の最小 reference は同梱の `CONFIGURATION.md`、trust model は同梱の `TRUST.md` を参照してください。より詳しい CLI semantics、Configuration guide、Glossary、Specification は同じ release の source distribution にある `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, `docs/SPECIFICATION.md` を参照してください。
'''
    vocabulary_refs @= (terms.TERM_1,)
