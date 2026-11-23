"""S3 object sources: location, object metadata, checksums, tags."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, XSD


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")

STRINGS = (
    "s3Bucket", "s3Key", "s3Region", "s3Endpoint", "s3VersionId", "s3ETag",
    "s3ContentType", "s3ContentEncoding", "s3ContentLanguage",
    "s3ContentDisposition", "s3CacheControl", "s3StorageClass",
    "s3ServerSideEncryption", "s3KmsKeyId", "s3ChecksumType",
    "s3ChecksumCrc32", "s3ChecksumCrc32c", "s3ChecksumCrc64Nvme",
    "s3ChecksumSha1", "s3ChecksumSha256", "s3ObjectLockMode",
    "s3ReplicationStatus", "s3Expiration",
)
BOOLEANS = ("s3BucketKeyEnabled", "s3ObjectLockLegalHold")


class RawS3ObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
            use_shapes=[RAW.S3ObjectShape, RAW.S3EntryShape],
        )
        self.assertEqual(conforms, expected, report)

    def obj(self, **props):
        data = Graph()
        data.add((EX.obj, RDF.type, RAW.S3Object))
        values = {
            "s3Bucket": Literal("dumps"),
            "s3Key": Literal("crm/2026-11-23/customers.csv"),
            "s3Region": Literal("eu-west-1"),
            "s3VersionId": Literal("3HL4kqtJlcpXroDTDmJ"),
            "s3ETag": Literal("9b2cf535f27731c974343645a3985328"),
            "s3StorageClass": Literal("STANDARD"),
            "s3ChecksumType": Literal("FULL_OBJECT"),
            "s3ChecksumSha256": Literal("MV9b23bQeMQ7isAGTkoBZGErH853yGk0W/yUx1iU7dM="),
            "s3PartsCount": Literal(3),
            "s3ObjectLockMode": Literal("GOVERNANCE"),
            "s3ObjectLockRetainUntil": Literal("2027-01-01T00:00:00Z", datatype=XSD.dateTime),
            "s3ObjectLockLegalHold": Literal(False),
            "s3BucketKeyEnabled": Literal(True),
        }
        values.update(props)
        for name, value in values.items():
            if value is not None:
                data.add((EX.obj, RAW[name], value))
        return data

    # -- vocabulary ---------------------------------------------------------

    def test_class_and_terms_are_declared_defined_and_owned(self):
        self.assertIn((RAW.S3Object, RDFS.subClassOf, RAW.Source), self.ontology)
        terms = STRINGS + BOOLEANS + ("s3PartsCount", "s3ObjectLockRetainUntil",
                                      "s3Tag", "s3UserMetadata", "s3EntryKey", "s3EntryValue")
        for name in terms:
            with self.subTest(term=name):
                self.assertIn((RAW[name], RDFS.isDefinedBy, RAW[""]), self.ontology)
                self.assertEqual(len(list(self.ontology.objects(RAW[name], RDFS.label))), 1)
                self.assertEqual(len(list(self.ontology.objects(RAW[name], RDFS.comment))), 1)
        for name in STRINGS + BOOLEANS + ("s3PartsCount", "s3ObjectLockRetainUntil"):
            with self.subTest(functional=name):
                self.assertIn((RAW[name], RDF.type, OWL.FunctionalProperty), self.ontology)
        for cls in (RAW.S3Tag, RAW.S3UserMetadataEntry):
            self.assertIn((cls, RDFS.subClassOf, RAW.S3Entry), self.ontology)

    def test_shapes_are_node_shapes(self):
        for shape in (RAW.S3ObjectShape, RAW.S3EntryShape):
            self.assertIn((shape, RDF.type, SH.NodeShape), self.ontology)

    # -- objects ------------------------------------------------------------

    def test_complete_object_is_valid(self):
        self.assert_valid(self.obj())

    def test_bucket_and_key_are_required(self):
        self.assert_valid(self.obj(s3Bucket=None), False)
        self.assert_valid(self.obj(s3Key=None), False)

    def test_everything_else_is_optional(self):
        minimal = {name: None for name in STRINGS + BOOLEANS + ("s3PartsCount", "s3ObjectLockRetainUntil")}
        minimal.update(s3Bucket=Literal("b"), s3Key=Literal("k"))
        self.assert_valid(self.obj(**minimal))

    def test_values_are_single_and_typed(self):
        data = self.obj()
        data.add((EX.obj, RAW.s3Key, Literal("other")))
        self.assert_valid(data, False)
        self.assert_valid(self.obj(s3PartsCount=Literal("3")), False)
        self.assert_valid(self.obj(s3PartsCount=Literal(0)), False)
        self.assert_valid(self.obj(s3ObjectLockLegalHold=Literal("false")), False)
        self.assert_valid(self.obj(s3ObjectLockRetainUntil=Literal("2027-01-01")), False)

    def test_etag_is_stored_without_quotes(self):
        self.assert_valid(self.obj(s3ETag=Literal('"9b2cf535"')), False)
        self.assert_valid(self.obj(s3ETag=Literal("9b2cf535f27731c974343645a3985328-3")))

    def test_enumerated_values(self):
        self.assert_valid(self.obj(s3ChecksumType=Literal("COMPOSITE")))
        self.assert_valid(self.obj(s3ChecksumType=Literal("full")), False)
        self.assert_valid(self.obj(s3ObjectLockMode=Literal("COMPLIANCE")))
        self.assert_valid(self.obj(s3ObjectLockMode=Literal("strict")), False)

    # -- tags and user metadata --------------------------------------------

    def entry(self, data, prop, cls, node, key, value):
        data.add((EX.obj, RAW[prop], node))
        data.add((node, RDF.type, cls))
        if key is not None:
            data.add((node, RAW.s3EntryKey, Literal(key)))
        if value is not None:
            data.add((node, RAW.s3EntryValue, Literal(value)))
        return data

    def test_tags_and_metadata_are_key_value_entries(self):
        data = self.obj()
        self.entry(data, "s3Tag", RAW.S3Tag, EX.tag, "classification", "internal")
        self.entry(data, "s3UserMetadata", RAW.S3UserMetadataEntry, EX.meta, "source-system", "crm")
        self.entry(data, "s3Tag", RAW.S3Tag, EX.empty, "flag", "")
        self.assert_valid(data)

    def test_entries_need_exactly_one_key_and_value(self):
        self.assert_valid(self.entry(self.obj(), "s3Tag", RAW.S3Tag, EX.tag, None, "v"), False)
        self.assert_valid(self.entry(self.obj(), "s3Tag", RAW.S3Tag, EX.tag, "k", None), False)
        data = self.entry(self.obj(), "s3Tag", RAW.S3Tag, EX.tag, "k", "v")
        data.add((EX.tag, RAW.s3EntryValue, Literal("w")))
        self.assert_valid(data, False)


if __name__ == "__main__":
    unittest.main()
