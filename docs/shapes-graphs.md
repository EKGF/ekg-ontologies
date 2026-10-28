# Shape collections and validation graphs

[Documentation index](../README.md#documentation)

The [SHACL Shape Metadata Ontology](../ekgf-shape.ttl) distinguishes a
`shape:ShapeSet`, which records collection membership and purpose, from the
concrete RDF graph supplied to a validator. `shape:hasShapesGraph` links them.
The ontology carries the model, examples, and validation limits in English
`annotation:markdownDescription` annotations as well.

## The relationship

| Resource | Role |
| --- | --- |
| `shape:ShapeSet` | Identifies a collection of entry shapes and their nested definitions. |
| `sh:ShapesGraph` | Identifies an actual RDF graph used as shapes input for validation. |
| `shape:hasShapesGraph` | Records an explicit connection from a set to a concrete shapes graph. |

The set and graph use different IRIs. Their classes are disjoint. A set may
reference zero or more graphs, and the same graph may serve multiple sets.
Neither functionality nor inverse functionality is asserted, so sharing a graph
does not merge sets, and multiple graph links do not merge graph identities.

For each validation run, explicitly select and resolve the intended graph.
The graph must supply the required definitions and dependencies. It can include
additional shapes or sets; collection membership does not restrict the targets
a SHACL engine evaluates. Do not assume that linked graphs are interchangeable,
combine their contents automatically, or choose an arbitrary first reference.

`hasShapesGraph` is distinct from SHACL's `sh:shapesGraph`, which suggests shapes
graphs for validating a data graph. The new relationship does not generate that
property or assert data conformance. It also does not fetch resources, follow
imports, copy shapes, or execute a validator.

## Complete example

Save this as `person-shapes.ttl`. Its graph IRI is
`https://example.test/personShapesGraph`; its collection has a different IRI.

```turtle
@prefix shape: <https://ekgf.org/ontology/shape#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <https://example.test/> .

ex:personShapeSet a shape:ShapeSet ;
    rdfs:label "Person validation set"@en ;
    shape:shapePurpose shape:Validation ;
    shape:hasShape ex:PersonShape ;
    shape:hasShapesGraph ex:personShapesGraph .

ex:personShapesGraph a sh:ShapesGraph .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path ex:name ; sh:minCount 1 ; sh:datatype xsd:string
    ] .
```

Validate the metadata with the local schema, without fetching imports:

```sh
pyshacl -s ekgf-shape.ttl -e ekgf-shape.ttl person-shapes.ttl
```

Then load the actual shapes input explicitly. This example expects collection
metadata to be included in the supplied file, as shown above:

```python
from pyshacl import validate
from rdflib import Graph, Namespace

shape = Namespace("https://ekgf.org/ontology/shape#")
ex = Namespace("https://example.test/")
schema = Graph().parse("ekgf-shape.ttl", format="turtle")
selected_graph = ex.personShapesGraph
concrete = Graph(identifier=selected_graph).parse(
    "person-shapes.ttl", format="turtle",
)
if (ex.personShapeSet, shape.hasShapesGraph, selected_graph) not in concrete:
    raise SystemExit("The selected graph is not linked from the expected set")
conforms, _, report = validate(
    concrete, shacl_graph=schema, ont_graph=schema, do_owl_imports=False,
)
if not conforms:
    raise SystemExit(report)

data = Graph().parse("people.ttl", format="turtle")
conforms, _, report = validate(
    data, shacl_graph=concrete, do_owl_imports=False,
)
if not conforms:
    raise SystemExit(report)
```

An unreadable or malformed file raises an error. It is not replaced with an
empty graph. In a store-backed application, resolve the selected graph IRI to
the intended stored graph and reject unavailable or incomplete inputs. Metadata
assertions alone are not evidence that those contents exist or were used.

`tests/test_shapes_graph_links.py` loads the example as its identified graph,
checks its metadata, rejects a Person without a name, and accepts the same
record after the required name is supplied.

## Validation and repository use

`ShapesGraphLinkShape` requires a ShapeSet subject and ShapesGraph IRI objects,
keeping the collection and graph roles separate. `ShapeSetShape` checks the
subject's existing label, purpose, and member-definition requirements even when
it is found only through a graph link. Both shapes belong to the metadata
ontology's own `ValidationShapeSet`.

The command above uses no entailment, so supply endpoint types explicitly.
RDFS or OWL reasoning can infer endpoint classes from the property's domain and
range. Neither explicit nor inferred typing proves graph availability or
contents. Metadata validation does not dereference graph IRIs, compare named
graph contents with a collection, check import closure, or validate application
data. The application must supply complete graph inputs to the execution step.

Every validation set in this repository links to its module's ontology IRI;
the module declares that IRI's ShapesGraph role. For example, the collection
`https://ekgf.org/ontology/story#ValidationShapeSet` links to the graph
`https://ekgf.org/ontology/story#`, supplied by `ekgf-story.ttl`. The tests load
each local module under its identified graph IRI and verify that its registered
entry definitions are present. No identity is derived from a filename or label.

Existing unlinked collections remain valid. To add a graph reference, retain
the collection's identity and select a separate graph IRI. A resource used for
both collection and graph must be split into separately identified resources
before this metadata validates.

## Standards scope and use-case independence

`sh:ShapesGraph` is referenced from the
[SHACL 1.2 Core Working Draft of 25 October 2026](https://www.w3.org/TR/2026/WD-shacl12-core-20261025/).
It is an external graph-role term, not an EKGF-owned class. The metadata
constraints use SHACL Core features supported by the repository's pinned
validator; using the term does not claim full implementation of that draft.

The use-case tree prescribes no inheritance of profiles, graph links,
constraints, or conformance. Child use cases may choose stricter, looser, or
different requirements. Parentage and reuse produce no positional warnings or
automatic profiling relationships. Any future inheritance policy requires a
separate explicit decision.

Profile ownership and composition, conformance-evidence processing, and
SHACL-based Story implementations are separate modeling work. This relationship
does not introduce or implement those features.
