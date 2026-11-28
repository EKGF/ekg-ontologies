# Raw data capture

[Documentation index](../README.md#documentation)

The [Raw Data Ontology](../ekgf-raw.ttl) records source data before transformation
into domain ontologies. Its captured-content contract distinguishes a value
occurrence from its literal content and locates that occurrence within one
source row and one physical column in the same view.

## Captured content

Each `raw:Value` must have exactly one `raw:literalValue`, or be explicitly
classified as `raw:NullValue` without a literal value. Occurrences can be IRIs
or blank nodes. A literal retains its RDF datatype or language; there is no
requirement to convert native source values to strings.

Keep text as text when the source supplies no type. Capture must not infer that
an identifier such as `"00123"` is numeric merely because it contains digits.
Source readers are responsible for producing valid RDF literals and mapping
available source types faithfully; domain interpretation belongs to subsequent
transformations.

`raw:sourceText` is an optional, single `xsd:string` recording original text
exposed by the source reader before normalization. It can preserve `"0007"`
alongside the typed number `7`. Do not invent original text by formatting a
parsed value. Reader-exposed cell text does not preserve file bytes, delimiter
quoting, spreadsheet formulas, or complete display formatting; those require
retaining the source or additional format-specific metadata.

| Captured condition | Representation |
| --- | --- |
| A source-supplied scalar value | One `literalValue` with its available datatype or language. |
| An empty string or whitespace | A string literal retaining that content. |
| Zero or false | A numeric or boolean literal; neither denotes missing content. |
| Explicit source null | `a raw:NullValue`, with no `literalValue`. Optional `sourceText` can retain the source null marker. |
| Content metadata missing | Invalid. Missing triples do not imply a source null. |
| Source field absent | Do not invent a value or null occurrence. Source-structure rules are separate from this content contract. |

A string such as `"NULL"` remains a string unless the source format or an
explicit capture policy identifies it as a null marker. The distinction between
original text and an interpreted value is also present in the
[W3C tabular data model](https://www.w3.org/TR/tabular-data-model/#cells).

## Source location

| Relationship | Meaning |
| --- | --- |
| `raw:valueOf` | Each value occurrence identifies exactly one source `Row`. |
| `raw:forColumn` | Each value occurrence identifies exactly one physical `Column`. |
| `raw:isRowInView` | Each row belongs to exactly one `View`. |
| `raw:hasColumn` / `raw:isColumnInView` | Each column belongs to exactly one view. Assert either direction or both consistently. |

Domains and ranges infer the endpoint classes. A view can contain many columns;
one column can have value occurrences from many rows. A column is specific to
its view: a column in a different view is a different physical column even when
the headers or mapped predicates match. The model permits IRIs and blank nodes
for these resources.

The row and column of an occurrence must belong to the same view. Validation
counts both column-membership directions and counts a repeated link to the same
view once. It rejects missing or multiple rows, columns, or containing views,
nonresource endpoints, and mismatched row/column views. `NullValue` occurrences
have the same location requirements as literal-bearing occurrences.

`forPredicate` and a column's `predicate` record mappings, not physical source
locations. They do not replace `forColumn` or establish column identity.

## Executable examples

```turtle
@prefix raw: <https://ekgf.org/ontology/raw#> .
@prefix ex: <https://example.test/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:source a raw:XlsxFile ; raw:hasView ex:view ;
    raw:gitBlob "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391" ;
    raw:gitCommit "7cb0e12ad31958cab0cac1994784b5ccd90c8d8b" ;
    raw:gitPath "data/orders.xlsx" ; raw:gitModified false .
ex:view raw:viewNumber 1 ;
    raw:hasColumn ex:textColumn, ex:numberColumn, ex:amountColumn,
    ex:dateColumn, ex:translationColumn, ex:emptyColumn, ex:zeroColumn,
    ex:falseColumn, ex:nullColumn, ex:totalColumn .
ex:totalColumn raw:formulaR1C1 "RC[-2]*RC[-1]" .
ex:row raw:isRowInView ex:view .

ex:text a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:textColumn ;
    raw:literalValue "00123" .
ex:paddedNumber a raw:Value ;
    raw:valueOf ex:row ; raw:forColumn ex:numberColumn ;
    raw:literalValue 7 ; raw:sourceText "0007" .
ex:amount a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:amountColumn ;
    raw:literalValue "12.50"^^xsd:decimal .
ex:date a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:dateColumn ;
    raw:literalValue "2026-10-26"^^xsd:date .
ex:translation a raw:Value ;
    raw:valueOf ex:row ; raw:forColumn ex:translationColumn ;
    raw:literalValue "bonjour"@fr .
ex:empty a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:emptyColumn ;
    raw:literalValue "" .
ex:zero a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:zeroColumn ;
    raw:literalValue 0 .
ex:false a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:falseColumn ;
    raw:literalValue false .
ex:null a raw:NullValue ; raw:valueOf ex:row ; raw:forColumn ex:nullColumn .
ex:total a raw:Value ; raw:valueOf ex:row ; raw:forColumn ex:totalColumn ;
    raw:literalValue 20.0 ;
    raw:formula "A2*B2" ; raw:formulaR1C1 "RC[-2]*RC[-1]" .
```

The view contains ten physical columns. The single row has one occurrence for
each demonstrated field. Column types are inferred from `hasColumn` and
`forColumn`; explicit column type assertions are unnecessary with inference.
`tests/test_raw_values.py` parses and validates them and checks null/content
conflicts, missing or multiple literals, nonliteral payloads, optional source
text, subclass coverage, inference, and standard SHACL meta-validation.
`tests/test_raw_locations.py` validates the complete example and tests required
locations, both membership directions, view consistency, untyped and subclassed
resources, and distinct columns sharing a mapping.

## Validation and migration

From the repository root, with the test dependencies installed:

```sh
pyshacl -s ekgf-raw.ttl -e ekgf-raw.ttl -i rdfs raw-data.ttl
```

This loads the local schema without fetching imports. `ValueContentShape`
targets `Value` instances and subclasses, plus subjects using `literalValue`,
`sourceText`, `valueOf`, `forPredicate`, or `forColumn`. Untyped occurrence
metadata cannot bypass content or location checks. `ValueLocationShape`,
`RowLocationShape`, and `ColumnLocationShape` check the physical location and
the shared view. All four shapes and their nested constraints belong to the
Raw Data Ontology's shapes graph. Column membership is validated with SHACL paths
in either direction; RDFS inference suffices without an OWL inverse closure.

Existing value occurrences without content now fail validation. Add their
source-supplied `literalValue`, or explicitly classify actual source nulls as
`NullValue`; preserve occurrence identities and references. Recover content
from the original source or the capture application's documented representation.
Do not derive it from IRIs or assign a mapped row value to an occurrence without
establishing the correspondence. When content cannot be recovered, recapture
the source instead of guessing.

Existing occurrences also need `valueOf` and `forColumn`. Retain valid row
links, identify the actual physical column from the source or documented
capture metadata, and record each row's and column's containing view. Do not
assign columns by joining mapped predicates alone; that can select several
columns or columns from unrelated views. Missing or ambiguous correspondence
requires recapturing or resolving the source metadata, not a guessed mapping.

OWL describes content alternatives, endpoint classes, inverse membership, and
cardinalities. Functional relationships can equate conflicting row, column,
or view IRIs under OWL semantics. Validate a coherent capture context before
running OWL identity reasoning; the SHACL checks compare supplied resource
terms and reject conflicting assignments. Named graphs do not isolate
historical captures unless the application selects them for validation.
Neither mechanism fabricates content, null classifications, original text,
or physical source locations.

## Capture metadata

These terms describe where captured data came from and how a spreadsheet
computed it. They are validated by `ViewNumberShape`, `GitOriginShape`,
`FormulaShape` and `FormulaR1C1Shape` in the Raw Data Ontology's shapes graph.

- **Formats.** `CsvFile` and `TsvFile` are `File`s whose fields are always
  captured as text. `XlsxFile` covers workbooks. A `ParquetFile` is one view
  whose columns are the schema's top-level fields. Its values keep the
  datatypes that Parquet's types define.
- **View order.** `viewNumber` is the 1-based position of a view within its
  source, such as the worksheet order. Names can repeat and change, so they do
  not identify a view.
- **Git origin.** `gitBlob` is the git object id of the captured bytes. It is
  recorded for every file, whether or not the file is in a repository. A file in
  a work tree also records `gitCommit` (HEAD), `gitPath` (work-tree relative,
  using `/`) and `gitModified`. The optional `gitRepository` is the default
  remote's URL. `gitModified false` means the capture can be reproduced from
  history. Commit, path and modification state are recorded together.
- **Embedded checksums.** A file cannot contain the checksum of its own final
  bytes. A capture step that embeds a checksum in its output therefore computes
  it over the bytes before the checksum and records their number with
  `checksumByteCount` on the `spdx:Checksum`. Verifying it means hashing the
  first `checksumByteCount` bytes, for example `head -c N file | sha256sum`.
  A checksum without `checksumByteCount` covers the whole file.
- **Formulas.** A formula cell is an ordinary `Value` whose `literalValue` is
  the result the source cached. If there is no cached result, it is a
  `NullValue`. `formula` keeps the A1 text verbatim, without the leading `=`.
  `formulaR1C1` keeps the same formula with references made relative to the
  cell. On a `Column`, `formulaR1C1` states that every formula in the column
  has this one relative form. Such a column is a derivation rule, for example
  `RC[-2]*RC[-1]`, which a later step can translate into a SPARQL or SHACL rule.

The executable example below shows a formula occurrence, its column rule,
the view number and the git origin of its source.

## Column profile

A capture step may profile each column. It writes exact measures on the
`Column`, computed over the column's value occurrences; header cells are not
occurrences. `ColumnProfileShape` validates the profile.

- **Counts.** `count` is the number of non-null occurrences, and `nullCount`
  the number of `NullValue`s. `unique` is the number of distinct literal terms.
  `top` is the most frequent literal and `freq` how often it occurs. A measure
  that was not computed, for example because a column exceeded a capture-time
  limit, is absent rather than zero.
- **Datatype evidence.** `inferredDatatype` names a datatype that the column's
  values conform to, and `conformingCount` says how many do. The values
  themselves keep their source literals, so a column of mostly ISO dates is
  stated as `inferredDatatype xsd:date` with, for example, `conformingCount 98`
  of `count 100`. A later step can cast with known confidence and inspect the
  exceptions. The candidate datatypes and the required share are capture policy.
- **Statistics.** These cover the occurrences that conform to the inferred
  datatype. `min` and `max` are literals of that datatype. `mean`, `std`
  (sample standard deviation) and the `25pct`, `50pct` and `75pct` percentiles
  (linear interpolation, Hyndman and Fan type 7) are `xsd:double` values and
  apply only to numeric datatypes.

## S3 objects

A source read from Amazon S3, or from an S3-compatible store, is also an
`S3Object`, alongside its format class. The capture step records the object
as the store reported it when it was read:

- **Location:** `s3Bucket`, `s3Key`, and optionally `s3Region`, `s3Endpoint`
  (for stores other than Amazon S3) and `s3VersionId`.
- **Object metadata:** `s3ETag` (without its quotes), `s3ContentType`,
  `s3ContentEncoding`, `s3ContentLanguage`, `s3ContentDisposition`,
  `s3CacheControl`, `s3StorageClass`, `s3PartsCount`, `s3ReplicationStatus`
  and `s3Expiration`, each verbatim.
- **Checksums:** `s3ChecksumType` and the CRC32, CRC32C, CRC64NVME, SHA-1 and
  SHA-256 checksums S3 stores, base64-encoded as S3 returns them. These are
  separate from the SHA-256 the capture step computes over the content.
- **Encryption and retention:** `s3ServerSideEncryption`, `s3KmsKeyId`,
  `s3BucketKeyEnabled`, `s3ObjectLockMode`, `s3ObjectLockRetainUntil` and
  `s3ObjectLockLegalHold`.
- **Tags and user metadata:** key-value entries, linked with `s3Tag` and
  `s3UserMetadata`, each with `s3EntryKey` and `s3EntryValue`.

`S3ObjectShape` and `S3EntryShape` validate these.

The S3 properties, like the git origin properties, describe one place where
the content was found, but they are stated on the content-addressed source.
The same bytes stored under two keys and captured in separate runs therefore
give one source with conflicting location metadata. Whether locations should
become resources of their own is an open modelling question.

## Remaining model work

Content and row/column location are validated. The following work is still open:

- Preservation of original column headers and view names.
- Further structural validation, including view-to-source ownership and
  distinct structural roles.
- Coordinate conventions and bounds.
- Source-key structure and identity policy.
- The semantics and property type of predicate mappings.
- Separating where content was found (file paths, git origins, S3 objects)
  from the content itself.
- Translation of column formulas (`formulaR1C1`) into SPARQL or SHACL rules,
  and cross-view formula references.

Content and location validation do not establish that a whole capture dataset is
structurally complete or faithful to its original source.
