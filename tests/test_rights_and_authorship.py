"""Ontologies record authorship and rights holders once, on their headers."""

from pathlib import Path
import unittest

from rdflib import Graph, Literal, Namespace, OWL, RDF, URIRef


ROOT = Path(__file__).resolve().parents[1]
DCT = Namespace("http://purl.org/dc/terms/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
CMNS_ORG = Namespace("https://www.omg.org/spec/Commons/Organizations/")
MIT = URIRef("https://opensource.org/licenses/MIT")
CMNS_AV = Namespace("https://www.omg.org/spec/Commons/AnnotationVocabulary/")
AUTHOR = URIRef("http://orcid.org/0000-0003-2309-5068")
EDM_ASSOCIATION = URIRef("urn:uuid:c2c98445-9dac-4515-bd06-ce6c5bdace11")
OMG = URIRef("urn:uuid:ec3f703d-55a9-4bea-a818-e71705f8dd2e")
EKGF_AUTHORITY = URIRef("urn:uuid:6c1408aa-039c-42f9-8dee-9c3f0009d61a")


class RightsAndAuthorshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = Graph()
        for name in ("well-known-organizations.ttl", "well-known-authorities.ttl"):
            cls.registry.parse(ROOT / "dataset" / name)
        cls.agnos, = [s for s, label in cls.registry.subject_objects(URIRef("http://www.w3.org/2000/01/rdf-schema#label"))
                      if str(label) == "agnos.ai U.K. Ltd"]
        cls.dataroad, = [s for s, label in cls.registry.subject_objects(URIRef("http://www.w3.org/2000/01/rdf-schema#label"))
                         if str(label) == "DataRoad Inc"]

    def test_every_ontology_header_names_its_creator_and_rights_holders(self):
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path)
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            with self.subTest(path=path.name):
                self.assertEqual(set(graph.objects(ontology, DCT.creator)), {AUTHOR})
                self.assertEqual(set(graph.objects(ontology, DCT.rightsHolder)),
                                 {self.agnos, EDM_ASSOCIATION, self.dataroad})
                self.assertEqual(set(graph.objects(ontology, DCT.license)), {MIT})
                self.assertEqual({str(v) for v in graph.objects(ontology, CMNS_AV.copyright)},
                                 {"Copyright (c) 2020-2026 agnos.ai U.K. Ltd",
                                  "Copyright (c) 2025-2026 EDM Association",
                                  "Copyright (c) 2024-2026 DataRoad Inc, Delaware USA, "
                                  "operating under the name Legra"})

    def test_terms_carry_no_individual_author_stamps(self):
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path)
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            with self.subTest(path=path.name):
                stamped = {s for s in graph.subjects(DC.creator, None) if s != ontology}
                self.assertEqual(stamped, set())

    def test_edm_association_is_the_legal_owner(self):
        self.assertIn((EDM_ASSOCIATION, RDF.type, CMNS_ORG.LegalEntity), self.registry)
        self.assertIn((OMG, CMNS_ORG.isSubUnitOf, EDM_ASSOCIATION), self.registry)
        self.assertNotIn((OMG, RDF.type, CMNS_ORG.LegalEntity), self.registry)
        self.assertEqual(set(self.registry.objects(EKGF_AUTHORITY, ARTGOV.legalOwner)),
                         {EDM_ASSOCIATION})
        self.assertIn((self.agnos, RDF.type, CMNS_ORG.LegalEntity), self.registry)


if __name__ == "__main__":
    unittest.main()
