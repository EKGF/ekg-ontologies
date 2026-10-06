# Authorities and organizations

[Documentation index](../README.md#documentation)

The [artifact governance ontology](../ekgf-artifact-governance.ttl)
defines authority roles and their relationships to organizations.
The [authority registry](../dataset/well-known-authorities.ttl) and
[organization registry](../dataset/well-known-organizations.ttl)
record their identities. [Families](families.md) provide optional
groupings of the artifacts these authorities govern.

## Registered identities

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

## Roles and their players

An `ekg-artgov:Authority` is a Commons `cmns-pts:PartyRole`. Its player
is linked with `cmns-rlcmp:isPlayedBy`. The organization playing the
role is a separate resource, described with Commons organization
types such as `cmns-org:LegalEntity` or
`cmns-org:OrganizationalSubUnit` where known. Commons makes agents
and roles disjoint. One organization can play several authority
roles, and a role can be recorded before its player is identified.

`ekg-artgov:communityOrganization` identifies the organization hosting
the community; `ekg-artgov:legalOwner` identifies the legal owner or
administrator. Neither relationship substitutes for `isPlayedBy`.

An authority may have multiple `ekg-artgov:authorityHost` and
`ekg-artgov:baseIri` values. Organizations may have multiple
`cmns-org:hasWebsite` values. These are editable metadata, not keys.
Retain historical hosts while their artifact IRIs remain in use.
A shared host, especially a namespace service such as PURL, does
not establish that all artifacts there have the same governing
authority.

The authority UUIDs replace the former host-derived UUIDs. Consumers
must load the registered identifiers and updated references instead
of computing identities from hosts.

## Artifact references

An `ekg-artgov:Reference` gives an artifact a stable registry identity
and slug, including when the artifact itself is not loaded. Its
`ekg-artgov:refersTo` values identify the artifact's known IRIs; several
values can represent aliases, such as IRIs with and without a trailing
hash. Assert aliases explicitly in the registry.

The [local artifact references](../dataset/ekgf-family-references.ttl)
cover the ontologies in this repository. References can carry
`ekg-artgov:governedBy` and optional `ekg-artgov:inFamily` assertions.
[Family recognition](families.md#optional-membership) collects explicit
memberships across references and their aliases;
[publication](publication.md#publication-scope) can select references
directly.

## Organization categories

`ekg-artgov:organizationCategory` classifies the organization playing an
authority role or hosting its community. It specializes Commons
`cmns-cls:isClassifiedBy`. Its values are individuals of
`ekg-artgov:OrganizationCategory`, a subclass of `cmns-cls:Classifier`,
in the extensible `ekg-artgov:OrganizationCategoryScheme`.

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
PREFIX cmns-rlcmp: <https://www.omg.org/spec/Commons/RolesAndCompositions/>
PREFIX ekg-artgov: <https://ekgf.org/ontology/artifact-governance#>

SELECT ?authority ?category WHERE {
    ?authority cmns-rlcmp:isPlayedBy/ekg-artgov:organizationCategory ?category .
}
```

Publishing responsibilities such as owner and publisher remain on
the authority through `ekg-artgov:publishingRole`. Roles such as editor
and reviewer remain `ekg-artgov:communityRole` values. Neither set of
role values can be used as organization categories. Legal entities
and organizational sub-units are still described with Commons
organization classes.
