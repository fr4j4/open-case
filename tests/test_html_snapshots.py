"""The HTML of every document of every case must match the photo in tests/snapshots/.

A change that is not meant to alter the PDFs must leave these files untouched. When a change is
meant to alter them, rewrite the photos and review their diff in the pull request:

    python -m pytest tests/test_html_snapshots.py --update-snapshots      (or: make test-update)
"""
from pathlib import Path

import pytest

from opencase.documents import REPO_ROOT, build_documents
from opencase.loader import case_languages, load_case
from opencase.markup import use_strings
from snapshot import normalize_html

SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"
CASES = sorted(p.parent for p in (REPO_ROOT / "cases").glob("*/case.yaml"))
CASE_LANGS = [(c, lang) for c in CASES for lang in case_languages(c)[1]]


def build(root, lang):
    case = load_case(root, lang)
    use_strings(case.strings)
    return {d.file: normalize_html(d.html, REPO_ROOT) for d in build_documents(case)}


@pytest.fixture(scope="module", params=CASE_LANGS, ids=[f"{c.name}-{lang}" for c, lang in CASE_LANGS])
def built(request):
    root, lang = request.param
    return root, lang, build(root, lang)


def test_matches_snapshot(built, request):
    root, lang, docs = built
    folder = SNAPSHOTS / root.name / lang
    if request.config.getoption("--update-snapshots"):
        if folder.exists():
            for old in folder.glob("*.html"):
                old.unlink()
        folder.mkdir(parents=True, exist_ok=True)
        for file, html in docs.items():
            (folder / f"{file}.html").write_text(html, encoding="utf-8")
        return
    expected = {p.stem: p.read_text(encoding="utf-8") for p in folder.glob("*.html")}
    assert expected, f"no photo in {folder}: run `make test-update`"
    assert sorted(docs) == sorted(expected), "the list of documents changed"
    changed = [f for f in docs if docs[f] != expected[f]]
    assert not changed, (f"the HTML of {', '.join(changed)} changed. If that is intended, run `make test-update` "
                         "and review the diff of tests/snapshots/")


def test_is_deterministic(built):
    root, lang, docs = built
    assert build(root, lang) == docs


def test_has_no_absolute_paths(built):
    root, lang, docs = built
    for file, html in docs.items():
        assert str(REPO_ROOT) not in html, file
        assert "file://" not in html, file
