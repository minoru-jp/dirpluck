<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `devdocs/canonical_documents/package_cli/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/intermediate_documents/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck CLI Quick Reference

wheel に同梱する最小 CLI reference です。

```text
dirpluck [TARGET ...] [--config PATH] [--case NAME] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck -i PATH [-e NAME] [--case NAME] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
dirpluck --version
```

- Effective Configuration に Pluck がある場合は1個以上の positional `TARGET` reference を指定します。Pluck がない場合は指定しません。
- `project` は常設の default Scope 直下の `project`、`work/project` は named Scope `work` 直下の `project` を選びます。Default Scope root は常に root Configuration file の directory です。Target は Scope root の direct child directory に限定します。
- `/` は default Scope、`work/` は named Scope `work` の eligible directory をすべて Target として展開します。Scope の `ignore` に一致する directory は除きます。Unknown Scope は error です。未使用の named Scope root は存在確認しません。
- `--config` 省略時は cwd の `default.dirpluck` だけを自動的に使用します。`--config PATH` は cwd 基準の relative path または host filesystem の absolute path で1個の Configuration document を明示し、別 directory を探索しません。末尾が `.dirpluck` でなければ suffix を付加するため、`release-1.2` や `configs/release-1.2` のような path も使えます。Document path は symbolic link / Windows directory junction を含めて host OS の通常の filesystem semantics に従います。選択した document path の location は relative document reference の基準として保持します。Path separator は Windows でも `/` です。`.toml` 互換 fallback はありません。
- `--case NAME` は named Case を1個選びます。
- `-i PATH` / `--invocation-template PATH` は cwd 基準の relative path または host filesystem の absolute path で1個の `.dirpluck-inv` Invocation Template file を明示します。別 directoryは探索せず、document path は symbolic link / Windows directory junction を含めて host OS の通常の filesystem semantics に従います。末尾が `.dirpluck-inv` でなければ suffix を付加します。Root `[invocation]` は `-e` 省略時の default Invocation、`[invocation.<name>]` は `-e NAME` / `--entry NAME` で選ぶ named Invocation entry です。各 Invocation の optional `config` / `targets` / `case` / `archive_mtime` は独立しており、named entry は root から field を継承しません。これらの field 名は entry name としては予約語です。Relative `config` path は選択した Template file path の directory 基準で、`.dirpluck` suffix は省略できます。Control document path の symbolic link / Windows directory junction は host OS の通常の filesystem semantics に従います。Field を持たない Invocation も有効で、CLI runtime value と通常の defaults を使い、成功した preview / build では note を表示します。Template と positional `TARGET` / `--config` は組み合わせません。CLI `--case NAME` は選択した Invocation の `case`、`--archive-mtime VALUE` は `archive_mtime` を上書きします。`--preview` / `--sequence` / `--archive-mtime` / `--paths` も runtime modifier として併用できます。
- `--preview` は Archive を書き込まず ZIP contents の plan を表示します。Root Configuration に Output declaration がなくても使用でき、`--sequence` とは組み合わせません。Selection traversal で non-ignored symbolic link / Windows directory junction を除外した場合は件数を note として表示します。通常 build でも同じ件数を output path の後に表示します。
- `--paths` は生成される Archive README に解決済み source filesystem path を追加します。既定では path を記録しません。
- `--sequence N` は timestamp output name の明示的な正整数 sequence です。自動採番ではありません。
- `--archive-mtime VALUE` は全 ZIP entry に同じ timestamp を設定します。`VALUE` は `YYYY-MM-DDTHH:MM:SS`、`now`、`zip-epoch` のいずれかです。明示 timestamp は ZIP の 1980..2107 範囲で、奇数秒は2秒粒度へ切り下げます。`zip-epoch` は `1980-01-01T00:00:00`、`now` は1 run で local current time を一度だけ取得します。省略時は従来の entry timestamp を使います。固定 timestamp は reproducible な Archive を作る一助になりますが、source file の permission bits など他の metadata は正規化しません。Archive 全体の byte-for-byte reproducibility は保証しません。Timestamp output filename の時刻には影響しません。

```console
dirpluck example --preview
dirpluck work/example --case audit
dirpluck /
dirpluck work/
dirpluck --config snapshot
dirpluck -i release
dirpluck -i release -e docs
```

TOML の最小 reference は同梱の `CONFIGURATION.md`、trust model は同梱の `TRUST.md` を参照してください。より詳しい CLI semantics、Configuration guide、Glossary、Specification は同じ release の source distribution にある `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, `docs/SPECIFICATION.md` を参照してください。
