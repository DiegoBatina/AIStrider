import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tablet"))

import build_www  # noqa: E402


def test_gera_pagina_do_tablet(tmp_path):
    html = build_www.gerar(tmp_path / "index.html").read_text(encoding="utf-8")
    assert "__" not in html.replace("__proto__", "")
    assert "Conexão com a central" in html and "/admin/licenses" in html
    assert "/licencas/api" not in html
