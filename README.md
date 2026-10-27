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

- [Ontology reference](https://ekgf.github.io/ekg-ontologies/spec/develop/):
  the generated editor's draft, with a PDF download and documentation graph.
- [Generate the HTML and PDF ontology reference](docs/generated-reference.md):
  build the family directly from this checkout with GraphArch.

- [Documentation coverage and modeling review](docs/documentation-audit.md):
  annotation coverage, corrected labels, and model decisions requiring review.
- [Ontology catalog and prefixes](docs/ontologies.md): all ontologies,
  their preferred prefixes, namespace conventions and SHACL
  declarations.
- [Data element concepts](docs/concepts.md): reusable meanings,
  business and technical manifestations, compound constructs and the
  relationship to ISO/IEC 11179.
- [Story concept usages](docs/story-concept-usages.md): typed input, output,
  and dependent usages, ownership, input defaults, validation and migration.
- [Raw data capture](docs/raw-data.md): captured literals, original source text,
  explicit source nulls, physical source locations, validation and migration.
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
git diff --check
```

The [tests](tests/) check registered identities, references, Commons
role semantics, namespace declarations, family recognition and
publication constraints, including publication without families.
They also check documentation coverage for locally defined named terms and
ontology headers, data element concept inference, manifestation
separation, class disjointness, lifecycle bindings, and exactly one owning
story per implementation, including validation of versioned snapshots.
Story-usage checks cover role inference, one owner and concept per usage,
shared meanings, input flags and defaults, and rejection of retired vocabulary.
Template checks cover source languages, renderer support, separation of
template documents from native SPARQL, and RDF-aware value substitution.
Raw-data checks cover literal content, source text, explicit nulls, physical
columns, row/column view consistency, and rejection of incomplete or conflicting
value occurrences and memberships.
They also validate shapeset membership, purpose annotations, and coverage of
all entry and nested shapes, including the shape-metadata validators themselves.
They run offline using the relevant Commons 1.3 axioms in a test
fixture. Its `.ttl.txt` suffix keeps it out of RDF file discovery
when consumers load this repository.

Use the [reference matcher](docs/families.md#reference-matcher) to
recognize a family from an artifact IRI, source path or graph IRI.
See [publication validation](docs/publication.md#validation) for the
command to check release and approval records with SHACL.

## GitHub Actions

The [Publish ontology reference](.github/workflows/grapharch-reference.yml)
workflow builds the HTML and PDF reference and a restorable documentation KG
when ontology, registry, documentation or publication sources change. Pull
requests build the reference for review; successful builds on `main` deploy it
to [GitHub Pages](https://ekgf.github.io/ekg-ontologies/spec/develop/). It can also
be started manually from the Actions tab.

The workflow installs a pinned, verified GraphArch binary and discovers the
publication settings in this repository. It requires no Rust build and does
not publish an ontology release or change its approval status. See the
[reference generation guide](docs/generated-reference.md) for details.

The publication build does not execute the complete ontology validation suite.
Run the checks in [Validation](#validation) locally before submitting changes.

## License

See [LICENSE](LICENSE).
