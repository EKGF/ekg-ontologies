# Documentation coverage and modeling review

[Documentation index](../README.md#documentation)

The October 2026 documentation pass covers the 24 root ontology files.
All 704 locally defined, named, explicitly typed resources now have an English
label, a definition, and `rdfs:isDefinedBy` pointing to their source ontology.
This includes classes, properties, named individuals, datatypes, and named SHACL
shapes. Each ontology header also has a name, a description, and the repository's
CC0 license link.

The pass adds 135 labels, 288 definitions, 665 defining-ontology links, and 24
ontology license links. It corrects the unused Outcome Dublin Core namespace
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
story-usage model, with its pending implementation stated explicitly.

The test detects missing documentation. It does not certify business accuracy,
completeness of examples, a publishable standards release, or a sound OWL model.
During this pass, the before/after RDF graphs were compared with documentation
annotations excluded: structural assertions remained isomorphic in all 24 files.
No domains, ranges, imports, restrictions, class relationships, SHACL constraints,
or registered identities were changed.

## Recorded story-usage decision

The agreed replacement uses `StoryInput`, `StoryOutput`, and
`StoryDependent` as subclasses of `StoryConceptUsage`. Specific story
predicates range over those usage objects and specialize `hasConceptUsage`,
so the reasoner can infer the usage types. Each usage has one owning story and
references one shared data element concept. A Story Service interprets absent
`isMandatory` and `isServerProvided` flags as false. Missing flags remain
valid; SHACL default annotations do not populate the graph.

The [Story Ontology's Markdown description](../ekgf-story.ttl) records the
decision and required migration. The source axioms still mix usage-object and
direct-concept links. Implementing the agreed classes, predicates, flags, and
shapes is a semantic change that remains pending.

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

Add executable examples for story concept usages and implementation bindings, authorization-rule
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
