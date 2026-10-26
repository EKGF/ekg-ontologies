"""Email recipients require an email endpoint and may use other channels too."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS


ROOT = Path(__file__).resolve().parents[1]
COMM = Namespace("https://ekgf.org/ontology/communication#")
EX = Namespace("https://example.test/")


class CommunicationEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-communication.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self):
        data = Graph()
        data.add((EX.recipient, RDF.type, COMM.EmailRecipient))
        return data

    def add_endpoint(self, data, node, kind, channel, address):
        data.add((EX.recipient, COMM.hasEndpoint, node))
        data.add((node, RDF.type, kind))
        data.add((node, COMM.endpointChannel, channel))
        data.add((node, COMM.endpointAddress, Literal(address)))

    def add_email_endpoint(self, data, node=EX.email):
        self.add_endpoint(data, node, COMM.EmailEndpoint, COMM.EmailChannel,
                          "recipient@example.test")

    def add_sms_endpoint(self, data):
        self.add_endpoint(data, EX.sms, COMM.SmsEndpoint, COMM.SmsChannel,
                          "+12025550123")

    def test_email_recipient_accepts_email_and_sms_endpoints(self):
        data = self.fixture()
        data.add((EX.recipient, RDF.type, COMM.SmsRecipient))
        self.add_email_endpoint(data)
        self.add_sms_endpoint(data)
        self.assert_valid(data)

    def test_email_recipient_accepts_one_or_several_email_endpoints(self):
        data = self.fixture()
        self.add_email_endpoint(data)
        self.assert_valid(data)
        self.add_email_endpoint(data, EX.otherEmail)
        self.assert_valid(data)

    def test_missing_email_endpoint_is_rejected(self):
        for endpoint in ("none", "sms", "unclassified-email-address"):
            with self.subTest(endpoint=endpoint):
                data = self.fixture()
                if endpoint == "sms":
                    self.add_sms_endpoint(data)
                elif endpoint == "unclassified-email-address":
                    self.add_endpoint(data, EX.generic, COMM.CommunicationEndpoint,
                                      COMM.EmailChannel, "recipient@example.test")
                self.assert_valid(data, False)

    def test_email_endpoint_subclasses_satisfy_the_requirement(self):
        data = self.fixture()
        data.add((EX.WorkEmailEndpoint, RDFS.subClassOf, COMM.EmailEndpoint))
        self.add_endpoint(data, EX.email, EX.WorkEmailEndpoint, COMM.EmailChannel,
                          "recipient@example.test")
        self.assert_valid(data)

    def test_another_recipients_email_endpoint_does_not_satisfy_the_requirement(self):
        data = self.fixture()
        self.add_email_endpoint(data)
        data.remove((EX.recipient, COMM.hasEndpoint, EX.email))
        data.add((EX.otherRecipient, COMM.hasEndpoint, EX.email))
        self.add_sms_endpoint(data)
        self.assert_valid(data, False)

    def test_additional_endpoints_must_still_have_a_channel_and_address(self):
        for missing in (COMM.endpointChannel, COMM.endpointAddress):
            with self.subTest(missing=missing):
                data = self.fixture()
                self.add_email_endpoint(data)
                self.add_sms_endpoint(data)
                data.remove((EX.sms, missing, None))
                self.assert_valid(data, False)

    def test_communication_shapes_pass_standard_shacl_meta_validation(self):
        conforms, _, report = validate(
            Graph(), shacl_graph=self.ontology, meta_shacl=True,
            do_owl_imports=False,
        )
        self.assertTrue(conforms, report)


if __name__ == "__main__":
    unittest.main()
