"""Publish only GraphArch artifacts, preserving their configured URL path."""
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stage_grapharch_pages", ROOT / "scripts/stage_grapharch_pages.py"
)
STAGING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGING)


class GraphArchPagesTests(unittest.TestCase):
    def test_staging_preserves_destination_and_downloads_without_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            output = root / "output"
            publication = output / "spec/develop"
            publication.mkdir(parents=True)
            (publication / "index.html").write_text("reference")
            (publication / "document.pdf").write_bytes(b"%PDF-test")
            archive = output / "documentation.nq"
            archive.write_text("<urn:subject> <urn:predicate> <urn:object> .")
            (output / "store").mkdir()
            (output / "store/private").write_text("not a publication artifact")
            destination = root / "pages"
            STAGING.stage(output, publication, archive, destination)
            self.assertEqual((destination / "spec/develop/index.html").read_text(), "reference")
            self.assertEqual((destination / "spec/develop/document.pdf").read_bytes(), b"%PDF-test")
            self.assertEqual((destination / "spec/develop/documentation.nq").read_bytes(), archive.read_bytes())
            self.assertIn('url=spec/develop/', (destination / "index.html").read_text())
            self.assertFalse((destination / "store").exists())

    def test_staging_rejects_escaping_artifacts_and_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            output = root / "output"
            publication = output / "spec/develop"
            publication.mkdir(parents=True)
            (publication / "index.html").write_text("reference")
            archive = output / "documentation.nq"
            archive.write_text("graph")
            external = root / "external"
            external.mkdir()
            (external / "index.html").write_text("external")
            with self.assertRaises(ValueError):
                STAGING.stage(output, external, archive, root / "pages")
            existing = root / "existing"
            existing.mkdir()
            (existing / "user-file").write_text("preserve")
            with self.assertRaises(FileExistsError):
                STAGING.stage(output, publication, archive, existing)
            self.assertEqual((existing / "user-file").read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
