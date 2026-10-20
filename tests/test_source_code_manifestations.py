"""Source-code identifiers and their system-specific occurrences."""

import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Literal, RDF, RDFS
from rdflib.namespace import OWL

from test_data_element_concepts import CONCEPT
from test_governance_registry import ERROR, EX, turtle


class SourceCodeManifestationTests(unittest.TestCase):
    def setUp(self):
        self.graph = turtle("ekgf-concept.ttl")

    def expand(self):
        DeductiveClosure(OWLRL_Semantics).expand(self.graph)
        self.assertFalse(list(self.graph.objects(None, ERROR)))

    def test_language_identifiers_inherit_the_common_source_code_type(self):
        for kind in (CONCEPT.JavaScriptIdentifierManifestation,
                     CONCEPT.PythonIdentifierManifestation,
                     CONCEPT.JavaIdentifierManifestation):
            self.assertIn((kind, RDF.type, OWL.Class), self.graph)
            self.assertIn((kind, RDFS.subClassOf,
                           CONCEPT.SourceCodeIdentifierManifestation), self.graph)
            self.graph.add((EX[str(kind).split("#")[-1]], RDF.type, kind))
        self.expand()
        for kind in (CONCEPT.JavaScriptIdentifierManifestation,
                     CONCEPT.PythonIdentifierManifestation,
                     CONCEPT.JavaIdentifierManifestation):
            identifier = EX[str(kind).split("#")[-1]]
            for parent in (CONCEPT.SourceCodeIdentifierManifestation,
                           CONCEPT.TechnicalManifestation,
                           CONCEPT.ConceptManifestation):
                self.assertIn((identifier, RDF.type, parent), self.graph)

    def test_unlisted_language_can_use_the_common_class_directly(self):
        self.graph.add((EX.identifier, RDF.type,
                        CONCEPT.SourceCodeIdentifierManifestation))
        self.graph.add((EX.identifier, CONCEPT.manifestationValue,
                        Literal("customer_id")))
        self.expand()
        self.assertIn((EX.identifier, RDF.type,
                       CONCEPT.TechnicalManifestation), self.graph)
        self.assertNotIn((EX.identifier, RDF.type,
                          CONCEPT.PythonIdentifierManifestation), self.graph)
        self.assertNotIn((CONCEPT.CypherIdentifierManifestation, RDFS.subClassOf,
                          CONCEPT.SourceCodeIdentifierManifestation), self.graph)

    def test_occurrences_record_distinct_systems_without_a_repository(self):
        self.assertIn((CONCEPT.sourceSystem, RDF.type, OWL.ObjectProperty), self.graph)
        self.assertIn((CONCEPT.sourceSystem, RDFS.domain,
                       CONCEPT.ManifestationOccurrence), self.graph)
        self.assertIn((CONCEPT.sourceSystem, RDFS.range, RDFS.Resource), self.graph)
        for occurrence, system in ((EX.firstOccurrence, EX.legacySystem),
                                   (EX.secondOccurrence, EX.reportingSystem)):
            self.graph.add((occurrence, CONCEPT.occurrenceOf, EX.identifier))
            self.graph.add((occurrence, CONCEPT.sourceSystem, system))
        self.expand()
        for occurrence in (EX.firstOccurrence, EX.secondOccurrence):
            self.assertIn((occurrence, RDF.type,
                           CONCEPT.ManifestationOccurrence), self.graph)
            self.assertFalse(list(self.graph.objects(occurrence,
                                                     CONCEPT.sourceRepository)))
        self.assertNotIn((EX.legacySystem, OWL.sameAs, EX.reportingSystem), self.graph)
        self.assertNotIn((EX.identifier, CONCEPT.sourceSystem, EX.legacySystem),
                         self.graph)


if __name__ == "__main__":
    unittest.main()
