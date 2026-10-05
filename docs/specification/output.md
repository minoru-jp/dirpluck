# Output

## SPEC_107

A Configuration may omit Output. A Configuration without Output may also be used as the Root for archive planning or `--preview`. A build that actually writes an Archive uses either the Root Configuration's own fixed / timestamp Output or Runtime Output as the effective Output. Only when Runtime Output is absent must the Root Configuration directly declare its own Output; Base Output is not inherited as the Root Output.

level: MUST

## SECTION_901

title: Fixed Output

### SPEC_109

```toml
[output]
path = "artifacts/context.zip"
overwrite = false
```

level: INFORMATIVE

### SPEC_110

`path` is required. `overwrite` is an optional boolean and defaults to `false`. A `timestamp` subtable, `prefix`, and `suffix` cannot be specified in fixed mode.

level: MUST

### SPEC_111

`path` is a concrete file path. Directory notation ending in `/`, globs, and destinations that resolve as directories are rejected. Relative paths may resolve `.` and `..` normally. Required parent directories are created. The Output location is not restricted by a Configuration-directory boundary.

level: MUST

### SPEC_112

If the effective Output resolves to an existing destination and the effective overwrite policy is false, the build fails without modifying that existing destination.

level: MUST

### SPEC_113

When overwrite is permitted and the destination already exists, its previous contents remain intact until the new Archive has been completed successfully; the completed Archive then replaces the destination. A failed build must not leave the destination partially replaced by an incomplete Archive.

level: MUST

### SPEC_114

Creation and replacement of the final Output file follow the host OS's ordinary file-creation and replacement semantics, subject to dirpluck's overwrite policy and safety checks.

level: MUST

### SPEC_115

The filename extension is not used to determine ZIP format. In fixed mode, the filename written in the Configuration is not changed or expanded at runtime.

level: MUST NOT

## SECTION_902

title: Timestamp Output

### SPEC_116

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

level: INFORMATIVE

### SPEC_117

`path` is required. `prefix` and `suffix` are optional. `overwrite` cannot be specified.

level: MUST

### SPEC_118

`path` is a concrete directory path and must end in `/` in Configuration notation. Globs are rejected. Relative paths may resolve `.` and `..` normally. Required directories are created. The Output location is not restricted by a Configuration-directory boundary.

level: MUST

### SPEC_119

`prefix` and `suffix` are each one non-empty portable filename fragment. `.`, `..`, path separators, control characters, and `< > : " | ? *` are rejected.

level: MUST

### SPEC_120

The generated filename has this fixed form:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

level: MUST

### SPEC_121

Timestamp Output uses one timestamp value consistently for the automatic filename generated for a single build.

level: MUST

### SPEC_122

`N` is an integer of 1 or greater supplied by CLI `--sequence N` or Python API `sequence=`. When omitted, no number segment is emitted. `dirpluck` does not inspect existing outputs to infer a number and does not perform automatic numbering or automatic renaming. A sequence may be used only when the effective Output generates an automatic timestamp filename.

level: MUST

### SPEC_123

If the generated filename already exists at the point it is checked, the run fails by default. Timestamp Output has no Configuration `overwrite` field, but runtime `--force` / `force=True` makes the effective overwrite policy true and permits replacement. The generated Archive file uses the same host-OS new-file permission and mode semantics as fixed Output.

level: MUST

condition: when the generated filename already exists

## SECTION_9022

title: Runtime Output

### SPEC_124

CLI `--here[=FILENAME]`, `-o PATH` / `--output PATH`, and Python API `output=` specify Runtime Output for a build. When Runtime Output is present, a Configuration fixed output path or timestamp output directory is not used as the effective destination. The Root Configuration may omit Output entirely.

level: MUST

condition: when Runtime Output is present

### SPEC_125

CLI `--here` is automatic Output whose directory is the runtime cwd. `--here=FILENAME` is an exact output filename directly under the runtime cwd. `FILENAME` must not contain `/` or `\`, must not be `.` or `..`, and must be one portable filename fragment. The optional filename is accepted only in the `--here=FILENAME` form with `=`. `--here` and `--output` are mutually exclusive. `-h` remains reserved for `--help`; `--here` has no short option.

level: MUST

### SPEC_126

CLI `--output PATH` / `-o PATH` and Python `output=PATH` use the Filesystem path notation and reject backslashes and globs. Relative `PATH` is resolved from the runtime cwd; an absolute `PATH` refers directly to the host filesystem. A `PATH` ending in `/` is an output directory. A `PATH` without trailing `/` is an exact output file path. dirpluck does not infer file versus directory form from existing filesystem state. In exact form, a final component of `.`, `..`, or no filename is an error. Required parent or output directories are created during a normal build.

level: MUST

related: [SPEC_017](paths.md#spec_017), [SPEC_022](paths.md#spec_022)

### SPEC_127

Automatic Runtime Output (`--here`, or trailing-`/` `--output` / `output=`) samples process-local time once and creates a timestamp filename. If the Root Configuration declares `[output.timestamp]`, its `prefix` / `suffix` naming rule is reused, but its configured `path` is not. Without Root timestamp Output, the fixed prefix is `dirpluck` and the filename is:

```text
dirpluck-YYYYMMDD-HHMMSS[-N].zip
```

level: MUST

condition: when automatic Runtime Output is used

### SPEC_128

With Root timestamp Output, the existing `[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip` form is used in the runtime directory. Exact Runtime Output does not use Configuration `prefix` / `suffix` and its supplied filename is not modified.

level: MUST

condition: when the Root declares timestamp Output

### SPEC_129

`--sequence N` / `sequence=` may be used with automatic Runtime Output. It is an error with exact Runtime Output. If a generated destination already exists, dirpluck does not infer a new sequence, automatically rename the file, or sample a new timestamp.

level: MUST

### SPEC_130

Runtime Output defaults to `overwrite = false`; a Configuration fixed Output's `overwrite` value is not inherited into Runtime Output. CLI `-f` / `--force` or Python `force=True` sets the effective overwrite policy to true for either Runtime Output or Configuration Output. Without force, only Configuration fixed Output uses its own `[output].overwrite` value.

level: MUST

condition: when determining the Runtime Output overwrite policy

## SECTION_9025

title: Archive entry timestamp

### SPEC_131

`--archive-mtime VALUE` controls ZIP-entry timestamp metadata, not the Output path or filename. There is no corresponding Configuration field. The policy may be supplied as a CLI or Python-API runtime option, or stored as `archive_mtime` in an Invocation Template.

level: MUST

### SPEC_132

`VALUE` is `now`, `zip-epoch`, or a strict `YYYY-MM-DDTHH:MM:SS` string. An explicit timestamp is interpreted as a timezone-free literal; no timezone suffix, offset, or conversion is accepted. The supported range is the ZIP/DOS timestamp range from `1980-01-01T00:00:00` through `2107-12-31T23:59:59`. `zip-epoch` is equivalent to `1980-01-01T00:00:00`. `now` samples process-local current time once for the high-level run and uses that single value.

level: MUST

### SPEC_133

ZIP timestamps have two-second precision. If the resolved timestamp has an odd second, dirpluck rounds it down to the preceding even second; microseconds are discarded. The resolved timestamp is then applied uniformly to every ZIP entry written by that run, including the generated root `README.md`, empty-directory entries, and selected source files.

level: MUST

### SPEC_134

When `--archive-mtime` and Invocation `archive_mtime` are both omitted, existing semantics are preserved: selected source files use their filesystem mtimes, while entries generated by dirpluck use their generation time.

level: MUST

condition: when both `--archive-mtime` and Invocation `archive_mtime` are omitted

### SPEC_135

This option fixes Archive-entry timestamps so timestamp-driven byte differences can be removed. Source-file permission metadata is not normalized, so Archives with identical file contents and timestamps can still differ in bytes when runtime/platform ZIP metadata differs. dirpluck does not guarantee byte-for-byte reproducibility across compressor implementations, runtime versions, platforms, permission metadata, or other ZIP serialization details. This option is also independent of the process-local `YYYYMMDD-HHMMSS` used in timestamp Output filenames and does not change that filename timestamp. In preview mode no Archive is written, so archive mtime has no effect on the preview result.

level: MUST

## SECTION_905

title: Concurrent writes and input collision

### SPEC_143

`dirpluck` does not provide inter-process locking or conflict arbitration. Concurrent writes to the same output path are unsupported. Existing-destination checks for an effective no-overwrite Output are not atomic no-clobber guarantees against another process. Callers that may run concurrently must choose different output destinations.

level: MUST NOT

### SPEC_144

In either Output mode, the final output file generated by the run cannot itself be selected as an Archive input.

level: MUST NOT
