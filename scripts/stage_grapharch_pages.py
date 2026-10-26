"""Stage generated artifacts at their publication path for GitHub Pages."""
import argparse
import html
from pathlib import Path
import shutil
from urllib.parse import quote


def stage(output: Path, publication: Path, archive: Path, destination: Path):
    output = output.resolve(strict=True)
    publication = publication.resolve(strict=True)
    archive = archive.resolve(strict=True)
    relative = publication.relative_to(output)
    archive.relative_to(output)
    if relative == Path("."):
        raise ValueError("The publication must have a destination beneath the output root")
    if not (publication / "index.html").is_file() or not archive.is_file():
        raise ValueError("GraphArch did not produce an HTML publication and KG archive")
    if (publication / "documentation.nq").exists():
        raise ValueError("Refusing to overwrite an existing publication artifact")
    if any(path.is_symlink() for path in publication.rglob("*")):
        raise ValueError("Publication artifacts must not contain symbolic links")
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / relative
    shutil.copytree(publication, target)
    shutil.copyfile(archive, target / "documentation.nq")
    url = html.escape(quote(relative.as_posix(), safe="/") + "/", quote=True)
    (destination / "index.html").write_text(
        '<!doctype html>\n<html lang="en"><meta charset="utf-8">\n'
        f'<meta http-equiv="refresh" content="0;url={url}">\n'
        f'<link rel="canonical" href="{url}">\n'
        '<title>EKGF ontology reference</title>\n'
        f'<p><a href="{url}">Open the EKGF ontology reference</a></p></html>\n',
        encoding="utf-8",
    )
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--publication", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    stage(args.output, args.publication, args.archive, args.destination)
