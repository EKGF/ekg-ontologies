# Families and artifact recognition

[Documentation index](../README.md#documentation)

The [artifact governance ontology](../ekgf-artifact-governance.ttl)
defines family membership and recognition rules. Registered families
and their recognition prefixes live in the
[family registry](../dataset/well-known-families.ttl).

## Optional membership

Families are optional. An authority can govern artifacts directly
through `ekg-artgov:governedBy`, without any family. When used, a family
spans artifact types: the ontologies, shapesets and taxonomies of
FIBO are members of the one FIBO family.

`ekg-artgov:inFamily` explicitly assigns membership on an artifact or
its `ekg-artgov:Reference`. Collect these assertions, including those on
known IRI aliases linked through references, before applying any
recognition rules. Multiple explicit memberships are permitted.

## Modules

Large families organise their artifacts into modules: FIBO has domains such as
FBC, SEC and FND, and some of those contain further modules.
`ekg-artgov:Module` represents one module. It belongs to exactly one family
through `ekg-artgov:inFamily`. An artifact, a reference or a nested module joins
it through `ekg-artgov:inModule`, with at most one direct module per member.
Query `inModule+` to find every enclosing module.

```turtle
@prefix artgov: <https://ekgf.org/ontology/artifact-governance#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <https://example.org/> .

ex:fibo a artgov:Family .
ex:fnd a artgov:Module ; rdfs:label "FND"@en ; artgov:inFamily ex:fibo .
ex:utilities a artgov:Module ; rdfs:label "Utilities"@en ;
    artgov:inFamily ex:fibo ; artgov:inModule ex:fnd .
ex:annotationVocabulary artgov:inModule ex:utilities .
```

Modules are stated, never derived from IRI path segments, file names or
directories, because module boundaries do not reliably follow them. A harvester
that knows a family's conventions can generate these statements. A family
without modules declares none. Whether a viewer shows the module level is a
presentation choice.

`ModuleShape` and `ModuleMembershipShape` check that each module has a label and
exactly one family, that nesting is acyclic, that a member has at most one
direct module, and that a member declaring families includes its module's
family.

Inside a family, an ontology's name often repeats the family name, as in
"Commons Identifiers Ontology". `ekg-annotation:shortTitle` gives the shorter
name a viewer can show under the family heading, such as "Identifiers
Ontology", with at most one short title per language.

## Recognition

For artifacts without explicit membership, these optional recognition
methods are available. A family can have several prefixes per method.
The properties below use the `ekg-artgov:` namespace.

| Property             | Matches                                |
| -------------------- | -------------------------------------- |
| `namespaceIriPrefix` | Start of the supplied artifact IRI     |
| `filePathPrefix`     | Start of any actual source path segment |
| `graphIriPrefix`     | Start of the complete named-graph IRI   |

For example, a namespace prefix can be
`https://spec.edmcouncil.org/fibo/ontology/`, a file path prefix can
be `fibo/` or `ekgf-`, and a graph IRI prefix can be
`s3://standards/fibo/`.

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
a recognized result as `ekg-artgov:inFamily`.

## Reference matcher

Install the [validation dependencies](../README.md#validation), then
run the matcher from the repository root:

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

## Migrating file path rules

The former relative `graphIriPrefix` values `ekgf-` and `cdmc-` have
moved to `filePathPrefix`. Consumers must read that property and
supply the actual file path. `graphIriPrefix` now accepts only absolute
IRI prefixes typed `xsd:anyURI`; relative values are rejected.
