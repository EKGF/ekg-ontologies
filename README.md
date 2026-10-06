# ekg-ontologies

Ontologies and datasets for organising use cases in an Enterprise
Knowledge Graph (EKG), based on the
[EKG/Method](https://method.ekgf.org).

The ontology and dataset sources are RDF in Turtle. The ontologies
are in the root of the repository, the datasets are in `dataset/`.
`scripts/` contains an executable reference matcher for family
recognition; `tests/` checks the vocabulary, registry and behavior.

## Ontologies

Every ontology lives in the file `ekgf-<name>.ttl` and has the IRI
`https://ekgf.org/ontology/<name>#`. The one exception is
`maturity-model`, whose IRI is
`https://ekgf.org/ontology/ekgf-maturity-model`.

Preferred prefixes start with `ekg-`, reflecting their use in Enterprise
Knowledge Graphs. Most use `ekg-<name>`, with these abbreviations:

| Ontology | Preferred prefix |
| --- | --- |
| Artifact governance | `ekg-artgov` |
| Artifact dependency | `ekg-artdep` |
| Artifact publication | `ekg-artpub` |
| Maturity model | `ekg-mm` |
| Specification by example | `ekg-sbe` |
| User experience | `ekg-ux` |

Each ontology records its mapping using `sh:declare`, with a `sh:prefix`
string and a `sh:namespace` literal typed `xsd:anyURI`. These SHACL
declarations are the source of preferred prefix mappings for consumers.
The mapping is attached to the ontology resource and agrees with a named
Turtle `@prefix` binding.
The maturity-model namespace includes the trailing `#`, even though
its ontology IRI does not. SHACL-SPARQL constraints can reuse these
declarations through `sh:prefixes` pointing to the ontology IRI.

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
- `capability`, `dataops`, `maturity-model`: business capabilities,
  pipelines and load requests, and EKG maturity

The Data Product Ontology (DPROD) is maintained separately in
[EKGF/dprod](https://github.com/EKGF/dprod), with the namespace
`https://www.omg.org/spec/DPROD/dprod/`.

### Artifacts and their governance

- `artifact-governance`: who governs an ontology, a shapeset, a
  taxonomy or a concept set, and which family it belongs to
- `artifact-publication`: publication by family or individual artifact
  references, with profiles, targets, runs, releases and approvals
- `artifact-dependency`: what an artifact depends on, the evidence
  for it and whether the dependency resolves
- `shape`: SHACL node shapes grouped into shapesets, and what a
  shape is for
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

- `well-known-authorities.ttl`: the authority roles that govern
  artifacts, such as those exercised by W3C, OMG and EKGF
- `well-known-organizations.ttl`: organizations that play authority
  roles or host their communities, with their own identities
- `well-known-families.ttl`: families of artifacts, such as FIBO
- `well-known-lifecycles.ttl`: lifecycles anyone can use
- `lifecycle-bindings.ttl`: which lifecycle the members of a class
  follow
- `ekgf-family-references.ttl`: one reference for each ontology in
  this repository

### Authorities and organizations

These Turtle datasets are the registry of authority and organization
identities. Each entry receives a random UUIDv4 URN once. Reuse the
registered IRI when referring to that authority or organization.
To mint an IRI for a new entry:

```sh
python3 -c "import uuid; print(uuid.uuid4().urn)"
```

Keep that IRI when a name, host or URL changes. Check the registry
before minting an entry; another name or domain may describe an
existing authority or organization. UUIDv4 supplies a random identity
without coupling it to a domain or creation time. The registry
establishes which entity the identifier denotes.

An `artgov:Authority` is a Commons `cmns-pts:PartyRole`. Its player
is linked with `cmns-rlcmp:isPlayedBy`. The organization playing the
role is a separate resource, described with Commons organization
types such as `cmns-org:LegalEntity` or
`cmns-org:OrganizationalSubUnit` where known. Commons makes agents
and roles disjoint. One organization can play several authority
roles, and a role can be recorded before its player is identified.

`artgov:communityOrganization` identifies the organization hosting
the community; `artgov:legalOwner` identifies the legal owner or
administrator. Neither relationship substitutes for `isPlayedBy`.

An authority may have multiple `artgov:authorityHost` and
`artgov:baseIri` values. Organizations may have multiple
`cmns-org:hasWebsite` values. These are editable metadata, not keys.
Retain historical hosts while their artifact IRIs remain in use.
A shared host, especially a namespace service such as PURL, does
not establish that all artifacts there have the same governing
authority.

The authority UUIDs replace the former host-derived UUIDs. Consumers
must load the registered identifiers and updated references instead
of computing identities from hosts.

### Organization categories

`artgov:organizationCategory` classifies the organization playing an
authority role or hosting its community. It specializes Commons
`cmns-cls:isClassifiedBy`. Its values are individuals of
`artgov:OrganizationCategory`, a subclass of `cmns-cls:Classifier`,
in the extensible `artgov:OrganizationCategoryScheme`.

The initial categories are standards body, consortium, project and
community. Several can apply to one organization: W3C and OMG are
classified as both standards bodies and consortia. SPDX and FOAF
are classified as projects, and EKGF as a community. The organization
records link to the supporting sources. An absent classification
means none has been asserted; categories are not inferred from a
name, host, legal type or parent organization.

An authority's organization categories can be read with this SPARQL
property path:

```sparql
?authority cmns-rlcmp:isPlayedBy/artgov:organizationCategory ?category .
```

Publishing responsibilities such as owner and publisher remain on
the authority through `artgov:publishingRole`. Roles such as editor
and reviewer remain `artgov:communityRole` values. Neither set of
role values can be used as organization categories. Legal entities
and organizational sub-units are still described with Commons
organization classes.

### Families

Families are optional. An authority can govern artifacts directly
through `artgov:governedBy`, without any family. When used, a family
spans artifact types: the ontologies, shapesets and taxonomies of
FIBO are members of the one FIBO family.

`artgov:inFamily` explicitly assigns membership on an artifact or
its `artgov:Reference`. Collect these assertions, including those on
known IRI aliases linked through references, before applying any
recognition rules. Multiple explicit memberships are permitted.

For artifacts without explicit membership, these optional recognition
methods are available. A family can have several prefixes per method.

| Property | Matches | Example |
| --- | --- | --- |
| `artgov:namespaceIriPrefix` | Beginning of the supplied artifact IRI | `https://spec.edmcouncil.org/fibo/ontology/` |
| `artgov:filePathPrefix` | Beginning of any segment of the actual source path | `fibo/` or `ekgf-` |
| `artgov:graphIriPrefix` | Beginning of the complete named-graph IRI | `s3://standards/fibo/` |

All matching is literal and case-sensitive. IRI prefixes are absolute
and typed `xsd:anyURI`. File path prefixes are nonempty relative
strings, using forward slashes without a scheme, drive, empty segment
or `.`/`..` segment. A trailing slash restricts a prefix to a directory:
`fibo/` matches `/work/fibo/model.ttl`, but not
`/work/fibo-extra/model.ttl`. `ekgf-` matches the filename
`/work/ekgf-story.ttl`, but not `/work/not-ekgf-story.ttl`.

Supply the actual source path independently of the graph name; an
opaque graph IRI need not encode a path. Source paths may be relative
or absolute, including Windows drive paths. Matching normalizes their
separators, `.` segments and repeated separators; callers must resolve
`..` segments first. Source URIs must be converted to paths by the
caller rather than treated as file paths.

Within each method, choose the longest matching prefix. Equal best
matches for different families are errors. Then require all methods
that matched to agree on the family. Their prefix lengths are not
comparable, so a long IRI does not override a conflicting short file
prefix. Explicit membership takes precedence over recognition; invalid
registry data or malformed inputs are still errors.

No assertion and no match means no family. Recognition is derived
metadata and can change when paths, IRIs or rules change. Keep its
provenance separate from asserted membership: do not silently persist
a recognized result as `artgov:inFamily`.

With the validation dependencies installed, run the reference matcher:

```sh
python3 -B scripts/recognize_family.py dataset/well-known-families.ttl \
  --artifact 'https://ekgf.org/ontology/story#' \
  --source-path './ekgf-story.ttl'
```

It returns JSON with `families` and `basis` (`explicit`, `recognized`
or `unmatched`). Conflicts and invalid inputs exit nonzero. Supply
additional Turtle files, such as `dataset/ekgf-family-references.ttl`,
to include asserted memberships. The matcher does not modify the
registry or fetch artifacts. Consumers can use it as a reference for
implementing the same contract in their loaders.

The former relative `graphIriPrefix` values `ekgf-` and `cdmc-` have
moved to `filePathPrefix`. Consumers must read that property and
supply the actual file path. `graphIriPrefix` now accepts only absolute
IRI prefixes typed `xsd:anyURI`; relative values are rejected.

### Publication, versions and approvals

A family is an enduring grouping that can serve as a publication
unit. Each version is a separate `artpub:StandardsRelease`, and
approval applies to that exact release. Publication also works
without families, by selecting one or more `artgov:Reference`
resources representing the artifacts being published.

| Scope | Publication profile | Standards release |
| --- | --- | --- |
| One family | `artpub:publishesFamily` | `artpub:releaseFamily` |
| Explicit artifact references | `artpub:publishesReference` | `artpub:releaseReference` |

Choose one scope form per profile or release. Selecting references
does not create a family or assign family membership. References
identify source artifacts; `artpub:publicationArtifact` identifies
generated outputs such as RDF downloads and PDFs.

Each release has its own identity and one `artpub:releaseVersion`.
Its scope, version and content provenance are immutable: changed
content requires a new release identity. Retain the configuration
of any profile linked to a release; changed configuration needs a
new profile identity. A version label can recur in another family's
or artifact's publication history, so it is not an identity key.
External releases can be recorded without a local publication run
or input commit. If a run is linked, its profile must select the
same scope and its input commit must match the release's commit.

An `artpub:ReleaseApproval` records one authority's affirmative
decision about one release, with `artpub:approvesRelease`,
`artpub:approvedBy` and `artpub:approvedAt`. Several authorities
can approve the same release through separate records. For example,
this standalone ontology needs no family:

```turtle
@prefix ex: <https://example.org/> .
@prefix artgov: <https://ekgf.org/ontology/artifact-governance#> .
@prefix artpub: <https://ekgf.org/ontology/artifact-publication#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:authority a artgov:Authority .
ex:reference a artgov:Reference ;
    artgov:refersTo ex:ontology ;
    artgov:governedBy ex:authority .
ex:release a artpub:StandardsRelease ;
    artpub:releaseReference ex:reference ;
    artpub:releaseVersion "1.0" .
ex:approval a artpub:ReleaseApproval ;
    artpub:approvesRelease ex:release ;
    artpub:approvedBy ex:authority ;
    artpub:approvedAt "2026-10-01T09:00:00Z"^^xsd:dateTime .
```

Approval does not transfer to later releases or future family
members. A governing or publishing role does not prove approval,
and approval does not itself publish a release. Lifecycle state
can change independently, including to superseded or withdrawn.
Required approvers and withdrawal procedures belong to governance
policy. Supporting approval evidence can use `rdfs:seeAlso`.

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

## Validation

Install the test dependencies in a virtual environment and run:

```sh
python3 -m pip install -r requirements-test.txt
python3 -B -m unittest discover -s tests -v
```

The tests check registered identities, references, Commons role
semantics, namespace declarations, family recognition and publication
constraints, including publication without families. They run offline
using the relevant Commons 1.3 axioms in a test fixture. Its `.ttl.txt`
suffix keeps it out of RDF file discovery when consumers load this
repository.

`ekgf-artifact-publication.ttl` includes SHACL shapes for profiles,
releases and approvals. Validate publication records before accepting
them, including the referenced authority, family or reference types
in the data graph:

```sh
pyshacl -s ekgf-artifact-publication.ttl -f human publication-data.ttl
```

Validation rejects missing or conflicting scopes, missing versions,
incomplete approvals and inconsistent profile or run provenance.
The validator exits nonzero on failure. Consumers must also enforce
immutability when storing updates; validation of a single graph
cannot detect a change to a previously stored release.

## License

See [LICENSE](LICENSE).
