<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/selection.py` です。
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

# Selection and shared patterns

## SPEC_065

Pluck の base / Pluck Case Selection と、Always source の base Selection は、`must` / `may` の candidate を少なくとも1個必要とする。Candidate は direct string pattern、structured `match` entry、または Shared reference で記述できる。`description` は任意で、記述する場合だけ空でない string を必要とする。Always Case は Selection ではなく effective Always source 集合の membership filter なので、この Selection grammar を持たない。

level: MUST

## SPEC_066

`must` / `may` の array item は direct pattern string、`{ match = "..." }` inline table、または `{ shared = "..." }` inline table とする。

```text
"foo"                         direct pattern
{ match = 'src/.*\.py' }    structured match
{ shared = "foo" }            Shared reference
```

level: MUST

## SPEC_067

`ignore` の direct string は name pattern とする。Structured entry は `{ match = "..." }` を root-relative path の regular-expression match、`{ shared = "..." }` を `shared.ignore` reference、`{ path = "..." }` を Selection-relative concrete path とする。

```text
"*.pyc"                              direct name pattern
{ match = 'build/' }                 structured match
{ shared = "python-noise" }          Shared ignore reference
{ path = "tests/fixtures/big.bin" }  file/directory path
{ path = "tests/fixtures/" }         directory path
```

level: MUST

## SPEC_069

Shared reference namespace は field から一意に決まる。

```text
must   -> shared.must
may    -> shared.may
ignore -> shared.ignore
```

level: MUST

## SPEC_070

Shared pattern definition の value は direct string pattern または `{ match = "..." }` inline table の non-empty array とし、Shared reference や path reference を nested させない。

level: MUST

## SPEC_071

Shared reference は Base composition 後の effective shared namespace を参照し、対応する pattern set と同じ意味を持つ。Unknown reference は Configuration error とする。Path reference は Shared namespace を参照せず、その Selection の source root を基準に解釈する。

level: MUST

related: [SPEC_034](composition.md#spec_034)

## SPEC_072

展開後の `must` 内、`may` 内、`ignore` 内の同一記述の duplicate pattern / structured match / reference、および `must` / `may` 間の同一 include entry は Configuration error とする。一方、異なる selection entry が結果として同じ filesystem entry を選ぶ semantic overlap は有効で、最終 Selection では同一 file を1回だけ含める。異なる ignore 条件が同じ filesystem entry に一致する semantic overlap も有効で、除外結果は条件の和とする。

level: MUST

## SPEC_073

`allow_empty` は boolean で既定 `false` とする。`allow_empty = true` は、Shared reference 展開後に `must` pattern を持たない selection だけで指定できる。

level: MUST

condition: `allow_empty = true` を指定する場合

## SECTION_601

title: Include pattern grammar (`must` / `may`)

### SPEC_074

`must` と `may` の direct / expanded pattern は source directory からの `/` separator の relative path とする。Absolute path、`.` / `..` による逸脱、backslash を拒否する。

level: MUST

### SPEC_075

各 path element には `*` を最大1個だけ含められる。`*` はひとつの実体名内部で0文字以上に一致し、path separator を越えない。そのため Configuration に書いた path hierarchy の深さは固定される。

```text
src/
README.md
dist/package-*.whl
packages/*/dist/
```

level: MUST

### SPEC_076

`must` pattern は1件以上の **non-ignored selectable entry** に一致しなければ error、`may` pattern は0件一致を許容する。複数一致した場合は `ignore` 適用後に残ったものを selection candidate とする。

level: MUST

condition: `must` / `may` pattern を評価する場合

### SPEC_077

`must` / `may` の direct string pattern は **最終 component の末尾 `/` だけ**で期待する entry type を決める。末尾 `/` なしは regular file、末尾 `/` ありは regular directory を要求し、filesystem 上の実体型から意味を推測しない。Intermediate component は次の component へ進む traversal point なので directory として解釈する。Directory leaf に一致した場合は `ignore` に従って配下の regular file を再帰収集する。Type mismatch は selectable match としない。期待型の selectable match が0件で、同じ string pattern に一致する反対型の non-ignored regular entry が存在する場合、`must` は通常 build では従来どおり unsatisfied must error としつつ末尾 `/` の追加または削除を案内し、preview planning では missing result を維持したまま同じ hint を non-fatal diagnostic として記録する。`may` は optional missing のまま成功可能とし、同じ type hint を non-fatal diagnostic として記録する。各 diagnostic は該当 source label を含み、CLI は stderr へ warning として表示し、Python API は `RunResult.warnings` に返す。この diagnostic は `must` / `may` の selection semantics を変更しない。`ignore` は entry の種類による診断より優先し、ignored entry は selectable match、link-only / special-entry-only match、skipped-link count のいずれにも含めない。Symbolic link または Windows directory junction として認識した **non-ignored** entry は selectable entry とみなさない。Pattern がそのような non-ignored link-like entry だけに一致した場合、`must` は通常の不存在と区別できる理由付き error とし、`may` は optional missing として扱う。

level: MUST

condition: include pattern を評価する場合

### SPEC_078

FIFO、socket、device など regular file / regular directory ではない **non-ignored** filesystem entry も selectable entry とせず、Archive に含めない。`may` がそのような特殊 entry に一致しても選択せず optional missing とし、`must` が特殊 entry だけに一致した場合は unsupported special filesystem entry にしか一致しなかったことを示す理由付き error とする。Regular directory の配下を再帰収集するときに現れる特殊 entry は traversal せず、静かに除外する。内容や filename の意味に基づく暗黙 ignore は行わない。

level: MUST NOT

condition: include pattern が special filesystem entry に一致する場合

### SPEC_079

Matching は OS に依存せず case-sensitive とする。`**`、`?`、character class (`[]`)、`!` はサポートしない。複数一致を version、mtime、その他 metadata で順位付けしない。

level: MUST

## SECTION_602

title: Ignore grammar

### SPEC_080

Selection の `ignore` は direct name pattern、structured `{ path = "..." }` concrete path、structured `{ match = "..." }`、および `{ shared = "..." }` による Shared ignore expansion を持つ。

level: MUST

### SPEC_081

Direct string はひとつの実体名を case-sensitive に照合する。末尾 `/` のない pattern は matching file name と directory name の両方へ適用し、末尾 `/` の pattern は directory name だけに限定する。対応形式は次とする。

```text
name      exact
name*     prefix
*name     suffix
*name*    substring
```

level: MUST

### SPEC_082

Directory だけへ限定したい name pattern ではこの body の末尾に `/` を付ける。末尾 `/` を省略した同じ body は file / directory の両方へ適用する。

```text
.git/
__pycache__/
tmp-*/
```

level: MUST

### SPEC_083

Selection-relative concrete path は `ignore` の `{ path = STRING }` inline table で記述する。Pluck では Target directory、Always source では解決済み Always source directory を Selection root とする。`path` は Selection root 基準の relative path であり、先頭の `./` は任意として正規化する。末尾 `/` のない concrete path は、その path にある file / directory の両方を除外対象とする。末尾 `/` を付けた場合だけ directory に限定する。

```text
{ path = "tests/fixtures/big.bin" }   exact entry path (file or directory)
{ path = "tests/fixtures/" }          exact directory path and its subtree
{ path = "./tests/fixtures/" }        same path after normalization
```

level: MUST

### SPEC_084

`path` は Selection root の内側だけを指し、空 path、`.` / `./` 自体、`..` component、absolute path、glob、backslash を拒否する。Path separator は `/` とする。`.` component は正規化し、たとえば `./src/./generated/` と `src/generated/` は同じ concrete path として扱う。末尾 `/` の有無にかかわらず、実体が directory として一致した場合はその directory と subtree 全体を Selection 対象から除外する。末尾 `/` なしは同じ path の regular file にも一致するが、末尾 `/` ありは regular file に一致しない。

level: MUST

### SPEC_085

Name pattern、Shared ignore expansion、structured `path`、structured `match` は集合的な除外条件として適用し、同じ entry に複数条件が一致しても error としない。

level: MUST

### SPEC_086

`ignore` は link-like / special entry の種類による診断より優先する。Ignored entry は Selection candidate、link-only / special-entry-only error の根拠、skipped-link count の対象にせず、ignored directory の subtree も Selection / filesystem-entry diagnostic の対象外とする。末尾 `/` のない name pattern は matching file / directory name の両方に加え、同じ name を持つ特殊 entry にも適用する。Structured `path` が link-like entry 自身に一致する場合も ignored entry として扱う。

level: MUST

### SPEC_087

Name pattern では `*` 単体、`*/`、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!`、backslash、body 内の path separator を拒否する。Structured `path` は wildcard syntax を持たない。

level: MUST NOT

## SECTION_603

title: Structured path match (`{ match = "..." }`)

### SPEC_159

`must` / `may` / `ignore` と Shared pattern set は `{ match = STRING }` inline table を direct Selection entry として受理する。Inline table は `match` 以外の key を持てず、`match` は non-empty string とする。

level: MUST

### SPEC_160

`match` の value は512 character 以下の有効な Python-compatible regular expression とする。Matching は `re.fullmatch()` 相当の full-match semantics とし、invalid regular expression は Configuration error とする。

level: MUST

### SPEC_161

`match` は Selection root 自身を除く descendant regular file / regular directory の root-relative POSIX-style path 全体へ適用する。Path separator は OS にかかわらず `/` とする。Regular file は末尾 `/` を持たず、regular directory は `src/` / `src/pkg/` のように末尾 `/` を持つ normalized path とする。

level: MUST

### SPEC_162

`must` の structured match は ignore 適用後に1件以上の selectable entry に一致しなければ error とする。`may` は0件一致を許容する。1つの structured match が複数 entry に一致した場合は一致した entry をすべて selection candidate とする。Regular file に一致すればその file を選択し、regular directory に一致すれば通常の directory leaf と同じく `ignore` に従って subtree の regular file を再帰収集する。

level: MUST

### SPEC_163

通常の string pattern、Shared expansion、structured match が同一 regular file を複数回選択しても、その file は Archive candidate として1回だけ扱う。複数の `must` entry が同じ file に一致した場合でも、それぞれの `must` は独立して成立できる。

level: MUST

### SPEC_164

`ignore` の structured match は他の ignore 条件と同じ優先度を持つ。Regular file path に一致すればその file を除外し、regular directory path に一致すればその directory と subtree 全体を除外する。Ancestor directory path に structured ignore match が成立する descendant も除外された subtree の一部として扱う。

level: MUST

### SPEC_165

Structured match は既存の filesystem safety boundary を変更しない。Ignored entry は match の成立や link-like / special-entry diagnostic の根拠に含めない。Non-ignored symbolic link / Windows junction、FIFO、socket、device 等は selectable match とせず、`must` がそのような entry だけに一致した場合は既存の link-only / special-entry-only diagnostic semantics を適用する。

level: MUST
