# Publication, releases and approvals

[Documentation index](../README.md#documentation)

The [artifact publication ontology](../ekgf-artifact-publication.ttl)
describes publication profiles, targets, runs, releases and approvals.
It uses [authorities and references](governance.md) from artifact
governance and supports publication with or without
[families](families.md).

## Publication scope

A family is an enduring grouping that can serve as a publication
unit. Each version is a separate `ekg-artpub:StandardsRelease`, and
approval applies to that exact release. Publication also works
without families, by selecting one or more `ekg-artgov:Reference`
resources representing the artifacts being published. The properties
below use the `ekg-artpub:` namespace.

| Scope      | Profile              | Release            |
| ---------- | -------------------- | ------------------ |
| One family | `publishesFamily`    | `releaseFamily`    |
| References | `publishesReference` | `releaseReference` |

Choose one scope form per profile or release. Selecting references
does not create a family or assign family membership. References
identify source artifacts; `ekg-artpub:publicationArtifact` identifies
generated outputs such as RDF downloads and PDFs.

## Releases and versions

Each release has its own identity and one `ekg-artpub:releaseVersion`.
Its scope, version and content provenance are immutable: changed
content requires a new release identity. Retain the configuration
of any profile linked to a release; changed configuration needs a
new profile identity. A version label can recur in another family's
or artifact's publication history, so it is not an identity key.
External releases can be recorded without a local publication run
or input commit. If a run is linked, its profile must select the
same scope and its input commit must match the release's commit.

## Approvals

An `ekg-artpub:ReleaseApproval` records one authority's affirmative
decision about one release, with `ekg-artpub:approvesRelease`,
`ekg-artpub:approvedBy` and `ekg-artpub:approvedAt`. Several authorities
can approve the same release through separate records. For example,
this standalone ontology needs no family:

```turtle
@prefix ex: <https://example.org/> .
@prefix ekg-artgov: <https://ekgf.org/ontology/artifact-governance#> .
@prefix ekg-artpub: <https://ekgf.org/ontology/artifact-publication#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:authority a ekg-artgov:Authority .
ex:reference a ekg-artgov:Reference ;
    ekg-artgov:refersTo ex:ontology ;
    ekg-artgov:governedBy ex:authority .
ex:release a ekg-artpub:StandardsRelease ;
    ekg-artpub:releaseReference ex:reference ;
    ekg-artpub:releaseVersion "1.0" .
ex:approval a ekg-artpub:ReleaseApproval ;
    ekg-artpub:approvesRelease ex:release ;
    ekg-artpub:approvedBy ex:authority ;
    ekg-artpub:approvedAt "2026-10-01T09:00:00Z"^^xsd:dateTime .
```

Approval does not transfer to later releases or future family
members. A governing or publishing role does not prove approval,
and approval does not itself publish a release. Lifecycle state
can change independently, including to superseded or withdrawn.
Required approvers and withdrawal procedures belong to governance
policy. Supporting approval evidence can use `rdfs:seeAlso`.

## Validation

Install the [validation dependencies](../README.md#validation) and run
commands from the repository root.

The [publication ontology](../ekgf-artifact-publication.ttl) includes
SHACL shapes for profiles, releases and approvals. Validate publication
records before accepting them, including the referenced authority,
family or reference types in the data graph:

```sh
pyshacl -s ekgf-artifact-publication.ttl -f human publication-data.ttl
```

Validation rejects missing or conflicting scopes, missing versions,
incomplete approvals and inconsistent profile or run provenance.
The validator exits nonzero on failure. Consumers must also enforce
immutability when storing updates; validation of a single graph
cannot detect a change to a previously stored release.
