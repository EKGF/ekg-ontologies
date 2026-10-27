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

ex:source raw:hasView ex:view .
ex:view raw:hasColumn ex:textColumn, ex:numberColumn, ex:amountColumn,
    ex:dateColumn, ex:translationColumn, ex:emptyColumn, ex:zeroColumn,
    ex:falseColumn, ex:nullColumn .
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
```

The view contains nine physical columns. The single row has one occurrence for
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
Raw Data `ValidationShapeSet`. Column membership is validated with SHACL paths
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

## Remaining model work

Content and row/column location are validated. The following work is still open:

- Preservation of original column headers and view names.
- Further structural validation, including view-to-source ownership and
  distinct structural roles.
- Coordinate conventions and bounds.
- Source-key structure and identity policy.
- The semantics and property type of predicate mappings.

Content and location validation do not establish that a whole capture dataset is
structurally complete or faithful to its original source.
