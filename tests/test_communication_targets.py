"""Memberships and communication attempts must identify a recipient or endpoint."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS


ROOT = Path(__file__).resolve().parents[1]
COMM = Namespace("https://ekgf.org/ontology/communication#")
EX = Namespace("https://example.test/")
CASES = (
    (COMM.Membership, COMM.membershipRecipient, COMM.membershipEndpoint),
    (COMM.CommunicationAttempt, COMM.attemptRecipient, COMM.attemptEndpoint),
)


class CommunicationTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-communication.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self, kind):
        data = Graph()
        data.add((EX.record, RDF.type, kind))
        scope, parent = {
            COMM.Membership: (COMM.membershipCollection, EX.collection),
            COMM.CommunicationAttempt: (COMM.communicationProgram, EX.program),
        }[kind]
        data.add((EX.record, scope, parent))
        data.add((EX.collection, RDF.type, COMM.RecipientCollection))
        data.add((EX.program, RDF.type, COMM.CommunicationProgram))
        data.add((EX.program, COMM.programChannel, COMM.EmailChannel))
        data.add((EX.program, COMM.programPurpose, COMM.TransactionalPurpose))
        for recipient in (EX.recipient, EX.otherRecipient):
            data.add((recipient, RDF.type, COMM.Recipient))
        for endpoint in (EX.endpoint, EX.otherEndpoint):
            data.add((endpoint, RDF.type, COMM.EmailEndpoint))
            data.add((endpoint, COMM.endpointChannel, COMM.EmailChannel))
            data.add((endpoint, COMM.endpointAddress, Literal("recipient@example.test")))
        data.add((EX.recipient, COMM.hasEndpoint, EX.endpoint))
        return data

    def test_missing_target_is_rejected_even_when_targets_exist_elsewhere(self):
        for kind, _, _ in CASES:
            with self.subTest(kind=kind):
                self.assert_valid(self.fixture(kind), False)

    def test_recipient_endpoint_and_both_are_accepted(self):
        for kind, recipient, endpoint in CASES:
            for selection in ("recipient", "endpoint", "both"):
                with self.subTest(kind=kind, selection=selection):
                    data = self.fixture(kind)
                    if selection in ("recipient", "both"):
                        data.add((EX.record, recipient, EX.recipient))
                    if selection in ("endpoint", "both"):
                        data.add((EX.record, endpoint, EX.endpoint))
                    self.assert_valid(data)

    def test_subclasses_cannot_omit_their_target(self):
        for kind, _, _ in CASES:
            with self.subTest(kind=kind):
                data = self.fixture(kind)
                data.remove((EX.record, RDF.type, kind))
                data.add((EX.SpecificRecord, RDFS.subClassOf, kind))
                data.add((EX.record, RDF.type, EX.SpecificRecord))
                self.assert_valid(data, False)

    def test_multiple_recipients_or_endpoints_are_rejected(self):
        for kind, recipient, endpoint in CASES:
            for predicate, values in (
                (recipient, (EX.recipient, EX.otherRecipient)),
                (endpoint, (EX.endpoint, EX.otherEndpoint)),
            ):
                with self.subTest(kind=kind, predicate=predicate):
                    data = self.fixture(kind)
                    for value in values:
                        data.add((EX.record, predicate, value))
                    self.assert_valid(data, False)

    def test_literal_targets_are_rejected(self):
        for kind, recipient, endpoint in CASES:
            for predicate in (recipient, endpoint):
                with self.subTest(kind=kind, predicate=predicate):
                    data = self.fixture(kind)
                    data.add((EX.record, predicate, Literal("target")))
                    self.assert_valid(data, False)


if __name__ == "__main__":
    unittest.main()
