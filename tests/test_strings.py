"""The words the exporter prints (opencase/strings/<lang>.yaml) must exist in every language,
with the same {placeholders}, so no document comes out half translated."""
import string
from pathlib import Path

import pytest
import yaml

from opencase.i18n import STRINGS_DIR

BASE = "es"
LANGS = sorted(p.stem for p in Path(STRINGS_DIR).glob("*.yaml"))


def flat(node, prefix=""):
    out = {}
    for key, value in node.items():
        if isinstance(value, dict):
            out.update(flat(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


def load(lang):
    return flat(yaml.safe_load((Path(STRINGS_DIR) / f"{lang}.yaml").read_text(encoding="utf-8")))


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(str(text)) if name}


def test_base_and_english_exist():
    assert {BASE, "en"} <= set(LANGS)


@pytest.mark.parametrize("lang", [l for l in LANGS if l != BASE])
def test_same_keys(lang):
    base, other = load(BASE), load(lang)
    assert sorted(set(base) - set(other)) == [], f"missing in {lang}.yaml"
    assert sorted(set(other) - set(base)) == [], f"in {lang}.yaml but not in {BASE}.yaml"


@pytest.mark.parametrize("lang", [l for l in LANGS if l != BASE])
def test_same_placeholders(lang):
    base, other = load(BASE), load(lang)
    wrong = {k: (sorted(placeholders(base[k])), sorted(placeholders(other[k])))
             for k in base if k in other and placeholders(base[k]) != placeholders(other[k])}
    assert wrong == {}


@pytest.mark.parametrize("lang", LANGS)
def test_no_empty_strings(lang):
    assert [k for k, v in load(lang).items() if v is None or str(v).strip() == ""] == []
