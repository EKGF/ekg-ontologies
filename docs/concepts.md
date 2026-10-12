# Data element concepts and manifestations

[Documentation index](../README.md#documentation)

The [concept ontology](../ekgf-concept.ttl) defines
`ekg-concept:DataElementConcept`, called a **concept** for short:

> A reusable concept identifying the meaning of a data element or
> compound data construct, independently of its particular business
> or technical manifestations.

## Reuse and identity

A concept identifies a shared meaning. Its manifestations and graph
relationships express and describe that meaning. Reuse the same
concept across use cases, stories, languages and systems wherever
that meaning applies.

A concept is not inherently scoped to a particular context. Separate
concepts may be created where needed; independently created concepts
may later be merged when their owners establish that they represent
the same meaning. Matching names alone do not establish that identity.

`ConceptSet` groups related concepts under governance.
`ConceptManifestation` represents their business and technical
expressions. Properties such as `hasConcept`, `hasManifestation` and
`concept` use the everyday short form in their names.

## Relationship to ISO/IEC 11179

This class deliberately generalizes the data element concept in
[ISO/IEC 11179-31:2023][iso-11179], section 3.25. It follows the
distinction between a concept and its representation. In the ISO
model, a data element concept is associated with an object class and
a property, such as Customer and Identifier; a data element provides
a representation through an associated value domain.

The EKG class extends that scope to compound data constructs. A
concept may identify the meaning of a whole entity type or compound
structure, with an entire OWL class or SHACL shape as a manifestation.
This is a broader scope, rather than a claim of formal equivalence to
the ISO model.

[iso-11179]: https://www.iso.org/standard/78925.html

## Manifestations and occurrences

Users and code encounter a concept through its manifestations. The
same customer-identifier concept might appear as the business term
"Customer identifier", the SPARQL variable `?customerId`, the Python
variable `customer_id`, and the API parameter `customerId`.

A business term supplies a human-facing name or description.
Technical manifestations supply expressions in particular languages
and systems. For RDF resources, a manifestation links to the resource
through `manifestationResource`. A `ManifestationOccurrence` records
a particular sighting in a source, including its repository, path,
line or commit.

For example, these business, SPARQL and API manifestations share one
concept:

```turtle
@prefix ex: <https://example.org/> .
@prefix ekg-concept: <https://ekgf.org/ontology/concept#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:customerIdentifier
    a ekg-concept:DataElementConcept ;
    ekg-concept:preferredBusinessTerm ex:customerIdentifierTerm ;
    ekg-concept:preferredQueryParameterManifestation ex:customerIdAPI ;
    ekg-concept:hasManifestation ex:customerIdSPARQL .

ex:customerIdentifierTerm
    a ekg-concept:BusinessTerm ;
    rdfs:label "Customer identifier"@en .

ex:customerIdSPARQL
    a ekg-concept:SPARQLVariableManifestation ;
    ekg-concept:manifestationValue "?customerId" .

ex:customerIdAPI
    a ekg-concept:URIParameterManifestation ;
    ekg-concept:manifestationValue "customerId" .
```

`DataElementConcept` has no `skos:Concept` superclass. A SKOS concept
can be linked through a `SKOSConceptManifestation`, just as an OWL
class or SHACL shape can be linked through its respective technical
manifestation. This does not classify the shared concept as any of
those resources or identify it with them.

## Migration from Concept

The formal class IRI changes from `ekg-concept:Concept` to
`ekg-concept:DataElementConcept`. Update stored RDF, SPARQL queries,
SHACL shapes and consumer code that refer to the old class. There is
no alias or equivalence axiom for the retired IRI.

The namespace `https://ekgf.org/ontology/concept#`, preferred prefix
`ekg-concept`, source filename, `ConceptSet`, `ConceptManifestation`
and property names retain the short form. Story and use-case links,
class disjointness and the default lifecycle now reference the new
class.

Replace previous ontology graphs when loading this version so the
retired class declarations and the former SKOS superclass axiom in
the persona ontology are removed. The concept ontology supplies the
class definition; the story ontology no longer supplies a separate
definition tied to a business term.
