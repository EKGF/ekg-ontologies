# Ontology catalog and prefixes

[Documentation index](../README.md#documentation)

These ontologies describe Enterprise Knowledge Graphs, their use cases
and the artifacts used to build and govern them. Each catalog entry
links to its Turtle source and names its preferred prefix.

## Namespaces and prefixes

Each ontology lives in `ekgf-<name>.ttl`. Its ontology IRI and term
namespace are `https://ekgf.org/ontology/<name>#`, with one exception:
the maturity model has ontology IRI
`https://ekgf.org/ontology/ekgf-maturity-model` and term namespace
`https://ekgf.org/ontology/ekgf-maturity-model#`.

Preferred prefixes start with `ekg-`, reflecting their use in Enterprise
Knowledge Graphs. Source filenames retain `ekgf-`. A prefix is a local
abbreviation for a namespace; changing that abbreviation leaves the
term IRIs unchanged.

### SHACL declarations

Every ontology records its preferred mapping on the ontology resource
using `sh:declare`, with one `sh:prefix` string and one `sh:namespace`
literal typed `xsd:anyURI`. A matching named Turtle `@prefix` binding
appears in the same file. For example:

```turtle
@prefix ekg-artgov: <https://ekgf.org/ontology/artifact-governance#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ekg-artgov: a owl:Ontology ;
    sh:declare [
        sh:prefix "ekg-artgov" ;
        sh:namespace
            "https://ekgf.org/ontology/artifact-governance#"^^xsd:anyURI
    ] .
```

Consumers should read these declarations as the repository's preferred
prefix mappings. Turtle `@prefix` bindings alone are serialization
syntax and do not add declaration triples to the graph.

SHACL-SPARQL constraints can reuse the declarations through
`sh:prefixes` pointing to the ontology IRI. Load the relevant ontology
declarations into the shapes graph. For the maturity model, point to
the ontology IRI without `#`; its declared term namespace retains `#`.

## Method ontologies

- [Use case](../ekgf-use-case.ttl), `ekg-use-case`: the use case tree
  and the stereotype of each use case.
- [Story](../ekgf-story.ttl), `ekg-story`: stories, their inputs and
  outputs, and their implementations.
- [SPARQL story implementation](../ekgf-story-impl-sparql.ttl),
  `ekg-story-impl-sparql`: a story implemented as a SPARQL statement.
- [Story service](../ekgf-story-service.ttl), `ekg-story-service`:
  the service that turns stories into executable APIs.
- [Specification by example](../ekgf-specification-by-example.ttl),
  `ekg-sbe`: scenarios that say what a story must do, as given, when
  and then.
- [Concept](../ekgf-concept.ttl), `ekg-concept`: concepts and their
  manifestations, such as a business term, query variable or OWL class.
- [Persona](../ekgf-persona.ttl), `ekg-persona`: personas that play
  stories.
- [Outcome](../ekgf-outcome.ttl), `ekg-outcome`: outcomes that use cases
  and stories contribute to.
- [Capability](../ekgf-capability.ttl), `ekg-capability`: business
  capabilities.
- [DataOps](../ekgf-dataops.ttl), `ekg-dataops`: pipelines and load
  requests.
- [Maturity model](../ekgf-maturity-model.ttl), `ekg-mm`: EKG maturity.

## Artifact ontologies

- [Artifact governance](../ekgf-artifact-governance.ttl), `ekg-artgov`:
  who governs an ontology, shapeset, taxonomy or concept set, and its
  optional family membership. See [governance](governance.md) and
  [family recognition](families.md).
- [Artifact publication](../ekgf-artifact-publication.ttl), `ekg-artpub`:
  publication by family or individual artifact references, with
  profiles, targets, runs, releases and approvals. See
  [publication](publication.md).
- [Artifact dependency](../ekgf-artifact-dependency.ttl), `ekg-artdep`:
  what an artifact depends on, the evidence for it and whether the
  dependency resolves.
- [Shape](../ekgf-shape.ttl), `ekg-shape`: SHACL node shapes grouped
  into shapesets, and what a shape is for.
- [Lifecycle](../ekgf-lifecycle.ttl), `ekg-lifecycle`: lifecycles and
  the states their members occupy. See [lifecycles](lifecycles.md).

## General ontologies

- [Annotation](../ekgf-annotation.ttl), `ekg-annotation`: a description
  in Markdown, a subtitle and a summary.
- [API](../ekgf-api.ttl), `ekg-api`: the slug by which a resource is
  addressed in a URL.
- [Authorization](../ekgf-authorization.ttl), `ekg-authorization`:
  role-based access control for personas.
- [Communication](../ekgf-communication.ttl), `ekg-communication`:
  recipients, audiences, consent and delivery.
- [Dataset](../ekgf-dataset.ttl), `ekg-dataset`: datasets and the files
  they include.
- [File system](../ekgf-file-system.ttl), `ekg-file-system`: files,
  directories, versions and links.
- [Raw](../ekgf-raw.ttl), `ekg-raw`: data captured from a source before
  it is mapped to other ontologies.
- [User experience](../ekgf-user-experience.ttl), `ekg-ux`: hints for
  user interfaces, such as colors and sort keys.

## Data products

The Data Product Ontology (DPROD) is maintained separately in
[EKGF/dprod](https://github.com/EKGF/dprod), with namespace
`https://www.omg.org/spec/DPROD/dprod/` and prefix `dprod`. Load it from
that repository when using data product terms.
