# ekg-ontologies

Ontologies and datasets for organising use cases in an Enterprise
Knowledge Graph (EKG), based on the
[EKG/Method](https://method.ekgf.org).

Everything here is RDF in Turtle. The ontologies are in the root of
the repository, the datasets are in `dataset/`.

## Ontologies

Every ontology lives in the file `ekgf-<name>.ttl` and has the IRI
`https://ekgf.org/ontology/<name>#`. The one exception is
`maturity-model`, whose IRI is
`https://ekgf.org/ontology/ekgf-maturity-model`.

### The method

- `use-case`: the use case tree and the stereotype of each use case
- `story`: stories, their inputs and outputs, and their
  implementations
- `story-impl-sparql`: a story implemented as a SPARQL statement
- `story-service`: the service that turns stories into executable
  APIs
- `specification-by-example`: scenarios that say what a story must
  do, as given, when and then
- `concept`: concepts and their manifestations, such as a business
  term, a query variable or an OWL class
- `persona`: the personas that play stories
- `outcome`: the outcomes that use cases and stories contribute to
- `capability`, `data-product`, `dataops`, `maturity-model`: business
  capabilities, data products, pipelines and load requests, and EKG
  maturity

### Artifacts and their governance

- `artifact-governance`: who governs an ontology, a shapeset, a
  taxonomy or a concept set, and which family it belongs to
- `artifact-publication`: how a family is published, in profiles,
  targets, runs and releases
- `artifact-dependency`: what an artifact depends on, the evidence
  for it and whether the dependency resolves
- `shape`: SHACL node shapes grouped into shapesets
- `lifecycle`: what a lifecycle is, which lifecycle a thing follows
  and which state it is in

### General

- `annotation`: a description in Markdown, a subtitle and a summary
- `api`: the slug by which a resource is addressed in a URL
- `authorization`: role-based access control for personas
- `communication`: recipients, audiences, consent and delivery
- `dataset`: datasets and the files they include
- `file-system`: files, directories, versions and links
- `raw`: data captured from any source as it is, before it is
  mapped to other ontologies
- `user-experience`: hints for user interfaces, such as colors and
  sort keys

## Datasets

- `well-known-authorities.ttl`: the bodies that govern artifacts,
  such as W3C, OMG and EKGF
- `well-known-families.ttl`: families of artifacts, such as FIBO
- `well-known-lifecycles.ttl`: lifecycles anyone can use
- `lifecycle-bindings.ttl`: which lifecycle the members of a class
  follow
- `ekg-family-references.ttl`: one reference for each ontology in
  this repository

### Authorities

The IRI of an authority is derived from its host. It is `urn:uuid:`
followed by the name-based UUID (version 5) of the host in the DNS
namespace. Two parties that describe the same host therefore mint
the same IRI.

```sh
python3 -c "import uuid; \
print(uuid.uuid5(uuid.NAMESPACE_DNS, 'www.w3.org'))"
```

### Families

A family spans artifact types: the ontologies, shapesets and
taxonomies of FIBO are members of the one FIBO family. A family
recognises its artifacts by two prefixes.

- `artgov:namespaceIriPrefix` is what the namespace IRIs of its
  artifacts start with. It is an absolute IRI.
- `artgov:graphIriPrefix` is what the named graphs of its source
  files start with. It is an absolute IRI such as
  `s3://standards/fibo/`, or a path prefix such as `fibo/` that
  holds wherever the files are stored.

When the prefixes of several families match, the longest one wins.

### Lifecycles

A lifecycle is a named sequence of states, optionally grouped into
phases. Each lifecycle has a namespace of its own,
`https://ekgf.org/lifecycle/<slug>#`, because lifecycles share state
names such as Draft and Deprecated.

- `continuous-improvement`: plan, build, run and evolve, in nine
  states from identified to decommissioned
- `achievement`: draft, active, achieved, deprecated
- `software-delivery`: development, test, user acceptance test,
  production
- `publication`: from working draft to published, and on to
  superseded or withdrawn
- `execution`: admitted, queued, running, then done, failed or
  cancelled

Which lifecycle a thing follows is decided in this order.

1. The lifecycle the thing names itself, with
   `lifecycle:followsLifecycle`.
2. The lifecycle that applies to a class of the thing, with
   `lifecycle:appliesTo`.

The bindings in `lifecycle-bindings.ttl` are defaults. They are
policy, so an organization that wants its stories, say, to follow a
lifecycle of its own replaces the binding in its own data.

```turtle
<my-story> lifecycle:hasState continuous-improvement:Deployed .
```

## License

See [LICENSE](LICENSE).
