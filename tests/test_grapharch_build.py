"""Build every publication and package only their public artifact trees."""
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_grapharch_pages", ROOT / "scripts/build_grapharch_pages.py"
)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class GraphArchBuildTests(unittest.TestCase):
    def test_builds_all_targets_and_retains_each_documentation_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory).resolve()
            commands = []

            def generator(command, **kwargs):
                commands.append(command)
                self.assertEqual(kwargs["cwd"], root)
                if "package-site" in command:
                    package = root / "_site/pages/static"
                    package.mkdir(parents=True)
                    (package / "index.html").write_text("EKGF home")
                    return subprocess.CompletedProcess(command, 0, "package")
                target = command[command.index("--target") + 1].rsplit(":", 1)[1]
                folder = {"specification": "site/spec/main", "pdf": "site/pdf",
                          "website": "site"}[target]
                publication = root / "_site" / folder
                publication.mkdir(parents=True, exist_ok=True)
                if target != "pdf":
                    (publication / "index.html").write_text(target)
                archive = root / "_site/documentation.nq"
                archive.write_text(f"graph for {target}")
                if target != "pdf":
                    # GraphArch writes each target's graph at its documentationGraphPath.
                    (publication / "documentation.nq").write_text(f"graph for {target}")
                pdf = (publication / "ekgf-spec-ekg-ontologies.pdf"
                       if target == "pdf" else None)
                if pdf:
                    pdf.write_bytes(b"%PDF-test")
                report = {"schema_version": 1, "publication_path": str(publication),
                          "kg_path": str(archive), "pdf_path": str(pdf) if pdf else None}
                return subprocess.CompletedProcess(command, 0, json.dumps(report))

            with patch.object(BUILD.subprocess, "run", side_effect=generator):
                package = BUILD.build("grapharch-test", "default", root)
            self.assertEqual(package, root / "_site/pages/static")
            self.assertTrue((package / ".nojekyll").is_file())
            self.assertEqual(len(commands), 4)
            for command in commands[:2]:
                self.assertIn("build-family", command)
                self.assertIn("--local-repository", command)
            self.assertIn("build-site", commands[2])
            for command in commands[:3]:
                self.assertEqual(command[command.index("--edition") + 1], "default")
            self.assertFalse((root / "_site/site/pdf/documentation.nq").exists())
            for target, folder in (("specification", "site/spec/main"),
                                   ("website", "site")):
                self.assertEqual((root / "_site" / folder / "documentation.nq").read_text(),
                                 f"graph for {target}")

    def test_failed_renderer_stops_before_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            error = subprocess.CalledProcessError(1, ["grapharch-test"])
            with patch.object(BUILD.subprocess, "run", side_effect=error) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    BUILD.build("grapharch-test", "default", pathlib.Path(directory))
            self.assertEqual(run.call_count, 1)

    def test_rejects_invalid_or_escaping_build_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            output = root / "_site"
            publication = output / "spec/main"
            publication.mkdir(parents=True)
            (publication / "index.html").write_text("family")
            archive = output / "documentation.nq"
            archive.write_text("graph")
            report = {"schema_version": 1, "publication_path": str(publication),
                      "kg_path": str(archive), "pdf_path": None}
            invalid = [dict(report, schema_version=2),
                       dict(report, kg_path=str(root / "outside.nq")),
                       dict(report, publication_path=str(root)),
                       dict(report, pdf_path=str(root / "private.pdf"))]
            for value in invalid:
                with self.subTest(report=value), self.assertRaises((ValueError, FileNotFoundError)):
                    BUILD.retain_graph(value, output, require_pdf=False)
            with self.assertRaises(ValueError):
                BUILD.retain_graph(report, output, require_pdf=True)


if __name__ == "__main__":
    unittest.main()
