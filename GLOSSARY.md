# dirpluck Glossary

This glossary defines the concepts used consistently across the `dirpluck` documentation and implementation. It defines what the terms mean, not specification details such as cardinality, resolution order, or error conditions.

## dirpluck

A CLI tool that selects files from sources according to a declared extraction intent and produces a ZIP archive.

## Configuration file

A TOML document that describes a `dirpluck` extraction intent.

## Target

A source definition whose common selection rules are applied to source directories selected at runtime.

## Target location

A named directory whose direct child directories can be selected as Targets at invocation time.

## Case

A named selection definition representing an extraction variation distinct from the base selection.

## Companion

A source definition that fixes a source directory in the Configuration and associates it with the same extraction intent.

## Source directory

The actual directory from which files are extracted for a Target or Companion.

## Extraction

The process of determining which files from a source directory belong in the Archive according to selection rules.

## Archive

The ZIP artifact produced by `dirpluck` from an extraction result.

## Output definition

Configuration describing where the Archive is written and how it is named.

## Archive README

An index document generated at the root of an Archive that describes its contents.

## Shared pattern

A named reusable set of include or exclude patterns referenced by selection definitions.

## Configuration import

A mechanism for bringing another Configuration in as an inner layer and composing definitions with it.

## Root Configuration

The outermost Configuration that starts one `dirpluck` run.

## Effective Configuration

The Configuration used for one run after resolving the Root Configuration and its Configuration imports.
