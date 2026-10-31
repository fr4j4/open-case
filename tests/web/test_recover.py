"""F6a · site/play/js/recover.js: the backup file, the recovery codes and the game rebuilt from what the phones hold, against the
scripted game of the v8 simulation (tests/web/partidas/). Run with `node --test` (tests/web/recover.test.mjs); without node these
tests are skipped. The pages (a director that loses its device, over the real relay transport) are in test_recover_ui.py."""
import shutil
import subprocess
from pathlib import Path

import pytest

from opencase import web

REPO = Path(__file__).resolve().parent.parent.parent
CASES = REPO / "cases"
CASE = "chupacabras-labranza"
GAME = REPO / "tests" / "web" / "partidas" / "v8_tres_equipos.json"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def test_recover_js_with_the_scripted_game(tmp_path):
    entries = web.build_cases([CASES / CASE], tmp_path)
    folder = tmp_path / "play" / next(e for e in entries if e["language"] == "es")["path"]
    env = {"OC_WEB_DIR": str(folder), "OC_PARTIDA": str(GAME), "PATH": str(Path(NODE).parent)}
    done = subprocess.run([NODE, "--test", str(REPO / "tests" / "web" / "recover.test.mjs")], cwd=REPO, env=env,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stdout[-8000:] + done.stderr[-2000:]
