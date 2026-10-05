<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/paths.py` です。
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

# Filesystem path notation

## SPEC_017

Configuration / Invocation Template の TOML で filesystem location を表す field と、CLI の `--config PATH` / `-i PATH` / `--output PATH`、Python API の runtime `output` は、host OS に関係なく `/` を path separator として使用する。Backslash は separator として受理せず、Windows でも `/` を記述する。

level: MUST

## SPEC_018

Configuration 内の relative filesystem path は、field の種類や runtime state によって resolution base を切り替えず、**その field が記述されている Configuration file の directory**から解決する。少なくとも次の field にこの規則を適用する。

```text
about.base
scope.<name>.path
always.<name>.path
output.path
output.timestamp.path
```

level: MUST

## SPEC_019

Base Configuration に記述された relative path は、その Configuration 自身の directory から解決し、Root Configuration の directory を基準にはしない。

level: MUST

## SPEC_020

Absolute path は host OS が完全な absolute path として認識する root form を `/` separator で記述し、その場所を直接参照する。例として POSIX host の `/opt/data`、Windows host の `C:/data` と `//server/share/data` を受理できる。別 OS の root form へ自動変換しない。Windows drive-relative form (`C:foo`) は absolute path として扱わない。

level: MUST

## SPEC_021

Filesystem-location notation では `~` expansion と environment-variable interpolation を行わず、glob を受理しない。`.` と `..` は field / option 固有の file / directory 条件を満たす範囲で通常の path component として解決する。Absolute path を使用した Configuration や CLI document selection は参照先 filesystem に依存し、OS 間 portability を保証しない。

level: MUST

## SPEC_022

CLI の `--config PATH` / `-i PATH` / `--output PATH` と Python API の runtime `output` は relative path の resolution base を runtime cwd とする。Invocation Template 内の default / named Invocation の `config` は Template document 自身の directory を基準にする。Configuration に記述された relative filesystem path resolution に runtime cwd を使用しない。

level: MUST

## SPEC_023

Configuration / Invocation Template **document 自体を選択または参照する path** は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path を特別に拒否しない。cwd の `default.dirpluck`、`--config PATH`、`-i PATH`、`about.base`、Invocation の `config` のいずれでも、relative document reference と、その document に記述された relative filesystem location は **利用者が指定・参照した lexical document path の directory** を基準にする。Symlink / junction の参照先 directory へ暗黙に rebase しない。一方、Base chain が path alias を経由して同じ Configuration file へ戻る場合は同一 file への cycle とみなす。

level: MUST

## SPEC_024

この control-document rule は source root resolution / source tree traversal の link handling とは別である。`[scope.<name>].path` と `[always.<name>].path` のように Configuration が明示する source root location は host OS の通常の filesystem semantics に従い、path の途中または最終 component が symbolic link / Windows directory junction であることだけを理由に拒否しない。明示 location を実在 directory に解決した後、その directory を source root / selection boundary とする。一方、その root から Dirpluck が Target discovery / Selection traversal を自動的に行う段階では Filesystem boundary and entry types の link-like entry rule に従い、認識した link-like entry を選択・走査しない。Include pattern、ignore pattern、archive path、CLI Target reference など filesystem location ではない値は、それぞれの規則に従う。

level: MUST
