# Outcome relationships

[Documentation index](../README.md#documentation)

The [Outcome Ontology](../ekgf-outcome.ttl) models an
`outcome:OutcomeRelationship` as an identified contribution from one Use Case
to one shared Outcome. The source is the Method's
[Outcome Relationship](https://method.ekgf.org/concept/outcome/outcome-relationship/#ontology)
and its endpoint cardinalities. The relationship and its endpoints have
separate identities.

## Model

| Resource or property | Meaning |
| --- | --- |
| `outcome:OutcomeRelationship` | One independently identified contribution. |
| `outcome:useCase` | Exactly one source Use Case. |
| `use-case:outcomeLink` | Inverse navigation from the source Use Case to its relationships. |
| `outcome:targetOutcome` | Exactly one shared Outcome. |
| `outcome:contributionDescription` | Optional nonblank plain or language-tagged text describing this contribution. |
| `use-case:hasOutcome` | An unqualified outcome summary derived by OWL from the relationship path. |

Use a stable UUID URN for each relationship. Generate a fresh random UUIDv4
when creating a contribution record, and retain it when names or descriptions
change. The validation profile requires the `urn:uuid:` prefix and hyphenated
UUID syntax. It does not constrain the UUID version or prove random generation
or global uniqueness. Namespace IRIs, names and endpoint pairs are not
relationship identifiers.

Several relationships can have the same source, the same target, or both.
No inverse-functional endpoint or pair-based key merges their identities.
Applications must explicitly decide whether two records describe the same
contribution. A relationship cannot itself be a Use Case or an Outcome.

## Example

These use cases explicitly contribute to the same outcome, describing different
parts of the work. Parentage does not create the child's relationship.

Save this complete example as `outcome-data.ttl`:

```turtle
@prefix outcome: <https://ekgf.org/ontology/outcome#> .
@prefix use-case: <https://ekgf.org/ontology/use-case#> .
@prefix ex: <https://example.test/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:shorterHandlingTime a outcome:Outcome ;
    rdfs:label "Shorter case handling time"@en ;
    rdfs:comment "Reduce elapsed time from case intake to a completed review."@en .

ex:caseReview a use-case:UseCase ;
    rdfs:label "Case review"@en ;
    use-case:outcomeLink <urn:uuid:fa48a552-6f45-4f01-872e-0146622295d6> .

<urn:uuid:fa48a552-6f45-4f01-872e-0146622295d6>
    a outcome:OutcomeRelationship ;
    outcome:targetOutcome ex:shorterHandlingTime ;
    outcome:contributionDescription
        "Reduce the time reviewers spend assembling the information for a decision."@en .

ex:caseIntake a use-case:UseCase ;
    rdfs:label "Case intake"@en ;
    use-case:isPartOf ex:caseReview .

<urn:uuid:4fabf150-e1e0-4414-91a7-11b31f92d3ad>
    a outcome:OutcomeRelationship ;
    outcome:useCase ex:caseIntake ;
    outcome:targetOutcome ex:shorterHandlingTime ;
    outcome:contributionDescription
        "Collect the required information at intake to reduce later clarification."@en .
```

The example deliberately uses opposite source directions. Both identify one
source per relationship. Asserting both directions for the same source is also
valid and counts once. Multiple contribution descriptions are allowed,
including translations. An absent description is valid; every supplied value
must be nonblank text.

## Query contributions

This query counts either source direction without relying on materialized
inverse or summary triples:

```sparql
PREFIX outcome: <https://ekgf.org/ontology/outcome#>
PREFIX use-case: <https://ekgf.org/ontology/use-case#>

SELECT DISTINCT ?useCase ?relationship ?outcome ?contribution WHERE {
    ?relationship (outcome:useCase|^use-case:outcomeLink) ?useCase ;
        outcome:targetOutcome ?outcome .
    OPTIONAL {
        ?relationship outcome:contributionDescription ?contribution .
    }
}
```

The example returns two contribution records targeting one outcome. `DISTINCT`
prevents duplicate rows from repeating a source in both directions; translations
can produce additional rows.

With both ontology modules loaded, OWL infers inverse links and the summary
`use-case:hasOutcome` through the property chain
`use-case:outcomeLink / outcome:targetOutcome`. RDFS inference alone does not
execute that chain. A direct summary assertion supplies no relationship identity
or contribution metadata and does not create a relationship object.
The general `outcome:hasOutcome` and `story:contributesTo` properties also retain
their direct-outcome meanings; neither is interpreted as a relationship object.

## Validate before identity reasoning

Install the [test dependencies](../README.md#validation) and run from the
repository root:

```sh
pyshacl -s ekgf-outcome.ttl -f human outcome-data.ttl
```

This command uses explicit endpoint types, as supplied in the example.
For application data without explicit endpoint types, combine the local
`ekgf-outcome.ttl` and `ekgf-use-case.ttl` ontology graphs and supply that graph
to the validator with RDFS inference. The Outcome module references the Use
Case class; it does not import the Use Case module, which already imports
Outcome. No network import loading is required.

`OutcomeRelationshipShape` validates instances and subclasses, subjects of
relationship properties, and objects of `use-case:outcomeLink`. Missing explicit
relationship types therefore cannot hide incomplete contribution records.
It checks UUID URNs, both source directions, one target, IRI endpoints, endpoint
classes, separation of relationship and endpoint roles, and supplied text.

The validator and its nested shapes belong to the Outcome
`ValidationShapeSet`, whose `shape:hasShapesGraph` points to the Outcome module's
separate ShapesGraph IRI. See [shape collections and graphs](shapes-graphs.md)
for graph selection and loading responsibilities.

OWL exact cardinality and functional endpoints express the model. They do not
report a missing supplied assertion as a data error, and can equate different
endpoint names. Run SHACL before OWL identity reasoning to detect multiple
supplied endpoint terms. Validate a coherent version context: the same
relationship IRI in two separate snapshots can validate individually while their
merged graph fails if they name different endpoint versions. Named graphs do
not automatically isolate snapshots once their triples are combined.

## Ownership, reuse and remaining decisions

Contribution does not establish outcome ownership. The Method describes local
and ancestor outcomes, but it does not give a property that distinguishes
ownership from contribution. Neither `outcomeLink` nor the derived `hasOutcome`
assigns an owner. The existing general-purpose `use-case:usedIn` is not inferred
from a contribution.

Child and reused use cases can explicitly reference the same Outcome as another
use case. `isPartOf` and `isUsedIn` imply no inherited relationships,
descriptions, ownership or scoring. There is no requirement that a contribution
target an ancestor's outcome; contributions can cross the use-case tree.

Existing `outcome:priority` applies to the Outcome itself. It must not be used
for relationship priority: its domain would classify the relationship as an
Outcome, conflicting with role separation. Confidence scores, contribution
priority and explicit outcome ownership need separately agreed definitions.
This change adds no scoring scales, ownership properties or defaults.

The Method asks complete Use Cases to have outcomes. This validator focuses on
the relationship records; it does not impose a global minimum relationship
count on every Use Case in a partial dataset or validate complete Use Case
documentation. It also cannot establish that the contribution is accurate or
that the target outcome has been achieved.

`tests/test_outcome_relationships.py` validates and queries this example and
checks endpoint inference and cardinality, identity, shared outcomes, optional
multilingual text, snapshot contexts, summary inference, and independence from
hierarchy and ownership.
