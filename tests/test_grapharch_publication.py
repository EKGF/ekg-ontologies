"""Publication settings reuse the canonical registry without redefining it."""
import pathlib
import unittest

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, RDFS

ROOT = pathlib.Path(__file__).resolve().parents[1]
GA = Namespace("https://ekgf.org/ontology/grapharch#")
ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
ARTPUB = Namespace("https://ekgf.org/ontology/artifact-publication#")
DOC = Namespace("urn:ekgf-ontologies:documentation:")
FAMILY = URIRef("urn:uuid:c0eda36a-f42a-4fa3-aea9-c7a5543207eb")
AUTHORITY = URIRef("urn:uuid:6c1408aa-039c-42f9-8dee-9c3f0009d61a")


class GraphArchPublicationTests(unittest.TestCase):
    def test_publication_uses_the_registered_family_name(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        registry = Graph().parse(ROOT / "dataset/well-known-families.ttl")
        names = [str(value) for value in registry.objects(FAMILY, RDFS.label)
                 if value.language == "en"]
        self.assertEqual(names, ["EKGF Ontologies"])
        for subject in (DOC.project, DOC.specification):
            self.assertEqual([str(value) for value in settings.objects(subject, DCTERMS.title)], names)

    def test_profile_and_publisher_resolve_to_existing_registry_entities(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        registry = Graph()
        for filename in ("well-known-authorities.ttl", "well-known-families.ttl",
                         "ekgf-family-references.ttl"):
            registry.parse(ROOT / "dataset" / filename)
        self.assertIn((DOC.profile, ARTPUB.publishesFamily, FAMILY), settings)
        self.assertIn((FAMILY, RDF.type, ARTGOV.Family), registry)
        self.assertIn((DOC.specification, GA.publisher, AUTHORITY), settings)
        self.assertIn((AUTHORITY, RDF.type, ARTGOV.Authority), registry)
        self.assertNotIn((FAMILY, RDF.type, ARTGOV.Family), settings)
        self.assertNotIn((AUTHORITY, RDF.type, ARTGOV.Authority), settings)
        self.assertTrue(list(registry.subjects(ARTGOV.inFamily, FAMILY)))

    def test_publication_project_is_separate_from_ontology_identities(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        self.assertIn((DOC.project, RDF.type, GA.Project), settings)
        ontologies = {subject for path in ROOT.glob("ekgf-*.ttl")
                      for subject in Graph().parse(path).subjects(
                          RDF.type, URIRef("http://www.w3.org/2002/07/owl#Ontology"))}
        self.assertTrue(ontologies)
        self.assertFalse(set(settings.subjects(RDF.type, GA.Project)) & ontologies)
