# EKG ontologies

Ontologies and registry datasets for Enterprise Knowledge Graphs (EKGs),
maintained by the Enterprise Knowledge Graph Forum (EKGF).

The ontologies describe use cases and stories based on the
[EKG/Method](https://method.ekgf.org), the artifacts used to implement
an EKG, and their governance, publication and lifecycles.

## Using the ontologies

The ontology and dataset sources are RDF in Turtle. Ontologies live in
`ekgf-*.ttl` at the repository root; registry datasets live in
[`dataset/`](dataset/).

Start with the [ontology catalog](docs/ontologies.md) to find the
vocabulary and source file for your use case. Each ontology declares
its preferred `ekg-` prefix and namespace using SHACL `sh:declare`,
`sh:prefix` and `sh:namespace`. These mappings are available as RDF
for consumers to reuse.

Authorities and organizations have separate registered UUID identities
that persist through name and domain changes. Families are optional:
artifacts can be governed and published directly. Versions and
approvals belong to individual releases.

The Data Product Ontology is maintained in the separate
[EKGF/dprod](https://github.com/EKGF/dprod) repository.

## Documentation

- [Ontology catalog and prefixes](docs/ontologies.md): all ontologies,
  their preferred prefixes, namespace conventions and SHACL
  declarations.
- [Authorities and organizations](docs/governance.md): registered
  identities, Commons roles, organization categories and artifact
  references.
- [Families and artifact recognition](docs/families.md): optional
  membership, IRI and source path matching, conflict handling and the
  reference matcher.
- [Publication, releases and approvals](docs/publication.md): family
  or artifact scopes, versioned releases, approval records and SHACL
  validation.
- [Lifecycles and states](docs/lifecycles.md): reusable lifecycles,
  class defaults and explicit state assignments.

## Datasets

The Turtle files are the registry. Reuse existing entries when adding
references to an authority, organization, family or artifact.

- [Authorities](dataset/well-known-authorities.ttl): roles that govern
  artifacts, such as those exercised by W3C, OMG and EKGF.
- [Organizations](dataset/well-known-organizations.ttl): organizations
  that play authority roles or host their communities.
- [Families](dataset/well-known-families.ttl): optional groupings of
  artifacts, such as FIBO, and their recognition prefixes.
- [Lifecycles](dataset/well-known-lifecycles.ttl): reusable lifecycles,
  phases and states.
- [Lifecycle bindings](dataset/lifecycle-bindings.ttl): default
  lifecycle assignments for members of a class.
- [Local artifact references](dataset/ekgf-family-references.ttl):
  registered references to the ontologies in this repository.

## Validation

From the repository root, create a virtual environment outside the
repository, install the test dependencies and run the tests:

```sh
python3 -m venv ../ekg-ontologies-venv
source ../ekg-ontologies-venv/bin/activate
python3 -m pip install -r requirements-test.txt
python3 -B -m unittest discover -s tests -v
```

The [tests](tests/) check registered identities, references, Commons
role semantics, namespace declarations, family recognition and
publication constraints, including publication without families.
They run offline using the relevant Commons 1.3 axioms in a test
fixture. Its `.ttl.txt` suffix keeps it out of RDF file discovery
when consumers load this repository.

Use the [reference matcher](docs/families.md#reference-matcher) to
recognize a family from an artifact IRI, source path or graph IRI.
See [publication validation](docs/publication.md#validation) for the
command to check release and approval records with SHACL.

## License

See [LICENSE](LICENSE).
