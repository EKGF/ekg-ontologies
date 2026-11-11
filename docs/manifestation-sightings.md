# Manifestation sightings

[Documentation index](../README.md#documentation)

A data element concept (DEC) is a logical data element with all its various
forms of physical manifestations and their sightings. The
[Concept Ontology](../ekgf-concept.ttl) keeps these as three layers:

| Layer | Resource | Answers |
| --- | --- | --- |
| Meaning | `DataElementConcept` | What does the data element mean? |
| Manifestation | `ConceptManifestation` | How is it expressed: as a business term, or as one of many kinds of technical term? |
| Sighting | `ManifestationOccurrence` | Where was each manifestation observed, and in which statement position? |

Sightings are the evidence of how a logical data element manifests physically.
The same concept can be a column in one dataset and a placeholder in a story's
statement template. Both are true facts about where the concept turns up, but
they are different kinds of appearance.

## Where: `foundIn`

`concept:foundIn` links a sighting to each artifact in which it was observed:
a dataset, a dataset file, a statement template, a story implementation, a
raw-data view or a code file. Record every level that the harvester resolves.
A placeholder in a template can be found in the template, in the story
implementation using it, and in the dataset containing the template's file.

The values are resources, not paths. Paths, lines and columns remain literals
that locate the sighting within an artifact. Two sightings with the same path
do not share an artifact unless the harvester asserts the same artifact
resource. Containment between sightings uses
[`occursWithin`](occurrence-containment.md).

## How: manifestation type and statement position

The manifestation's class records the kind of expression, for example
`RawSourceFieldManifestation` for a source column or
`TemplateParameterManifestation` for a template placeholder. Within a query or
update statement, `concept:statementPosition` records the role of an appearance:

| Position | Appearance | Expected Story usage |
| --- | --- | --- |
| `ParameterPosition` | A value supplied for the invocation: a template placeholder, or a variable the service pre-binds under its documented binding profile. | Input |
| `ProjectionPosition` | A result the statement returns: a projected `SELECT` variable or alias, or a `DESCRIBE` target. | Output |
| `GraphTemplatePosition` | A term in the statement's `CONSTRUCT` template, `INSERT` template or `INSERT DATA`. | Output |
| `GraphPatternPosition` | A term in the graph pattern matched against data: the `WHERE` clause, its filters, bindings and nested patterns, and its solution modifiers. | Dependent |

One appearance can have several positions. A placeholder inside a triple
pattern is a parameter appearing in the graph pattern; record both. Classify
the parameter position from the template language or the service's binding
profile, not from spelling: SPARQL treats `$name` and `?name` as the same
variable. A projection inside a subquery belongs to the enclosing graph
pattern. A positioned sighting must identify at least one artifact through
`foundIn`.

The positions do not classify terms in `DELETE` templates or `DELETE DATA`.
Which Story usage such a term implies is an open modeling decision, so an
analyzer must not record it as `GraphTemplatePosition`.

`StatementPosition` is an extensible classification. Application-defined
positions need an IRI, a label and a definition. When they are compared with
Story declarations, they must also map to one usage role through
`ekg-story:expectedUsageRole`.

## Used, not declared

The [Story Ontology](../ekgf-story.ttl) maps each position to the usage that
it leads an analysis to expect. `UndeclaredConceptUsageShape` compares that
evidence with the usages declared by the implemented story. It reports a
**warning** per implementation, concept and missing role:

- Parameter evidence without an input usage of the concept.
- Projection or graph-template evidence without an output usage.
- A concept sighted only in graph patterns, without any declared usage.
  Inputs and outputs also appear in graph patterns, so any declared role
  satisfies this expectation.

The result's focus node is the implementation and its value is the concept.
Its message names the expected usage class. Sightings outside story
implementations, for example in a dataset alone, are not compared.

The comparison does not report the reverse: a declared usage without a
matching sighting. Harvest coverage, indirect use, template rendering and
service-side input handling can each explain a missing sighting, so it
requires interpretation rather than a warning. Sightings never create or
change declared usages.

## Example

A product-category concept manifests as a column in a catalog extract and as
a placeholder in a story's statement template. The template
`SELECT ?product WHERE { ?product ex:inCategory $category }` filters by the
category. The story declares its product output, but not the category input.
Save this as `sightings.ttl`:

```turtle
@prefix concept: <https://ekgf.org/ontology/concept#> .
@prefix dataset: <https://ekgf.org/ontology/dataset#> .
@prefix story: <https://ekgf.org/ontology/story#> .
@prefix sparql: <https://ekgf.org/ontology/story-impl-sparql#> .
@prefix ex: <https://example.test/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# The logical data elements and how they manifest.
ex:productCategory a concept:DataElementConcept ;
    concept:preferredBusinessTerm ex:productCategoryTerm ;
    concept:hasManifestation ex:categoryColumn , ex:categoryPlaceholder .

ex:productCategoryTerm a concept:BusinessTerm ;
    rdfs:label "Product category"@en .

ex:categoryColumn a concept:RawSourceFieldManifestation ;
    concept:manifestationValue "product_category" .

ex:categoryPlaceholder a concept:TemplateParameterManifestation ;
    concept:templateLanguage ex:dollarTemplateLanguage ;
    concept:manifestationValue "$category" .

ex:product a concept:DataElementConcept ;
    concept:hasManifestation ex:productVariable .

ex:productVariable a concept:SPARQLVariableManifestation ;
    concept:manifestationValue "?product" .

ex:dollarTemplateLanguage a concept:TemplateLanguage ;
    rdfs:label "Python string.Template syntax"@en ;
    rdfs:seeAlso <https://docs.python.org/3/library/string.html#template-strings> .

# The artifacts.
ex:catalogExtract a dataset:Dataset ;
    rdfs:label "Product catalog extract"@en .

ex:storyDefinitions a dataset:Dataset ;
    rdfs:label "Story definitions"@en .

ex:listProducts a story:Story ;
    story:hasOutputConcept [ concept:hasConcept ex:product ] ;
    story:implementedBy ex:listProductsImplementation .

ex:listProductsImplementation
    a story:NamedStatementImplementation , sparql:StorySPARQLTemplateImplementation ;
    sparql:hasTemplate ex:listProductsTemplate ;
    sparql:usesRenderer ex:exampleRenderer .

ex:listProductsTemplate a sparql:StatementTemplate ;
    concept:templateLanguage ex:dollarTemplateLanguage ;
    sparql:templateFileName "list-products.rq.template" .

ex:exampleRenderer a sparql:TemplateRenderer ;
    sparql:supportsTemplateLanguage ex:dollarTemplateLanguage .

# Where and how the manifestations were sighted.
ex:categoryColumnSighting a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:categoryColumn ;
    concept:foundIn ex:catalogExtract ;
    concept:sourcePath "extracts/catalog.csv" .

ex:categoryPlaceholderSighting a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:categoryPlaceholder ;
    concept:foundIn ex:listProductsTemplate , ex:listProductsImplementation ,
        ex:storyDefinitions ;
    concept:statementPosition concept:ParameterPosition , concept:GraphPatternPosition ;
    concept:sourcePath "stories/list-products.rq.template" .

ex:productProjectionSighting a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:productVariable ;
    concept:foundIn ex:listProductsTemplate , ex:listProductsImplementation ,
        ex:storyDefinitions ;
    concept:statementPosition concept:ProjectionPosition ;
    concept:sourcePath "stories/list-products.rq.template" .
```

This query lists the datasets in which the product category was sighted, and
how it appears in each:

```sparql
PREFIX concept: <https://ekgf.org/ontology/concept#>
PREFIX dataset: <https://ekgf.org/ontology/dataset#>
PREFIX ex: <https://example.test/>

SELECT DISTINCT ?dataset ?how ?position WHERE {
    ?sighting concept:occurrenceOf ?manifestation ;
        concept:foundIn ?dataset .
    ?dataset a dataset:Dataset .
    ?manifestation (^concept:hasManifestation|concept:concept) ex:productCategory ;
        a ?how .
    OPTIONAL { ?sighting concept:statementPosition ?position }
}
```

It returns the catalog extract with a `RawSourceFieldManifestation` and no
position, and the story definitions with a `TemplateParameterManifestation` in
the parameter and graph-pattern positions. Run on the asserted data, `?how` is
the asserted manifestation class. With RDFS inference, superclasses such as
`TechnicalManifestation` also match.

## Validation

With the [test dependencies](../README.md#validation) installed, validate the
sightings against the Concept Ontology:

```sh
pyshacl -s ekgf-concept.ttl -e ekgf-concept.ttl -i rdfs sightings.ttl
```

Then compare them with the Story declarations:

```sh
pyshacl -s ekgf-story.ttl -e ekgf-story.ttl -i rdfs sightings.ttl
```

The second command reports one warning: `ex:productCategory` was sighted in
`ex:listProductsImplementation` in a position expecting a `StoryInput` usage,
and `ex:listProducts` declares none. The product output is declared, and
the category's graph-pattern position adds no dependent expectation, because
the same concept has input evidence. Add `--allow-warnings` to treat the
warning as conforming while violations still fail.

`OccurrenceSightingShape` and `StatementPositionShape` belong to the Concept
`ValidationShapeSet`. `StatementPositionUsageRoleShape` and
`UndeclaredConceptUsageShape` belong to the Story `ValidationShapeSet`. The
first Story shape rejects a position without exactly one expected role, so a
missing mapping fails instead of disabling the comparison.

Validation checks the supplied graph. It does not read sources, establish
harvest completeness or confirm that asserted artifacts and positions match the
source text. Harvesters are responsible for those observations.

[`tests/test_manifestation_sightings.py`](../tests/test_manifestation_sightings.py)
validates and queries this example. It also covers artifact and position
constraints, the position mappings, each expected role, per-implementation
scoping, either ownership direction, missing mappings, and independence of
sightings from Story declarations.
