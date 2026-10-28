# Story stereotypes

[Documentation index](../README.md#documentation)

The [Story Ontology](../ekgf-story.ttl) provides an optional primary-purpose
classification through `story:hasStereoType`, with range `story:StoryStereoType`.
The naming follows `UseCaseStereoType` and `hasStereoType` in the Use Case
Ontology. The Story and Use Case properties have different domains and ranges.

A story can have **zero or one** primary stereotype. No classification is
inferred when none is asserted. A stereotype can classify many distinct stories.
It is an individual of `StoryStereoType`, not a Story subclass or an executable
implementation.

## Built-in classifications

| Individual in the Story namespace | Primary purpose |
| --- | --- |
| `StoryStereoTypeQuery` | Retrieve or present information. |
| `StoryStereoTypeUpdate` | Apply an explicitly requested change to data. |
| `StoryStereoTypeTransformationRule` | Derive or transform data according to a rule. |
| `StoryStereoTypeValidationRule` | Assess data against requirements and report conformance or violations. |

Select the primary purpose when a story performs several activities. For
example, a rule that computes derived values is classified as Transformation
Rule even if its implementation also retrieves data. Use an application-defined
stereotype when the existing definitions do not fit; do not assign two primary
classifications to describe secondary activities.

The four built-ins are distinct individuals. They do not exhaust the vocabulary:
there is no `owl:oneOf` or SHACL enumeration restricting applications to them.
Additional stereotypes require an IRI, a nonempty literal `rdfs:label`, and a
meaningful nonempty literal definition in `rdfs:comment` or
`annotation:markdownDescription`. Language-tagged definitions are supported.
These checks establish metadata coverage, not the business accuracy of a
classification or definition.

## Purpose and implementation

Classify the story, while its implementations describe how it is delivered.
A validation story can use a query or API. A transformation story can use a
pipeline, query, or rule engine. Neither "Query" nor "Rule" in a stereotype
selects a language or processor.

Stereotypes do not infer `isUpdate`, `isDeletion`, or any execution behavior.
Those flags keep their separately documented meanings. Flags and implementation
classes also do not infer stereotypes. Dispatch must use the selected
implementation and its execution contract, not a classification label.
The story, its implementation, its concept usages, and the stereotype resource
have distinct roles; implementations and usages cannot receive story
classifications. Story and StoryImplementation are declared disjoint.

## Example

```turtle
@prefix story: <https://ekgf.org/ontology/story#> .
@prefix ex: <https://example.test/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:findRecords story:hasStereoType story:StoryStereoTypeQuery .
ex:applyChange story:hasStereoType story:StoryStereoTypeUpdate .
ex:deriveAmount story:hasStereoType story:StoryStereoTypeTransformationRule .
ex:assessRecord story:hasStereoType story:StoryStereoTypeValidationRule .

ex:Reconciliation a story:StoryStereoType ;
    rdfs:label "Reconciliation"@en ;
    rdfs:comment "Identifies and explains differences between source records."@en .
ex:reconcileRecords story:hasStereoType ex:Reconciliation .
```

The property's domain infers that the five subjects are Stories. Its range
infers the stereotype type. The built-in definitions are supplied by the
Story ontology; the example supplies the custom definition explicitly.
Stories do not need an implementation or concept usage merely to be classified.
Implementations, when supplied, still require exactly one owning story.

## Validation

From the repository root, with the test dependencies installed:

```sh
pyshacl -s ekgf-story.ttl -e ekgf-story.ttl -i rdfs story-data.ttl
```

Load custom stereotype definitions with the data or in the supplied ontology
graph. `StoryClassificationShape` checks assignments and accepts stories without
one. `StoryStereoTypeShape` checks all supplied stereotype definitions, including
subclasses and objects of `hasStereoType`. A bare, undocumented IRI fails even
though the range can infer its class.

Both shapes and their nested constraints belong to the Story
`ValidationShapeSet`. `tests/test_story_stereotypes.py` validates the example
and checks extensibility, metadata, inference, optionality, cardinality,
role separation, distinct story identities, and independence from implementation
technology and mutation flags.

OWL functionality may equate otherwise unconstrained custom stereotype IRIs.
SHACL counts supplied resource terms and rejects multiple assignments. Validate
a coherent version context before OWL identity reasoning. Named graphs do not
automatically isolate historical classifications when their contents are merged.

## Migration and remaining work

Existing unclassified stories remain valid. For an application-specific
classification, confirm its meaning before mapping it to a built-in individual.
Replace its assignment predicate with `story:hasStereoType` and its value with
the corresponding stereotype IRI. Retain story identities. When a custom
meaning is needed, keep its IRI, type it as `story:StoryStereoType`, and supply
its label and definition. Do not choose classifications automatically from
story titles, implementation languages, or boolean flags.

No presentation verb is required by this model. Human-readable labels and
definitions describe classifications; application sentence construction is a
separate concern.

SHACL-based implementation selection, including references to executable
shapes and the distinction between validation and rule execution, remains
separate modeling work. A Validation Rule stereotype alone does not declare a
SHACL implementation or provide an executable validator.
