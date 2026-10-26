# Documentation coverage and modeling review

[Documentation index](../README.md#documentation)

The initial October 2026 documentation pass covered the 24 root ontology files.
At that point, all 704 locally defined, named, explicitly typed resources had an
English label, a definition, and `rdfs:isDefinedBy` pointing to their source
ontology. These included classes, properties, named individuals, datatypes, and
named SHACL shapes. Each ontology header also received a name, a description,
and the repository's CC0 license link. Coverage checks continue to apply as the
model evolves.

That pass added 135 labels, 288 definitions, 665 defining-ontology links, and 24
ontology license links. It corrected the unused Outcome Dublin Core namespace
binding and the User Experience prototype default prefix/base, with regression
checks. It corrects capability class labels that contained the
names of example individuals and replaces an internal story-service question
with a description of the declared relationship. Existing terse descriptions
are clarified where the intended scope is supported by the surrounding model.

External vocabulary declarations are excluded from local coverage: repeating
`dc:creator` or a class from another ontology does not make this file the owner
of that term. Namespace ownership comes from the ontology's SHACL declarations,
including the maturity model's distinct ontology IRI and namespace.

## What the coverage test establishes

`tests/test_documentation_coverage.py` checks English labels and definitions,
local ownership links, ontology headers, and the corrected class/individual
labels. It also checks that the maturity-model descriptions mention the actual
domain members of the affected properties.

English `annotation:markdownDescription` literals also count as definitions,
including when a resource has no plain-text definition. A regression check
exercises that case. Markdown explanations in the Story, Story Service,
Concept, and Use Case ontologies record ownership, reuse, and the agreed
story-usage model. The initial pending implementation has since been completed
as described below.

The test detects missing documentation. It does not certify business accuracy,
completeness of examples, a publishable standards release, or a sound OWL model.
During that initial pass, the before/after RDF graphs were compared with documentation
annotations excluded: structural assertions remained isomorphic in all 24 files.
No domains, ranges, imports, restrictions, class relationships, SHACL constraints,
or registered identities were changed by the documentation pass. Subsequent
semantic changes are recorded separately below.

## Story implementation ownership

The [Story Ontology](../ekgf-story.ttl) now uses `implementedBy` and its inverse
`implementationOf` as its canonical implementation relationship.
`implementationOf` is functional, and `StoryImplementation` has an OWL
exactly-one-owner restriction. A story can have zero or more implementations;
each implementation belongs to exactly one story.

`StoryImplementationShape` rejects missing or multiple owners, counting both
relationship directions without requiring OWL inverse inference. Predicate
targets also cover untyped endpoints and implementation metadata. RDFS
inference with the ontology graph provides endpoint types and subclass
relationships. `LegacyImplementationShape` rejects the removed
`hasImplementation` predicate; stored assertions must migrate to the
canonical relationship.

Validate a coherent version context. Named graphs may hold historical
snapshots, but their contents must be selected explicitly for validation.
Repeated owner assertions for the same story identity count once. Graphs that
link one implementation IRI to different story-version IRIs cannot be combined
into a valid single ownership view.

`tests/test_story_implementations.py` covers inverse inference, multiple
implementations per story, missing and conflicting owners, subclass coverage,
invalid endpoints, retired links, and separate versus combined snapshots.

## SHACL shape metadata and shapesets

The former Shape Ontology is now titled **SHACL Shape Metadata Ontology**.
Its ontology IRI, namespace, preferred prefix, and registered artifact identity
are retained. `ShapeSet` supports both node and property shapes through
`hasShape` and `inShapeSet`. The node-only `hasNodeShape` predicate is
retired and rejected by validation.

The ontology includes validators for membership endpoints, labeled and typed
purpose values, nonempty shapesets, and complete coverage of supplied shape
definitions. Every shape must be a registered entry or reachable from one
through SHACL shape-reference properties and logical lists. Membership can be
asserted in either direction. Shapes can be reused across several sets;
membership does not imply exclusive ownership.

Each shape-bearing ontology declares a `ValidationShapeSet` and lists all its
named entry shapes. The nested property shapes and logical branches are
included through those definitions. The metadata ontology does this for its
own validators as well. All sets use the defined `Validation` purpose
individual; additional purpose individuals can be supplied.

`tests/test_shape_metadata.py` validates the combined sources, independently
checks entry and nested-shape coverage, and exercises invalid memberships and
purpose annotations. The metadata validators also pass standard SHACL
meta-validation. The [ontology's Markdown description](../ekgf-shape.ttl)
documents the validation command and migration.

## Communication endpoint validation

`EmailRecipientShape` requires at least one `EmailEndpoint` through
`hasEndpoint`. It uses a qualified minimum count so that a recipient can also
have SMS, voice, or other channel endpoints. The previous class constraint
incorrectly required every endpoint of an email recipient to be an email
endpoint. All endpoints remain subject to the general channel and address
constraints in `CommunicationEndpointShape`.

`tests/test_communication_endpoints.py` covers email and SMS endpoints on the
same recipient, multiple email endpoints, missing email endpoints, endpoint
subclasses, recipient-specific endpoint links, invalid additional endpoints,
and standard SHACL meta-validation.

## Communication target validation

`MembershipShape` requires a `membershipRecipient`, a `membershipEndpoint`,
or both. `CommunicationAttemptShape` similarly requires an `attemptRecipient`,
an `attemptEndpoint`, or both. Each shape uses `sh:or` to reject records that
identify no target. The existing target type checks and maximum of one value
per link remain in force, along with the required collection or program.

`tests/test_communication_targets.py` covers missing targets, subclass
validation, recipient-only and endpoint-only records, both links together,
multiple targets of the same kind, and literal targets. Unlinked recipients
and endpoints elsewhere in the graph do not satisfy a record's requirement.

## Story concept-usage model

The implemented model uses `StoryInput`, `StoryOutput`, and
`StoryDependent` as subclasses of `StoryConceptUsage`. Specific story
predicates range over those usage objects and specialize `hasConceptUsage`,
so the reasoner can infer the usage types. Each usage has one owning story and
references one shared data element concept. A Story Service interprets absent
`isMandatory` and `isServerProvided` flags as false. Missing flags remain
valid; SHACL default annotations do not populate the graph.

The [Story Ontology](../ekgf-story.ttl) declares these classes and predicates,
OWL ownership and concept cardinalities, disjoint usage roles, and boolean
input flags. SHACL enforces one owner, one concept, one role, and valid flags.
Its validators belong to the Story `ValidationShapeSet`. The former global
domain on `concept:hasConcept` is removed: story-specific constraints apply
to usage objects without narrowing the general Concept property.

Retired `hasInput`, `hasOutput`, `serverProvidedIRI`, `MandatoryParameter`,
`OptionalParameter`, and `OptionalStoryOutput` declarations are removed and
their use is rejected by validation. Direct concept links must migrate to
story-owned usage objects. The [usage guide](story-concept-usages.md) provides
an executable example and migration instructions, including legacy records
whose input or output contract needs an explicit decision.

`tests/test_story_concept_usages.py` checks range and subproperty inference,
usage/concept separation, shared-concept reuse, OWL identity consequences,
ownership and concept cardinalities, role distinctions, boolean defaults and
invalid flags, input-role inference from flags, distinct usages of one concept,
retired vocabulary, general Concept-property behavior, and the complete
documentation example with a shared template-placeholder manifestation. Tests first
reproduced the missing axioms and constraints before the migration was
implemented.

## Statement templates and renderers

The SPARQL Story Implementation Ontology distinguishes template source from
the generated SPARQL statement. `StorySPARQLTemplateImplementation` links
one `StatementTemplate` and one `TemplateRenderer`. Documents identify their
source language through `concept:templateLanguage`; renderers explicitly
declare matching `supportsTemplateLanguage` capabilities. Template text and
file references are stored on the template document, while native SPARQL
source fields are rejected on template-based implementations.

The Concept Ontology declares `TemplateLanguage` and requires each
`TemplateParameterManifestation` to identify a documented language and exact
token. The shared language property has no global domain, so labeling a
document does not classify it as a placeholder manifestation. These validators
belong to each ontology's own `ValidationShapeSet`.
The Concept `LegacyTemplateManifestationShape` explicitly rejects the retired
`LegraDollarManifestation` type, including instances that also carry the current
type and language metadata. Removing a class declaration alone does not reject
its instances under open-world semantics.

`tests/test_statement_templates.py` covers type inference, source requirements,
language and renderer cardinalities, renderer compatibility, source separation,
template-placeholder metadata and migration, standard SHACL meta-validation,
the complete documentation example, and RDF literal substitution with query-like input.
The runtime renderer and its approval policy remain service implementation
responsibilities; these ontologies declare and validate their metadata.

## Decisions needed before changing axioms

| Area | Evidence in the current sources | Opportunity |
| --- | --- | --- |
| Story-service result keys | `story-service:resultKey` has domain `Parameter`, while `resultType` has domain `Result`. | Decide whether the key describes a parameter, a result, or both; add examples and tests before changing its domain. |
| Parameter operations and directions | `parameterOp` has no datatype range; `parameterDirection` and `parameterType` are unconstrained strings. | Document the consumer vocabulary, then decide whether these are strings, RDF resources, or controlled values. |
| Parameter generation | `shouldBeGeneratedBy` links `Parameter` to `StoryService`; the previous comment only questioned its purpose. | Confirm its distinction from the statement/service and story/service relationships, or remove it through an explicit model change. |
| Capability structure | `SubCapability` is not declared a subclass of `Capability`; `CapabilityDomain` has no membership property. | Define the intended hierarchy and domain membership. The documentation deliberately does not invent those axioms. |
| Two capability vocabularies | Capability and maturity-model ontologies both define `Capability` with separate IRIs. | Decide whether they represent the same concept, related concepts, or intentionally separate assessment and operational models. |
| Maturity assessment criteria | The example model declares five numbered levels but no assessment criteria or named maturity stages. | Supply actual criteria and evidence requirements before presenting the example as a complete assessment standard. |
| Maturity membership | `inModel` is transitive and has a union domain of capability, capability area, level, and pillar. | Explain intended inference across `inArea`, `inPillar`, and model membership; transitivity alone does not provide cross-property inference. |
| Source occurrence positions | `concept:sourceLine` and `sourceColumn` are integers without an indexing convention. | Choose and document zero-based or one-based positions, with examples. |
| SPARQL flavors | SPARQL flavors are classes, while `flavor` is an object property ranging over `SPARQLFlavor`. | Document whether implementations reference flavor instances or use class IRIs with OWL punning. |
| Empty distinctness assertion | The SPARQL implementation ontology contains `owl:AllDifferent` with an empty member list. | Remove the ineffective axiom or populate an intentional list in a separate model change. |
| Communication classification | Legal categories and basis values record classifications; consent records can reference bases other than consent. | Keep classification evidence separate from the policy that decides eligibility, and review whether the consent class name accurately covers its intended scope. |

## Local import closure

The following sources refer to local ontology terms without declaring the
corresponding local import:

- `ekgf-dataops.ttl`: dataset.
- `ekgf-specification-by-example.ttl`: dataset and story.
- `ekgf-use-case.ttl`: concept.

Cross-ontology references are legal RDF and do not automatically require imports.
Decide whether each file is intended to work as a standalone OWL import closure
or only within a family dataset before adding dependencies. The documentation
pass leaves the import graph unchanged.

## Further documentation work

Add executable examples for implementation bindings, authorization-rule
interpretation, capability organization, and maturity assessment. Existing names
or broad superclass declarations do not provide enough evidence to invent those
application policies.

Continue reviewing existing definitions for depth: a nonempty annotation is a
minimum coverage requirement. Add application examples, lifecycle diagrams, and
cross-ontology navigation as part of the generated family reference.

SPARQL query-form descriptions link to the
[W3C query specification](https://www.w3.org/TR/sparql11-query/#QueryForms), and
update descriptions link to the
[W3C update specification](https://www.w3.org/TR/sparql11-update/#graphManagement).
The product and vendor entries document the identities already present in this
ontology; they do not assert current product availability, ownership, or support.
