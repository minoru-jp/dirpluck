# Configuration output

Fixed and timestamp Output declarations and their write boundaries.

This guide explains Configuration-side Output authoring. Exact fixed, timestamp, and runtime Output rules are defined in the [Output specification](../specification/output.md). For runtime Output controls, see [Preview and runtime Output](../cli/output.md); for the trust boundary, see the [Trust model](../TRUST.md).

## Output

Output is optional on a Configuration by itself. A Base Configuration that only provides shared definitions may omit it, and a Root Configuration used with `--preview` or Runtime Output may also omit it. A normal build without Runtime Output must directly declare exactly one of two modes on the Root Configuration: fixed mode, in which the user chooses the final filename, or timestamp mode, in which `dirpluck` generates a filename from a timestamp. Output from a Base Configuration is not inherited.

### Fixed Output

```toml
[output]
path = "artifacts/review.zip"
overwrite = false
```

`path` is a concrete output file path including the filename. A relative path is resolved from the directory containing the Configuration file in which this `[output]` is written.

`overwrite` controls whether an existing output may be replaced and defaults to `false`. Output files are created with the same permission semantics as ordinary newly created files, so POSIX systems apply the process `umask`. Even with `overwrite = true`, the mode of the file being replaced is not inherited. `prefix` and `suffix` are not used in fixed mode.

### Timestamp Output

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` specifies the output directory and ends in `/` to indicate directory notation. A relative path is resolved from the directory containing the Configuration file in which this definition is written.

The filename is generated in this form:

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

`prefix` and `suffix` are specific to timestamp mode. Use CLI `--sequence N` when multiple runs in the same second need to be distinguished intentionally. When CLI `--here`, trailing-`/` `--output`, or Python `output=` requests automatic Runtime Output, these `prefix` / `suffix` values are reused as the naming rule, but the configured timestamp-output directory is not. A policy that gives every ZIP entry the same mtime is not a Configuration field; set it at runtime with CLI `--archive-mtime` or Invocation Template `archive_mtime`.

