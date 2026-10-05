from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from ai_strider.main import app
from ai_strider.modulos import licencas

client = TestClient(app)


@pytest.fixture
def central_falsa(monkeypatch):
    chamadas = []
    passado = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    futuro = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    rows = [
        {"license_key": "RUNE-A", "product_code": "RUNE", "customer": "X", "plan": "Mensal", "status": "active", "expires_at": futuro},
        {"license_key": "RUNE-B", "product_code": "RUNE", "customer": "Y", "plan": "Mensal", "status": "active", "expires_at": passado},
        {"license_key": "SHOW-A", "product_code": "SHOW", "customer": "Z", "plan": "Anual", "status": "frozen", "expires_at": None},
    ]

    def fake(method, path, data=None):
        chamadas.append((method, path, data))
        if path == "/admin/licenses" and method == "GET":
            return [dict(r) for r in rows]
        return {"ok": True}

    monkeypatch.setattr(licencas, "central", fake)
    return chamadas


def test_aba_aparece_na_navegacao():
    r = client.get("/")
    assert r.status_code == 200
    assert 'href="/licencas"' in r.text and "Painel mestre de licenças" in r.text


def test_tela_de_licencas():
    r = client.get("/licencas")
    assert r.status_code == 200
    assert "Liga Brasileira Premodern" in r.text and 'class="ativa"' in r.text


def test_listagem_com_nome_do_produto(central_falsa):
    rows = client.get("/licencas/api/licenses").json()
    assert rows[0]["product_name"] == "Rune Pro"


def test_resumo_vem_da_central(central_falsa):
    s = {x["product_code"]: x for x in client.get("/licencas/api/summary").json()}
    assert (s["RUNE"]["active"], s["RUNE"]["expired"]) == (1, 1)
    assert s["SHOW"]["frozen"] == 1


def test_acoes_repassadas(central_falsa):
    client.post("/licencas/api/licenses/RUNE-A/freeze")
    client.post("/licencas/api/licenses/RUNE-A/extend?days=0")
    client.post("/licencas/api/licenses/RUNE-A/reset-device")
    assert ("POST", "/admin/licenses/RUNE-A/status", {"status": "frozen"}) in central_falsa
    assert ("POST", "/admin/licenses/RUNE-A/extend", {"days": 1}) in central_falsa
    assert ("POST", "/admin/licenses/RUNE-A/reset-device", None) in central_falsa
    assert client.post("/licencas/api/licenses/RUNE-A/apagar").status_code == 404


def test_sem_token(monkeypatch):
    monkeypatch.setattr(licencas, "central_token", lambda: "")
    r = client.get("/licencas/api/licenses")
    assert r.status_code == 500 and "Token" in r.json()["detail"]
