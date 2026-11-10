# Occurrence containment

[Documentation index](../README.md#documentation)

`concept:occursWithin` links an observed manifestation occurrence to another
occurrence directly containing it in the same source context. For example, a
column occurrence can appear within a worksheet occurrence. The relationship
belongs to the [Concept Ontology](../ekgf-concept.ttl).

## Meaning and identity

A DataElementConcept identifies reusable meaning. A ConceptManifestation
expresses that meaning, and a ManifestationOccurrence records one appearance
of that expression. Occurrences are disjoint from concepts and manifestations.

The same attribute concept can occur in different compound structures. Record
the context on the occurrence rather than asserting universal containment
between the concepts or their manifestations. A column token appearing in two
worksheets has two occurrences, even if both express the same concept through
one shared manifestation.

`occursWithin` is neither functional nor inverse-functional. An occurrence can
have several direct containers when source analysis establishes those contexts,
and each container can have several children. Sharing a container or a
manifestation does not merge occurrence identities. Both named and blank-node
occurrences are supported.

Containment is irreflexive and must be acyclic. The property is not transitive:
an indirect ancestor is found with the SPARQL path `occursWithin+` and is not
materialized as a direct parent. The harvester determines which edges represent
direct containment in its observed structural model.

## Example

The worksheet and its identifier column express separate compound and attribute
concepts. Their occurrences record where the column was found. Save this as
`observations.ttl`:

```turtle
@prefix concept: <https://ekgf.org/ontology/concept#> .
@prefix ex: <https://example.test/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:recordIdentifierConcept a concept:DataElementConcept ;
    rdfs:label "Record identifier"@en ;
    concept:hasManifestation ex:identifierColumn .

ex:recordConcept a concept:DataElementConcept ;
    rdfs:label "Record"@en ;
    concept:hasManifestation ex:recordsWorksheet .

ex:identifierColumn a concept:RawSourceFieldManifestation ;
    concept:manifestationValue "record_id" .

ex:recordsWorksheet a concept:TechnicalManifestation ;
    concept:manifestationResource ex:worksheetResource .

ex:identifierOccurrence a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:identifierColumn ;
    concept:occursWithin ex:worksheetOccurrence ;
    concept:sourceSystem ex:recordsSource ;
    concept:sourcePath "capture/records.xlsx" .

ex:worksheetOccurrence a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:recordsWorksheet ;
    concept:sourceSystem ex:recordsSource ;
    concept:sourcePath "capture/records.xlsx" .
```

This query relates the observed attribute concept to the observed compound
concept, retaining the occurrence identities that supply the context:

```sparql
PREFIX concept: <https://ekgf.org/ontology/concept#>

SELECT DISTINCT ?attributeOccurrence ?compoundOccurrence
                ?attributeConcept ?compoundConcept WHERE {
    ?attributeOccurrence concept:occursWithin ?compoundOccurrence ;
        concept:occurrenceOf/(^concept:hasManifestation|concept:concept)
            ?attributeConcept .
    ?compoundOccurrence
        concept:occurrenceOf/(^concept:hasManifestation|concept:concept)
            ?compoundConcept .
}
```

The example returns the identifier concept in the context of the record concept.
It accepts either direct concept/manifestation link direction without requiring
materialized inverses. If concept links use specialized preferred-manifestation
properties, load their schema and apply RDFS inference to expose the general
`hasManifestation` relationship first.

## Source context

An analyzer must establish containment from the source structure. Matching a
path, position, type or manifestation identifier is insufficient to create an
edge. A reference to a named definition has its own occurrence; the definition
does not become physically contained in every location referencing it. Typing
one source variable with several classes does not by itself establish nesting.

The current location fields do not form a unique statement or source-artifact
key. A file can contain several statements, and the same path can recur in
different systems, repositories or versions. Harvesters must resolve the source
and structural boundaries explicitly. Select a coherent source/version view
when validating and querying observations.

Source metadata remains on the occurrence recording that observation.
Containment does not copy paths, systems, commits or coordinates from a parent
to its children. The ontology does not add source fields or prescribe coordinate
indexing conventions as part of this change.

## Declarations and observations

A Story's input, output and dependent usages describe its declared concept
contract. Occurrences in an implementation describe observed source appearances.
Neither side is inferred from the other.

An analyzer can compare those sets once it has scoped occurrences to the
selected implementation and its actual statement or template. A file path and
line number alone do not establish that scope. Include dependent usages when
checking whether an observed concept was declared; not every internal concept
is an input or output.

A declared concept without a matching observation is a diagnostic requiring
interpretation. It does not alone prove that an input is ignored: harvest
coverage, indirect use, template rendering and service-side input handling can
affect what the analyzer observes. Likewise, an observed source appearance does
not by itself establish an input or output role.

An occurrence in a shape specification records the observed appearance of
that specification. The constraints expressed by the shape describe requirements
on data; the occurrence record does not establish that the data satisfies them.

## Validation

With the [test dependencies](../README.md#validation) installed, run:

```sh
pyshacl -s ekgf-concept.ttl -e ekgf-concept.ttl -i rdfs observations.ttl
```

`OccurrenceContainmentShape` targets both endpoints, including endpoints without
explicit types. RDFS inference supplies ManifestationOccurrence types from the
property's domain and range. With inference disabled, supply those types
explicitly. Validation rejects literal endpoints, concept or manifestation role
conflicts, direct self-links and longer cycles. It permits roots, multiple
parents and multiple children.

The validator and its nested constraints are registered in the Concept
`ValidationShapeSet`, bound to the module's concrete ShapesGraph through
`shape:hasShapesGraph`.

Validation checks the supplied RDF structure. It does not read files, prove
same-source membership, compare provenance values for equality, establish
harvest completeness, or execute a Story mismatch analysis. Harvesters are
responsible for asserting observed same-context containment.

`tests/test_occurrence_containment.py` validates and queries this example and
checks endpoint inference, identity separation, multiple containers, optional
parents, named and blank occurrences, cycles, metadata and independence from
Story declarations and shared manifestation identity.
