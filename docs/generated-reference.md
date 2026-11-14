# Generate the EKGF ontology family website

[Documentation index](../README.md#documentation)

[GraphArch](https://github.com/EKGF/grapharch/releases) builds
the EKGF website, a multipage ontology family reference and a PDF directly from
this checkout. The publication settings are in
[`publication/grapharch.ttl`](../publication/grapharch.ttl). They refer to the
existing EKGF family and authority UUIDs; they do not redefine those identities
or change ontology axioms. The generated reference is an editor's draft, not an
approved standards release.

This repository publishes from `main`. The website contains two further
publications, declared through `ga:containsTarget`: the family reference at
`spec/main/` and the PDF edition at `pdf/`. The paginated family reference does
not produce a combined PDF, so the PDF edition is a separate target. Its
`ga:TypstRenderer` renders the whole family as one document,
`pdf/ekgf-spec-ekg-ontologies.pdf`.

The [website](https://ekgf.github.io/ekg-ontologies/) uses the shared EKGF header,
footer, typography and theme controls, as other EKGF websites do. Its authored
introduction and usage page live in [`publication/site/`](../publication/site/).
The site's primary navigation places **Ontology family** and **PDF** in the
second bar beside the site name. The top bar carries shared EKGF navigation.
These links are relative to the website root, so the deployment location
comes from the hosting profile rather than the definitions. Links between
publications, such as the reference's download links, name the target IRI and
GraphArch resolves its published location.

The [family reference](https://ekgf.github.io/ekg-ontologies/spec/main/)
uses the same `ga:SpecificationPagesRenderer` as GraphArch's Commons showcase:
a family overview, one reference page per ontology, links between terms, and
shared search. The registered family explicitly selects `ga:collectionTerm
"family"`. It retains its own name, EKGF publishing authority and namespaces.
The [PDF edition](https://ekgf.github.io/ekg-ontologies/pdf/ekgf-spec-ekg-ontologies.pdf)
contains the complete reference as a book. The reference's
[documentation graph](https://ekgf.github.io/ekg-ontologies/spec/main/documentation.nq)
is available as a restorable RDF archive.

## Build locally

Install the GraphArch release pinned in the workflow, then run from this repository's root:

```sh
python3 -B scripts/build_grapharch_pages.py
```

Use `--grapharch /path/to/grapharch` if the executable is not on `PATH`.
The command requires a fresh `_site/` directory and fails if one already exists.
Move or remove your previous generated `_site/` tree before rebuilding.

The script explicitly selects three targets from `publication/grapharch.ttl`:

| Target | Renderer | Generated destination |
| --- | --- | --- |
| `doc:website` | `ga:WebsiteRenderer`, EKGF theme and documentation layout | `_site/site/` |
| `doc:specification` | `ga:SpecificationPagesRenderer` | `_site/site/spec/main/` |
| `doc:pdf` | `ga:TypstRenderer` | `_site/site/pdf/` |

Here `doc:` is `urn:ekgf-ontologies:documentation:`. The website has its own
scope and profile. The reference and the PDF edition use their own profiles,
which both publish the registered family.
The configuration records this arrangement in `annotation:markdownDescription`.

Each family target uses `publication build-family --local-repository .` with
explicit `--definitions`, `--project` and `--target` arguments. The source
checkout is read directly. Ontologies are not copied into another
repository, and imports are not downloaded. Git provenance records the observed
checkout state, including local edits. The website uses `publication build-site`
with its own explicit target; its authored pages come from the project's
`ga:contentSource "publication/site"`.

The script checks each versioned JSON build report. GraphArch writes each
target's documentation graph at its `ga:documentationGraphPath`, and the script
verifies that it matches the reported archive. It then uses GraphArch's
`publication package-site` with
[`publication/hosting.yaml`](../publication/hosting.yaml), a GitHub Pages
profile, to package the composed website. Packaging rejects collisions, private files and symlinks.
Graph stores and intermediate build directories are excluded.

The deployable static tree is `_site/pages/static/`. Its root is
the EKGF website; the family reference is at `spec/main/`, and the PDF edition
is at `pdf/`. The website and the family reference each have their own
restorable `documentation.nq`; `pdf/` holds only the PDF, named
`pdf/ekgf-spec-ekg-ontologies.pdf` on `main` and
`pdf/ekgf-spec-ekg-ontologies-pr-<number>.pdf` in pull-request previews.
Serve the assembled tree to preview the complete site:

```sh
python3 -m http.server 8770 --directory _site/pages/static
```

`_site/` is ignored by Git
and excluded from source discovery, so generated RDF cannot become an input to
the next run. Do not commit generated output.

## Build in GitHub Actions

The **Publish ontology reference** workflow runs when ontology, registry,
documentation or publication sources change. Pull requests build and check the
reference; successful builds on `main` deploy it to GitHub Pages. You can also
run the workflow manually. The site root serves the EKGF website, and the
family reference retains its canonical `spec/main/` URL.

The workflow pins the GraphArch action to the full commit SHA of a release,
with the release version as a comment. The action installs the binary of that
same release and verifies its checksum and source commit against the pinned
action commit. [Dependabot](../.github/dependabot.yml) checks GitHub Actions
daily and opens a pull request when a newer GraphArch release exists. That pull
request builds the reference with the new release before it is merged.
It builds directly from `actions/checkout`, running the same build script as
the local command. A failed renderer or invalid report stops packaging and deployment.
It downloads and verifies the release binary; no Rust installation or compilation
is required. Generated HTML, PDF and the restorable KG archive are included in
the Pages artifact. The workflow uploads only the assembled static tree.

Update the publication date and version URLs in the Turtle configuration when
preparing a new publication. Authority labels, family members, descriptions and
ontology terms continue to come from their existing source files and registry.
