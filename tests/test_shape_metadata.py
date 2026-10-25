"""Shapeset metadata validates itself and covers the repository's own shapes."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL


ROOT = Path(__file__).resolve().parents[1]
SH = Namespace("http://www.w3.org/ns/shacl#")
META = Namespace("https://ekgf.org/ontology/shape#")
EX = Namespace("https://example.test/")
REFERENCES = (SH.property, SH.node, SH["not"], SH.qualifiedValueShape)
LIST_REFERENCES = (SH["and"], SH["or"], SH.xone)


def nested_shapes(graph, roots):
    pending = list(roots)
    found = set()
    while pending:
        shape = pending.pop()
        if shape in found:
            continue
        found.add(shape)
        for predicate in REFERENCES:
            pending.extend(graph.objects(shape, predicate))
        for predicate in LIST_REFERENCES:
            for head in graph.objects(shape, predicate):
                pending.extend(graph.items(head))
    return found


def declared_shapes(graph):
    shapes = set(graph.subjects(RDF.type, SH.NodeShape))
    shapes.update(graph.subjects(RDF.type, SH.PropertyShape))
    shapes.update(graph.subjects(SH.path, None))
    for predicate in REFERENCES:
        shapes.update(graph.objects(None, predicate))
    for predicate in LIST_REFERENCES:
        for head in graph.objects(None, predicate):
            shapes.update(graph.items(head))
    return shapes


class ShapeMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-shape.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self):
        data = Graph()
        data.add((EX.shapeset, RDF.type, META.ShapeSet))
        data.add((EX.shapeset, RDFS.label, Literal("Example shapes", lang="en")))
        data.add((EX.purpose, RDF.type, META.ShapePurpose))
        data.add((EX.purpose, RDFS.label, Literal("Example validation", lang="en")))
        data.add((EX.shapeset, META.shapePurpose, EX.purpose))
        data.add((EX.shape, RDF.type, SH.NodeShape))
        data.add((EX.shapeset, META.hasShape, EX.shape))
        return data

    def test_ontology_title_describes_its_scope(self):
        self.assertEqual(
            set(self.ontology.objects(URIRef(str(META)), RDFS.label)),
            {Literal("SHACL Shape Metadata Ontology", lang="en")},
        )

    def test_membership_can_be_asserted_in_either_direction_or_both(self):
        for direction in ("set-to-shape", "shape-to-set", "both"):
            with self.subTest(direction=direction):
                data = self.fixture()
                if direction != "set-to-shape":
                    data.add((EX.shape, META.inShapeSet, EX.shapeset))
                if direction == "shape-to-set":
                    data.remove((EX.shapeset, META.hasShape, EX.shape))
                self.assert_valid(data)

    def test_shape_can_be_reused_in_several_sets(self):
        data = self.fixture()
        data.add((EX.otherSet, RDF.type, META.ShapeSet))
        data.add((EX.otherSet, RDFS.label, Literal("Other shapes", lang="en")))
        data.add((EX.otherSet, META.shapePurpose, EX.purpose))
        data.add((EX.otherSet, META.hasShape, EX.shape))
        self.assert_valid(data)

    def test_node_property_and_implicitly_typed_shapes_are_supported(self):
        for kind in ("node", "property", "implicit-property", "implicit-node"):
            with self.subTest(kind=kind):
                data = self.fixture()
                if kind != "node":
                    data.remove((EX.shape, RDF.type, None))
                if kind == "property":
                    data.add((EX.shape, RDF.type, SH.PropertyShape))
                if kind in ("property", "implicit-property"):
                    data.add((EX.shape, SH.path, EX.name))
                if kind == "implicit-node":
                    data.add((EX.shape, SH["class"], EX.Person))
                self.assert_valid(data)

    def test_inline_property_and_logical_shapes_are_covered_by_their_entry_shape(self):
        data = self.fixture()
        property_shape = BNode()
        data.add((EX.shape, SH.property, property_shape))
        data.add((property_shape, SH.path, EX.name))
        data.add((property_shape, SH.minCount, Literal(1)))
        head = BNode()
        empty_shape, typed_shape = BNode(), BNode()
        Collection(data, head, [empty_shape, typed_shape])
        data.add((EX.shape, SH["or"], head))
        data.add((typed_shape, SH["class"], EX.Person))
        self.assert_valid(data)

    def test_missing_membership_is_rejected_for_named_and_implicit_shapes(self):
        for orphan in ("named", "implicit-property", "implicit-node"):
            with self.subTest(orphan=orphan):
                data = self.fixture()
                if orphan == "named":
                    data.add((EX.orphan, RDF.type, SH.NodeShape))
                elif orphan == "implicit-property":
                    data.add((BNode(), SH.path, EX.name))
                else:
                    data.add((EX.orphan, SH["class"], EX.Person))
                self.assert_valid(data, False)

    def test_undefined_and_literal_members_are_rejected(self):
        for member in (EX.undefined, Literal("shape")):
            with self.subTest(member=member):
                data = self.fixture()
                data.add((EX.shapeset, META.hasShape, member))
                self.assert_valid(data, False)

    def test_missing_or_literal_shapeset_identity_is_rejected(self):
        data = self.fixture()
        data.remove((EX.shapeset, RDF.type, META.ShapeSet))
        self.assert_valid(data, False)
        data = self.fixture()
        data.add((EX.shape, META.inShapeSet, EX.undefinedSet))
        self.assert_valid(data, False)
        data = self.fixture()
        data.add((EX.shape, META.inShapeSet, Literal("set")))
        self.assert_valid(data, False)

    def test_empty_shapeset_is_rejected(self):
        data = self.fixture()
        data.add((EX.emptySet, RDF.type, META.ShapeSet))
        data.add((EX.emptySet, RDFS.label, Literal("Empty shapes", lang="en")))
        data.add((EX.emptySet, META.shapePurpose, EX.purpose))
        self.assert_valid(data, False)

    def test_missing_or_invalid_purpose_is_rejected(self):
        for purpose in (None, EX.undefinedPurpose, Literal("validation")):
            with self.subTest(purpose=purpose):
                data = self.fixture()
                data.remove((EX.shapeset, META.shapePurpose, None))
                if purpose is not None:
                    data.add((EX.shapeset, META.shapePurpose, purpose))
                self.assert_valid(data, False)

    def test_unlabelled_purpose_is_rejected(self):
        data = self.fixture()
        data.remove((EX.purpose, RDFS.label, None))
        self.assert_valid(data, False)

    def test_purposes_are_extensible_and_can_be_assigned_to_shapes(self):
        data = self.fixture()
        data.add((EX.otherPurpose, RDF.type, META.ShapePurpose))
        data.add((EX.otherPurpose, RDFS.label, Literal("Other purpose", lang="en")))
        data.add((EX.shape, META.shapePurpose, EX.otherPurpose))
        data.add((EX.shapeset, META.shapePurpose, EX.otherPurpose))
        self.assert_valid(data)

    def test_purpose_cannot_be_attached_to_an_undefined_shape(self):
        data = self.fixture()
        data.add((EX.undefined, META.shapePurpose, EX.purpose))
        self.assert_valid(data, False)

    def test_ordinary_rdf_resources_do_not_require_shapeset_membership(self):
        data = self.fixture()
        data.add((EX.person, RDF.type, EX.Person))
        data.add((EX.person, RDFS.label, Literal("Example person", lang="en")))
        self.assert_valid(data)

    def test_retired_node_only_membership_is_rejected(self):
        self.assertNotIn((META.hasNodeShape, RDF.type, OWL.AnnotationProperty),
                         self.ontology)
        data = self.fixture()
        data.add((EX.shapeset, META.hasNodeShape, EX.shape))
        self.assert_valid(data, False)

    def test_repository_registers_all_entry_shapes_and_covers_nested_shapes(self):
        files_with_shapes = 0
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path, format="turtle")
            shapes = declared_shapes(graph)
            if not shapes:
                continue
            files_with_shapes += 1
            with self.subTest(path=path.name):
                sets = set(graph.subjects(RDF.type, META.ShapeSet))
                self.assertEqual(len(sets), 1)
                shapeset, = sets
                roots = set(graph.objects(shapeset, META.hasShape))
                roots.update(graph.subjects(META.inShapeSet, shapeset))
                self.assertEqual(roots, {s for s in shapes if isinstance(s, URIRef)})
                self.assertTrue(shapes <= nested_shapes(graph, roots),
                                "An inline shape is outside the shapeset")
                self.assertEqual(set(graph.objects(shapeset, META.shapePurpose)),
                                 {META.Validation})
        self.assertGreaterEqual(files_with_shapes, 5)

    def test_metadata_ontology_validates_itself_and_all_repository_metadata(self):
        self.assertTrue(set(self.ontology.subjects(RDF.type, SH.NodeShape)))
        self.assert_valid(self.ontology)
        data = Graph()
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            data.parse(path, format="turtle")
        self.assert_valid(data)

    def test_metadata_validators_pass_standard_shacl_meta_validation(self):
        conforms, _, report = validate(
            self.ontology, shacl_graph=self.ontology, meta_shacl=True,
        )
        self.assertTrue(conforms, report)


if __name__ == "__main__":
    unittest.main()
