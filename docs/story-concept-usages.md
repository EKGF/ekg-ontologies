# Story concept usages

[Documentation index](../README.md#documentation)

The [Story Ontology](../ekgf-story.ttl) separates a story's use of a concept
from the reusable meaning defined by the [Concept Ontology](../ekgf-concept.ttl).
The following classes, properties, and constraints are implemented in OWL and
SHACL.

| Story predicate | Inferred usage class |
| --- | --- |
| `hasInputConcept` | `StoryInput` |
| `hasOutputConcept` | `StoryOutput` |
| `hasDependentConcept` | `StoryDependent` |

All three classes specialize `StoryConceptUsage`. All three predicates
specialize `hasConceptUsage`. A specialized predicate supplies the usage's
role through its range, so an explicit type assertion is unnecessary when
RDFS or OWL inference is enabled. With a direct `hasConceptUsage` assertion,
the role must be explicit or inferred from other assertions. For example,
either input flag infers `StoryInput` through its domain, even when its value
is false. A usage with no resolved role fails validation.

Each usage has exactly one owning story and exactly one `concept:hasConcept`
reference. The role classes are disjoint. A concept used as both an input and
an output has separate usage objects for those roles. Different stories also
have separate usage objects, even when they reference the same concept.
Usages may be blank nodes or IRIs. A story owns its usages; referencing a
concept does not transfer ownership of the concept to the story.

Consumers must preserve the identity of each usage object. Multiple usages
of the same concept on one story may carry different flags. Merging them by
concept IRI would lose those distinctions; a concept IRI is not a usage key.

The global `concept:hasConcept` property has no domain restriction. Its
exactly-one restriction is local to `StoryConceptUsage`; other resources
using the property do not become story usages.

## Input requirements and defaults

`isMandatory` and `isServerProvided` apply to input usages. Each accepts at
most one `xsd:boolean` value. The flags are independent: an input can be both
mandatory and supplied by the Story Service.

An absent flag means **false to a Story Service application**. Missing flags
are valid RDF and remain absent after OWL reasoning and SHACL validation.
`StoryInputShape` records `sh:defaultValue false` for both flags; that annotation
does not insert triples. An application may materialize explicit false values.
Neither flag specifies how an implementation injects or generates a value.

## Template documents and their language

A template-based implementation produces SPARQL by rendering a source
document in a declared template language. That document remains template
source until rendered, even if some of its text also parses as SPARQL.

| Resource | Representation |
| --- | --- |
| Template document | `sparql:StatementTemplate`, with `templateText`, `templateFileName`, or both, and one `concept:templateLanguage`. |
| Language/profile | `concept:TemplateLanguage`, with an IRI, label, and documentation reference. This identifies the source syntax, independently of the output language. |
| Renderer | `sparql:TemplateRenderer`, declaring `supportsTemplateLanguage`. |
| Template-based implementation | `sparql:StorySPARQLTemplateImplementation`, with one `hasTemplate` and one `usesRenderer`. The renderer must support the document's language. |
| Input placeholder | `concept:TemplateParameterManifestation`, with its exact token in `manifestationValue` and one `concept:templateLanguage`. |

Here `sparql:` abbreviates the SPARQL Story Implementation namespace
`https://ekgf.org/ontology/story-impl-sparql#`.

The rendered query or update is a separate runtime artifact for an invocation.
It is parsed before execution. The native-source fields `sparql` and `fileName`
are rejected on template-based implementations; their reusable source lives
on the linked template document. A direct SPARQL implementation can continue
to supply native SPARQL source through those fields.

## Executable example

Two stories below share a customer-identifier concept and its `$m`
template manifestation. They own different input usages and different
implementations, each linked to its own template document. The documents and
shared placeholder identify the same example language profile, and the
selected renderer declares support for it.
The first story also has an output usage, a dependent usage, and a mandatory
input supplied by the server. Both flags are absent on the second story's
input, so its effective application values are false.

```turtle
@prefix ex: <https://example.org/> .
@prefix story: <https://ekgf.org/ontology/story#> .
@prefix concept: <https://ekgf.org/ontology/concept#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sparql: <https://ekgf.org/ontology/story-impl-sparql#> .

ex:findCustomer a story:Story ;
    story:hasInputConcept [
        concept:hasConcept ex:customerIdentifier ;
        story:isMandatory true
    ] , [
        concept:hasConcept ex:tenantIdentifier ;
        story:isMandatory true ;
        story:isServerProvided true
    ] ;
    story:hasOutputConcept [ concept:hasConcept ex:customer ] ;
    story:hasDependentConcept [ concept:hasConcept ex:activeCustomer ] ;
    story:implementedBy ex:findCustomerSPARQL .

ex:updateCustomer a story:Story ;
    story:hasInputConcept [ concept:hasConcept ex:customerIdentifier ] ;
    story:implementedBy ex:updateCustomerSPARQL .

ex:findCustomerSPARQL
    a story:NamedStatementImplementation, sparql:StorySPARQLTemplateImplementation ;
    sparql:hasTemplate ex:findCustomerTemplate ;
    sparql:usesRenderer ex:exampleRenderer .
ex:updateCustomerSPARQL
    a story:NamedStatementImplementation, sparql:StorySPARQLTemplateImplementation ;
    sparql:hasTemplate ex:updateCustomerTemplate ;
    sparql:usesRenderer ex:exampleRenderer .

ex:findCustomerTemplate a sparql:StatementTemplate ;
    concept:templateLanguage ex:dollarTemplateLanguage ;
    sparql:templateFileName "find-customer.rq.template" .
ex:updateCustomerTemplate a sparql:StatementTemplate ;
    concept:templateLanguage ex:dollarTemplateLanguage ;
    sparql:templateFileName "update-customer.rq.template" .

ex:dollarTemplateLanguage a concept:TemplateLanguage ;
    rdfs:label "Python string.Template syntax"@en ;
    rdfs:seeAlso <https://docs.python.org/3/library/string.html#template-strings> .
ex:exampleRenderer a sparql:TemplateRenderer ;
    sparql:supportsTemplateLanguage ex:dollarTemplateLanguage .

ex:customerIdentifier a concept:DataElementConcept ;
    concept:hasManifestation ex:customerIdentifierTemplateParameter .
ex:tenantIdentifier a concept:DataElementConcept .
ex:customer a concept:DataElementConcept .
ex:activeCustomer a concept:DataElementConcept .

ex:customerIdentifierTemplateParameter a concept:TemplateParameterManifestation ;
    concept:templateLanguage ex:dollarTemplateLanguage ;
    rdfs:label "$m" ;
    concept:manifestationValue "$m" .

ex:findTemplateOccurrence a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:customerIdentifierTemplateParameter ;
    concept:sourcePath "find-customer.rq.template" .
ex:updateTemplateOccurrence a concept:ManifestationOccurrence ;
    concept:occurrenceOf ex:customerIdentifierTemplateParameter ;
    concept:sourcePath "update-customer.rq.template" .
```

Reuse a manifestation when the expression and its meaning are the same.
For template placeholders, the declared template language/profile must also
match; an identical token in another language is a separate manifestation.
Record separate appearances as `ManifestationOccurrence` resources, rather
than duplicating the manifestation for each statement. Identical variable
spellings with different meanings do not establish concept identity.

Here `$m` is intended as a template placeholder, so its type is
`TemplateParameterManifestation`. Native variables in SPARQL statements use
`SPARQLVariableManifestation`. Choose the type from the token's role and
language, rather than its spelling alone.

SPARQL accepts both `$m` and `?m` as the same native query variable, as specified
in [SPARQL variable syntax](https://www.w3.org/TR/sparql11-query/#QSynVariables).
An unexpanded template using `$m` can therefore parse as SPARQL while behaving
differently from the intended value substitution. The source must be treated
as a **statement template until processed**, even when it happens to parse.
A braced placeholder such as `${m}` is not native SPARQL variable syntax;
support for that spelling depends on the chosen template language.

[`tests/test_sparql_template_syntax.py`](../tests/test_sparql_template_syntax.py)
executes these distinctions with RDFLib: both native sigils work, an unbound
variable matches multiple values, an initial binding restricts the results,
and a braced placeholder fails SPARQL parsing.

The example is parsed and validated by
[`tests/test_story_concept_usages.py`](../tests/test_story_concept_usages.py)
and [`tests/test_statement_templates.py`](../tests/test_statement_templates.py).
The language profile and renderer illustrate metadata declarations. They do
not approve a particular engine for production use.

## Template processing contract

A **template processor**, also called a **template engine** or **renderer**,
turns a statement template and supplied story input values into a SPARQL
query or update. Template source and rendered SPARQL are different artifacts.
Template placeholders are resolved before the resulting statement is executed.

A Story Service supporting templates must:

1. Select an explicitly supported, documented template-language profile;
   reject unknown profiles and unsupported syntax. A dollar prefix does not
   identify a language or authorize shell expansion.
2. Validate the story input values and their RDF term kinds. For a value
   placeholder, serialize a complete RDF literal or IRI using an RDF-aware
   serializer, including the required quoting and escaping.
3. Render using strict substitution of those serialized values into permitted
   term positions. Reject unresolved placeholders and invalid bindings. Do
   not evaluate shell commands, arbitrary expressions, or user-supplied query
   fragments as input values.
4. Parse the generated query or update and reject invalid SPARQL before
   execution. Parsing checks syntax; typed substitution is still required
   because injected query fragments can themselves form valid SPARQL.

A general-purpose template language does not by itself provide RDF escaping.
For example, Python's documented
[`string.Template`](https://docs.python.org/3/library/string.html#template-strings)
performs dollar-placeholder substitution; it does not serialize RDF terms.
Its `safe_substitute` method can leave unresolved placeholders in the result,
so that behavior does not satisfy this contract.

The ontology stays engine-neutral while explicitly representing renderer
selection and language support. It does not provide a runtime renderer or
approve a particular language or engine. The application must enforce the
execution contract; OWL and SHACL validate the model metadata.

## Validation

From the repository root, validate a Turtle data file with RDFS inference:

```sh
pyshacl -s ekgf-story.ttl -e ekgf-story.ttl -i rdfs story-data.ttl
```

Include the referenced concept definitions in the data or in the supplied
ontology graph. This command does not fetch imports; the complete example
above explicitly types its concepts and works with the Story ontology alone.

To also validate template documents, language profiles, and renderers, load
the local Concept and SPARQL implementation shapes as well:

```python
from pyshacl import validate
from rdflib import Graph

schema = Graph()
for name in ("concept", "story", "story-impl-sparql"):
    schema.parse(f"ekgf-{name}.ttl", format="turtle")
data = Graph().parse("story-data.ttl", format="turtle")
conforms, _, report = validate(
    data, shacl_graph=schema, ont_graph=schema,
    inference="rdfs", do_owl_imports=False,
)
if not conforms:
    raise SystemExit(report)
```

Each of the three modules registers its named validators in its own
`ValidationShapeSet`. Template validation rejects missing or multiple
documents, renderers, or languages, missing source, unsupported renderer/language
combinations, and mixing template source with native SPARQL source.
The Concept `LegacyTemplateManifestationShape` rejects the retired
`LegraDollarManifestation` classification, even when current metadata is
also present.

`StoryConceptUsageShape` checks one owner, one referenced concept, resource
endpoints, and exactly one role. `StoryInputShape` checks input flags.
`LegacyConceptUsageShape` rejects retired vocabulary. These shapes, along with
the implementation ownership shapes, belong to the Story `ValidationShapeSet`.
Nested shapes are included through their registered entry definitions.

OWL expresses the ownership and concept cardinalities and can equate names
to satisfy them. SHACL checks actual resource terms and rejects missing or
multiple owners and concepts. Validate a deliberately selected, coherent
version context before running OWL identity reasoning; historical named graphs
are not automatically isolated from each other.

## Migration

This is a breaking change. Replace the previously loaded Story and Concept
ontology graphs so that obsolete ranges, classes, and the former domain on
`concept:hasConcept` are removed.

| Previous representation | Required migration |
| --- | --- |
| A story's `hasInputConcept`, `hasOutputConcept`, or `hasDependentConcept` points directly to a concept | Create a separate usage for each story and role. Point the story predicate to that usage and its `concept:hasConcept` to the existing concept. |
| `hasInput` or `hasOutput` points to a usage | Replace the predicate with `hasInputConcept` or `hasOutputConcept`, retaining the usage and its concept reference. |
| `MandatoryParameter` | Use `StoryInput` with `isMandatory true`. |
| `OptionalParameter` | Use `StoryInput` with `isMandatory false` or leave the flag absent. |
| `serverProvidedIRI` on a story | Identify the actual input usage and put `isServerProvided` there. Do not apply a story-level flag to arbitrary inputs. |
| `OptionalStoryOutput` | Resolve the intended output contract before removing this retired classification. Input flags do not encode output optionality. |
| `hasImplementation` | Use `implementedBy`, or `implementationOf` in the inverse direction. |
| Template text or a template file stored in native `sparql` / `fileName` fields | Use `StorySPARQLTemplateImplementation` with a linked `StatementTemplate`, its language profile, and a renderer declaring support for that profile. |
| `concept:LegraDollarManifestation` | Remove the retired type and use `concept:TemplateParameterManifestation` with its documented `concept:templateLanguage` profile. Preserve the manifestation's identity, token, concept links, and occurrence references. Adding the new type alongside the retired type still fails validation. |
| A template-placeholder manifestation without a language | Add its documented `concept:templateLanguage` profile. Matching token spellings alone cannot identify the template language. |

The ontology does not infer translations for ambiguous legacy data. Retired
classes and predicates cause validation errors, including when canonical
assertions are also present.

Concept vocabulary ownership and reuse follow the
[Method's Story/Concept Relationship](https://method.ekgf.org/concept/concept/story-concept-relationship/#ontology)
and [concept-vocabulary guidance](https://method.ekgf.org/concept/concept/concept-vocabulary/#ontology):
the story uses shared concepts, and its use case supplies access to its own
and ancestor vocabularies.
