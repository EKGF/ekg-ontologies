"""Family recognition by artifact IRI, source path and named-graph IRI."""

import unittest

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import XSD

from scripts.recognize_family import RecognitionError, recognize_family
from test_governance_registry import ARTGOV, EX, reason, turtle


EKGF = URIRef("urn:uuid:c0eda36a-f42a-4fa3-aea9-c7a5543207eb")
CDMC = URIRef("urn:uuid:cc08d976-d892-43aa-ac8f-5fcb3ddff634")


def registry():
    data = Graph()
    data.add((EX.general, RDF.type, ARTGOV.Family))
    data.add((EX.specific, RDF.type, ARTGOV.Family))
    data.add((EX.general, ARTGOV.namespaceIriPrefix,
              Literal("https://example.test/ontology/", datatype=XSD.anyURI)))
    data.add((EX.specific, ARTGOV.namespaceIriPrefix,
              Literal("https://example.test/ontology/specific/", datatype=XSD.anyURI)))
    data.add((EX.general, ARTGOV.filePathPrefix, Literal("models/")))
    data.add((EX.specific, ARTGOV.filePathPrefix, Literal("models/specific/")))
    return data


class FamilyRecognitionTests(unittest.TestCase):
    def test_namespace_prefix_uses_the_longest_match(self):
        result = recognize_family(registry(), "https://example.test/ontology/specific/Test")
        self.assertEqual(result.families, (EX.specific,))
        self.assertEqual(result.basis, "recognized")

    def test_path_matching_is_independent_of_artifact_and_graph_iris(self):
        for source in ("/checkout/models/specific/test.ttl",
                       "models/specific/test.ttl",
                       r"C:\checkout\models\specific\test.ttl"):
            with self.subTest(source=source):
                result = recognize_family(registry(), "urn:ontology:test",
                                          source_path=source, graph_iri="urn:graph:opaque")
                self.assertEqual(result.families, (EX.specific,))

    def test_directory_and_filename_prefixes_work_at_segment_boundaries(self):
        data = registry()
        data.add((EX.specific, ARTGOV.filePathPrefix, Literal("ekgf-")))
        for source, expected in (
            ("/work/ekgf-story.ttl", (EX.specific,)),
            ("/work/not-ekgf-story.ttl", ()),
            ("/work/not-models/test.ttl", ()),
            ("/work/models-extra/test.ttl", ()),
        ):
            with self.subTest(source=source):
                self.assertEqual(recognize_family(data, "urn:test", source_path=source).families,
                                 expected)

    def test_named_graph_iri_prefix_is_a_separate_method(self):
        data = registry()
        data.add((EX.specific, ARTGOV.graphIriPrefix,
                  Literal("s3://standards/specific/", datatype=XSD.anyURI)))
        result = recognize_family(data, "urn:test", graph_iri="s3://standards/specific/file.ttl")
        self.assertEqual(result.families, (EX.specific,))

    def test_matching_methods_can_agree(self):
        result = recognize_family(registry(), "https://example.test/ontology/specific/Test",
                                  source_path="/work/models/specific/test.ttl")
        self.assertEqual(result.families, (EX.specific,))

    def test_prefix_lengths_are_not_compared_between_methods(self):
        with self.assertRaisesRegex(RecognitionError, "Conflicting"):
            recognize_family(registry(), "https://example.test/ontology/specific/Test",
                             source_path="/work/models/general.ttl")

    def test_equal_best_prefixes_for_different_families_are_an_error(self):
        data = registry()
        data.add((EX.general, ARTGOV.filePathPrefix, Literal("models/specific/")))
        with self.assertRaisesRegex(RecognitionError, "Ambiguous"):
            recognize_family(data, "urn:test", source_path="models/specific/test.ttl")

    def test_multiple_equal_matches_for_one_family_are_not_ambiguous(self):
        data = registry()
        data.add((EX.general, ARTGOV.filePathPrefix, Literal("vendor/")))
        result = recognize_family(data, "urn:test", source_path="vendor/models/test.ttl")
        self.assertEqual(result.families, (EX.general,))

    def test_explicit_memberships_override_conflicting_recognition(self):
        data = registry()
        artifact = URIRef("https://example.test/ontology/specific/Test")
        data.add((artifact, ARTGOV.inFamily, EX.general))
        data.add((EX.reference, ARTGOV.refersTo, artifact))
        data.add((EX.reference, ARTGOV.inFamily, EX.specific))
        result = recognize_family(data, str(artifact), source_path="models/general.ttl")
        self.assertEqual(set(result.families), {EX.general, EX.specific})
        self.assertEqual(result.basis, "explicit")

    def test_membership_on_a_reference_or_alias_is_used(self):
        for subject in (EX.reference, EX.alias):
            with self.subTest(subject=subject):
                data = registry()
                data.add((EX.reference, ARTGOV.refersTo, EX.artifact))
                data.add((EX.reference, ARTGOV.refersTo, EX.alias))
                data.add((subject, ARTGOV.inFamily, EX.general))
                result = recognize_family(data, str(EX.artifact),
                                          source_path="models/specific/test.ttl")
                self.assertEqual(result.families, (EX.general,))
                self.assertEqual(result.basis, "explicit")

    def test_unmatched_artifacts_stay_without_a_family(self):
        result = recognize_family(registry(), "urn:unrelated", source_path="other/test.ttl")
        self.assertEqual(result.families, ())
        self.assertEqual(result.basis, "unmatched")

    def test_recognition_does_not_write_membership_or_change_the_registry(self):
        data = registry()
        before = set(data)
        recognize_family(data, "urn:test", source_path="models/test.ttl")
        self.assertEqual(set(data), before)
        self.assertFalse(list(data.triples((None, ARTGOV.inFamily, None))))

    def test_invalid_prefixes_are_rejected_even_with_explicit_membership(self):
        for predicate, value in (
            (ARTGOV.namespaceIriPrefix, Literal("relative/", datatype=XSD.anyURI)),
            (ARTGOV.namespaceIriPrefix, Literal("https://example.test/")),
            (ARTGOV.graphIriPrefix, Literal("ekgf-")),
            (ARTGOV.filePathPrefix, Literal("")),
            (ARTGOV.filePathPrefix, Literal("../models/")),
            (ARTGOV.filePathPrefix, Literal("/absolute/")),
            (ARTGOV.filePathPrefix, Literal("models//")),
            (ARTGOV.filePathPrefix, Literal("https://host/models/")),
            (ARTGOV.filePathPrefix, Literal(r"models\specific")),
        ):
            with self.subTest(predicate=predicate, value=value):
                data = registry()
                data.add((EX.general, predicate, value))
                data.add((EX.artifact, ARTGOV.inFamily, EX.general))
                with self.assertRaises(RecognitionError):
                    recognize_family(data, str(EX.artifact))

    def test_unregistered_family_is_an_error(self):
        data = registry()
        data.add((EX.artifact, ARTGOV.inFamily, EX.missing))
        with self.assertRaisesRegex(RecognitionError, "Unregistered family"):
            recognize_family(data, str(EX.artifact))

    def test_source_uri_is_not_silently_treated_as_a_file_path(self):
        with self.assertRaises(RecognitionError):
            recognize_family(registry(), "urn:test",
                             source_path="https://models/specific/test.ttl")

    def test_paths_are_normalized_but_empty_and_parent_paths_are_errors(self):
        result = recognize_family(registry(), "urn:test", source_path="./models//specific/test.ttl")
        self.assertEqual(result.families, (EX.specific,))
        for source in ("", "/", ".", "models/../other/test.ttl"):
            with self.subTest(source=source):
                with self.assertRaises(RecognitionError):
                    recognize_family(registry(), "urn:test", source_path=source)

    def test_recognition_can_change_while_an_explicit_assignment_persists(self):
        data = registry()
        first = recognize_family(data, str(EX.artifact), source_path="models/test.ttl")
        moved = recognize_family(data, str(EX.artifact), source_path="other/test.ttl")
        self.assertEqual(first.families, (EX.general,))
        self.assertEqual(moved.families, ())
        data.add((EX.artifact, ARTGOV.inFamily, EX.general))
        assigned = recognize_family(data, str(EX.artifact), source_path="other/test.ttl")
        self.assertEqual(assigned.families, (EX.general,))
        self.assertEqual(assigned.basis, "explicit")

    def test_registered_filename_rules_use_the_file_path_property(self):
        data = turtle("dataset/well-known-families.ttl")
        self.assertIn((EKGF, ARTGOV.filePathPrefix, Literal("ekgf-")), data)
        self.assertIn((CDMC, ARTGOV.filePathPrefix, Literal("cdmc-")), data)
        for source, family in (("/work/ekgf-story.ttl", EKGF), ("/work/cdmc-model.ttl", CDMC)):
            self.assertEqual(recognize_family(data, "urn:opaque", source_path=source).families,
                             (family,))

    def test_path_rules_classify_families_without_making_membership_assertions(self):
        data = Graph()
        data.add((EX.family, ARTGOV.filePathPrefix, Literal("models/")))
        inferred = reason(data)
        self.assertIn((EX.family, RDF.type, ARTGOV.Family), inferred)
        self.assertFalse(list(inferred.triples((None, ARTGOV.inFamily, None))))


if __name__ == "__main__":
    unittest.main()
