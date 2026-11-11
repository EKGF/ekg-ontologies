"""Build the EKGF website, ontology family browser and PDF with GraphArch."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "urn:ekgf-ontologies:documentation:project"
TARGET = "urn:ekgf-ontologies:documentation:"


def retain_graph(report, output: Path, *, require_pdf: bool):
    """Check the CLI report before retaining this target's graph beside its pages."""
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise ValueError("Unsupported GraphArch publication report schema")
    output = output.resolve(strict=True)

    def artifact(field):
        value = report[field]
        if not isinstance(value, str) or not value or any(c in value for c in "\n\r\x00"):
            raise ValueError(f"Invalid GraphArch artifact: {field}")
        path = Path(value).resolve(strict=True)
        if path == output or not path.is_relative_to(output):
            raise ValueError(f"Artifact must be beneath the output root: {field}")
        return path

    publication = artifact("publication_path")
    archive = artifact("kg_path")
    if not (publication / "index.html").is_file() or not archive.is_file():
        raise ValueError("GraphArch did not produce an HTML publication and KG archive")
    pdf = report.get("pdf_path")
    if require_pdf and pdf is None:
        raise ValueError("The book target did not produce a PDF")
    if pdf is not None and not artifact("pdf_path").is_file():
        raise ValueError("GraphArch did not produce the reported PDF")
    retained = publication / "documentation.nq"
    if retained.exists():
        raise ValueError("Refusing to overwrite an existing publication artifact")
    shutil.copyfile(archive, retained)


def build(binary: str, root: Path = ROOT):
    """Build explicit targets and use GraphArch's static hosting packager."""
    root = root.resolve(strict=True)
    output = root / "_site"
    # A fresh tree keeps partial builds and previous source snapshots out of a publication.
    output.mkdir(exist_ok=False)
    common = ["--definitions", "publication/grapharch.ttl", "--project", PROJECT]
    for target in ("specification", "pdf", "website"):
        source = (["build-site", "--source", "publication/site"] if target == "website"
                  else ["build-family", "--local-repository", "."])
        result = subprocess.run(
            [binary, "publication", *source, *common, "--target", TARGET + target,
             "--output-root", str(output), "--json"],
            cwd=root, stdout=subprocess.PIPE, text=True, check=True,
        )
        retain_graph(json.loads(result.stdout), output, require_pdf=target == "pdf")
    subprocess.run(
        [binary, "publication", "package-site", "--config", "publication/hosting.yaml",
         "--output-root", str(output / "pages"), "--mount", "/"],
        cwd=root, check=True,
    )
    package = output / "pages/.vercel/output/static"
    if not (package / "index.html").is_file():
        raise ValueError("GraphArch did not package the website home page")
    (package / ".nojekyll").touch()
    return package


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grapharch", default="grapharch", help="GraphArch executable")
    arguments = parser.parse_args()
    print(build(arguments.grapharch))
