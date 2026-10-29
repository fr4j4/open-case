"""The words the exporter itself prints on the documents ("Sheet 1 of 2", "Team", "Attached"...).

They live in opencase/strings/<language>.yaml. A language falls back to English for any
key it does not define, and a case can override any of them with `strings:` in
languages/<lang>/case.yaml."""
from pathlib import Path

import yaml

STRINGS_DIR = Path(__file__).resolve().parent / "strings"


def _merge(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Strings:
    def __init__(self, data):
        self.data = data

    @classmethod
    def load(cls, lang, overrides=None):
        english = yaml.safe_load((STRINGS_DIR / "en.yaml").read_text(encoding="utf-8"))
        data = english
        own = STRINGS_DIR / f"{lang}.yaml"
        if own.exists():
            data = _merge(data, yaml.safe_load(own.read_text(encoding="utf-8")))
        return cls(_merge(data, overrides))

    def __call__(self, key, **kw):
        node = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                raise KeyError(f"missing UI string '{key}'")
            node = node[part]
        return node.format(**kw) if kw else node
