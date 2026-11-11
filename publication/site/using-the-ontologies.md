---
title: Using the ontologies
nav_order: 2
permalink: /using-the-ontologies/
grapharch:
  subject: urn:ekgf-ontologies:website:using
---
# Using the ontologies

## Find a vocabulary

Use **Ontology family** in the navigation to select an ontology and inspect
its namespace, preferred prefix and terms. The
[ontology catalog](https://github.com/EKGF/ekg-ontologies/blob/main/docs/ontologies.md)
also maps each vocabulary to its Turtle source file.

The `ekgf-*.ttl` files at the repository root are the ontology sources.
Each ontology declares its namespace and preferred `ekg-` prefix with
SHACL `sh:declare`. Reuse those declarations when writing RDF or queries.

## Reuse registered identities

The [registry datasets](https://github.com/EKGF/ekg-ontologies/tree/main/dataset)
identify authorities, organizations, families and lifecycles. Reuse their
registered UUIDs. An authority role is distinct from the organization playing it.
Family membership is optional for artifacts in your own model.

## Validate your data

OWL axioms support inference. SHACL shapes check explicit data requirements;
their shape collections and validation graphs are documented in the reference.
The [repository validation instructions](https://github.com/EKGF/ekg-ontologies#validation)
explain how to run the offline test suite.

## Inspect the publication

The family reference and PDF edition each provide `documentation.nq`, a
restorable documentation graph with source and revision provenance. The home
site has its own [documentation graph](https://ekgf.github.io/ekg-ontologies/documentation.nq).
GraphArch reads this checkout directly and does not fetch ontology imports or
establish the semantic correctness of the model.
